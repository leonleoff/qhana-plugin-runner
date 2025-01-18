import json
from json import loads
from tempfile import SpooledTemporaryFile
from typing import Optional

import numpy as np
from celery.utils.log import get_task_logger
from common.algorithms import analyze_lineardependenceinhx
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.storage import STORE

from . import ClassicalStateAnalysisLineardependenceInHX

TASK_LOGGER = get_task_logger(__name__)


@CELERY.task(
    name=f"{ClassicalStateAnalysisLineardependenceInHX.instance.identifier}.lineardependenceinhx_task",
    bind=True,
)
def lineardependenceInHX_task(self, db_id: int) -> str:

    TASK_LOGGER.info(f"Starting 'lineardependenceInHX' task with database ID '{db_id}'.")

    # Load task data
    task_data = ProcessingTask.get_by_id(id_=db_id)
    if not task_data:
        msg = f"Task data with ID {db_id} could not be loaded!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    # Extract parameters and log them
    parameters = loads(task_data.parameters or "{}")
    TASK_LOGGER.info(f"Extracted parameters: {parameters}")

    vectors = parameters.get("vectors", [])
    dim_A = parameters.get("dimA")
    dim_B = parameters.get("dimB")
    singular_value_tolerance = parameters.get("singular_value_tolerance")
    linear_independence_tolerance = parameters.get("linear_independence_tolerance")

    TASK_LOGGER.info(
        f"Input parameters before transformation: vectors={vectors}, dim_A={dim_A}, dim_B={dim_B}, singular_value_tolerance={singular_value_tolerance}, linear_independence_tolerance={linear_independence_tolerance}"
    )

    # Transform input vectors into NumPy arrays of complex numbers
    new_set_of_vectors = []
    try:
        for vector in vectors:
            complex_numbers = []
            for pair in vector:
                complex_number = complex(pair[0], pair[1])
                complex_numbers.append(complex_number)
            np_vector = np.array(complex_numbers)
            new_set_of_vectors.append(np_vector)

        TASK_LOGGER.info(f"Transformed vectors: {new_set_of_vectors}")

    except Exception as e:
        TASK_LOGGER.error(f"Error while transforming input vectors: {e}")
        raise

    try:
        # Log and call the function to analyze linear dependence in HX
        TASK_LOGGER.info(
            "Invoking 'analyze_lineardependenceinhx' with parameters: "
            f"vectors={new_set_of_vectors}, dim_A={dim_A}, dim_B={dim_B}, singular_value_tolerance={singular_value_tolerance}, linear_independence_tolerance={linear_independence_tolerance}"
        )

        result = analyze_lineardependenceinhx(
            states=new_set_of_vectors,
            dim_A=dim_A,
            dim_B=dim_B,
            singular_value_tolerance=singular_value_tolerance,
            linear_independence_tolerance=linear_independence_tolerance,
        )

        TASK_LOGGER.info(f"Result of linear dependence in HX analysis: {result}")

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
                "custom/lineardependenceinhx-output",  # Data type
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
                "custom/lineardependenceinhx-output",  # Data type
                "application/json",  # MIME type
            )

        TASK_LOGGER.info(f"Results successfully saved for task ID {db_id}.")

        # Return JSON data
        return json.dumps(output_data)  # Rückgabe des JSON-Strings

    except Exception as e:
        TASK_LOGGER.error(f"Error during 'lineardependenceInHX' task execution: {e}")
        raise
