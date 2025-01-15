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
    TASK_LOGGER.info(f"Starting lineardependence task with db id '{db_id}'")
    task_data = ProcessingTask.get_by_id(id_=db_id)
    if not task_data:
        msg = f"Could not load task data with id {db_id}!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    parameters = loads(task_data.parameters or "{}")
    vectors = parameters.get("vectors", [])
    tolerance = parameters.get("tolerance", 1e-10)

    TASK_LOGGER.info(f"Parameters: vectors={vectors}, tolerance={tolerance}")

    try:
        # Convert vectors to numpy arrays
        numpy_vectors = [np.array(vector, dtype=complex) for vector in vectors]

        # Call the function to check linear dependence
        result = are_vectors_linearly_dependent(
            vectors=numpy_vectors, tolerance=tolerance
        )

        # Save the result as a file
        with SpooledTemporaryFile(mode="w") as output:
            output.write(f"{result}")
            output.seek(0)  # Reset file pointer
            STORE.persist_task_result(
                db_id,
                output,
                "out.txt",  # Filename
                "custom/lineardependence-output",  # Data type
                "text/plain",  # Content-Type
            )

        return f"{result}"

    except Exception as e:
        TASK_LOGGER.error(f"Error in lineardependence task: {e}")
        raise
