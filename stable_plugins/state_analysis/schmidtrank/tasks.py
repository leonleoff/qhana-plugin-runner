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
    dim_A = parameters.get("dim_A")
    dim_B = parameters.get("dim_B")
    tolerance = parameters.get("tolerance")

    TASK_LOGGER.info(
        f"Input parameters before transformation: vector={vector}, dim_A={dim_A}, dim_B={dim_B}, tolerance={tolerance}"
    )

    # Transform input vectors into NumPy arrays of complex numbers
    np_vector = []
    try:

        complex_numbers = []
        for pair in vector:
            complex_number = complex(pair[0], pair[1])
            complex_numbers.append(complex_number)
        np_vector = np.array(complex_numbers)

        TASK_LOGGER.info(f"Transformed vector: {np_vector}")

    except Exception as e:
        TASK_LOGGER.error(f"Error while transforming input vectors: {e}")
        raise

    try:
        # Log and call the function to analyze linear dependence in HX
        TASK_LOGGER.info(
            "Invoking 'schmidtrank' with parameters: "
            f"vector={np_vector}, dim_A={dim_A}, dim_B={dim_B}, tolerance={tolerance}"
        )

        result = compute_schmidt_rank(
            state=np_vector, dim_A=dim_A, dim_B=dim_B, tolerance=tolerance
        )

        TASK_LOGGER.info(f"Result of schmidtrank analysis: {result}")

        # Save the result as a file
        with SpooledTemporaryFile(mode="w") as output_file:
            output_file.write(f"{result}")
            output_file.seek(0)  # Reset the file pointer for reading
            STORE.persist_task_result(
                db_id,
                output_file,
                "out.txt",  # File name
                "custom/schmidtrank-output",  # Data type
                "text/plain",  # MIME type
            )
        TASK_LOGGER.info(f"Result successfully saved for task ID {db_id}.")

        return f"{result}"

    except Exception as e:
        TASK_LOGGER.error(f"Error during 'schmidtrank' task execution: {e}")
        raise
