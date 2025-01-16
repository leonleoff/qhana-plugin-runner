from json import loads
from tempfile import SpooledTemporaryFile
from typing import Optional

import numpy as np
from celery.utils.log import get_task_logger
from common.algorithms import are_vectors_linearly_dependent
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.storage import STORE

from . import ClassicalStateAnalysisLineardependence

TASK_LOGGER = get_task_logger(__name__)


@CELERY.task(
    name=f"{ClassicalStateAnalysisLineardependence.instance.identifier}.lineardependence_task",
    bind=True,
)
def lineardependence_task(self, db_id: int) -> str:

    TASK_LOGGER.info(f"Starting 'lineardependence' task with database ID '{db_id}'.")

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
    tolerance = parameters.get("tolerance")
    TASK_LOGGER.info(
        f"Input parameters before transformation: vectors={vectors}, tolerance={tolerance}"
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
        # Log and call the function to check linear dependence
        TASK_LOGGER.info(
            "Invoking 'are_vectors_linearly_dependent' with parameters: "
            f"vectors={new_set_of_vectors}, tolerance={tolerance}"
        )

        result = are_vectors_linearly_dependent(
            vectors=new_set_of_vectors, tolerance=tolerance
        )

        TASK_LOGGER.info(f"Result of linear dependence analysis: {result}")

        # Save the result as a file
        with SpooledTemporaryFile(mode="w") as output_file:
            output_file.write(f"{result}")
            output_file.seek(0)  # Reset the file pointer for reading
            STORE.persist_task_result(
                db_id,
                output_file,
                "out.txt",  # File name
                "custom/lineardependence-output",  # Data type
                "text/plain",  # MIME type
            )
        TASK_LOGGER.info(f"Result successfully saved for task ID {db_id}.")

        return f"{result}"

    except Exception as e:
        TASK_LOGGER.error(f"Error during 'lineardependence' task execution: {e}")
        raise
