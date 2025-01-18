import json
from json import loads
from tempfile import SpooledTemporaryFile
from typing import Optional

import numpy as np
from celery.utils.log import get_task_logger
from common.algorithms import compute_schmidt_rank
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.storage import STORE

from . import ClassicalStateAnalysisSchmidtrank

TASK_LOGGER = get_task_logger(__name__)


@CELERY.task(
    name=f"{ClassicalStateAnalysisSchmidtrank.instance.identifier}.schmidtrank_task",
    bind=True,
)
def schmidtrank_task(self, db_id: int) -> str:

    TASK_LOGGER.info(f"Starting 'schmidtrank' task with database ID '{db_id}'.")

    # Load task data
    task_data = ProcessingTask.get_by_id(id_=db_id)
    if not task_data:
        msg = f"Task data with ID {db_id} could not be loaded!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    # Extract parameters and log them
    parameters = loads(task_data.parameters or "{}")
    TASK_LOGGER.info(f"Extracted parameters: {parameters}")

    vector = parameters.get("vector", [])
    dim_A = parameters.get("dimA")
    dim_B = parameters.get("dimB")
    tolerance = parameters.get("tolerance")

    TASK_LOGGER.info(
        f"Input parameters before transformation: vector={vector}, dim_A={dim_A}, dim_B={dim_B}, tolerance={tolerance}"
    )

    # Transform the input vector into a NumPy array of complex numbers
    np_vector = []
    try:
        complex_numbers = []
        for pair in vector:
            complex_number = complex(pair[0], pair[1])
            complex_numbers.append(complex_number)
        np_vector = np.array(complex_numbers)

        TASK_LOGGER.info(f"Transformed vector: {np_vector}")

    except Exception as e:
        TASK_LOGGER.error(f"Error while transforming input vector: {e}")
        raise

    try:
        # Log and call the function to compute Schmidt rank
        TASK_LOGGER.info(
            "Invoking 'compute_schmidt_rank' with parameters: "
            f"vector={np_vector}, dim_A={dim_A}, dim_B={dim_B}, tolerance={tolerance}"
        )

        result = compute_schmidt_rank(
            state=np_vector, dim_A=dim_A, dim_B=dim_B, tolerance=tolerance
        )

        TASK_LOGGER.info(f"Result of Schmidt rank analysis: {result}")

        # JSON Output
        output_data = {
            "result": bool(result),  # Explizit in JSON-kompatiblen Typ umwandeln
        }

        # Save the result as a TXT file
        with SpooledTemporaryFile(mode="w") as txt_file:
            txt_file.write(str(output_data))  # output_data als String speichern
            txt_file.seek(0)  # Reset the file pointer for reading
            STORE.persist_task_result(
                db_id,
                txt_file,
                "out.txt",  # File name
                "custom/schmidtrank-output",  # Data type
                "text/plain",  # MIME type
            )

        # Save the result as a JSON file
        with SpooledTemporaryFile(mode="w") as json_file:
            json.dump(output_data, json_file)  # Schreibe das JSON in die Datei
            json_file.seek(0)  # Reset the file pointer for reading
            STORE.persist_task_result(
                db_id,
                json_file,
                "out.json",  # File name
                "custom/schmidtrank-output",  # Data type
                "application/json",  # MIME type
            )

        TASK_LOGGER.info(f"Results successfully saved for task ID {db_id}.")

        # Return JSON data
        return json.dumps(output_data)  # Rückgabe des JSON-Strings

    except Exception as e:
        TASK_LOGGER.error(f"Error during 'schmidtrank' task execution: {e}")
        raise
