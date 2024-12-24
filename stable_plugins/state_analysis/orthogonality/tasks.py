from tempfile import SpooledTemporaryFile

from typing import Optional
from json import loads

from celery.utils.log import get_task_logger

#import numpy as np

from . import ClassicalStateAnalysisOrthogonality
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask

from qhana_plugin_runner.storage import STORE

TASK_LOGGER = get_task_logger(__name__)

@CELERY.task(name=f"{ClassicalStateAnalysisOrthogonality.instance.identifier}.orthogonality_task", bind=True)
def orthogonality_task(self, db_id: int) -> str:
    TASK_LOGGER.info(f"Starting orthogonality task with db id '{db_id}'")
    task_data: Optional[ProcessingTask] = ProcessingTask.get_by_id(id_=db_id)

    if task_data is None:
        msg = f"Could not load task data with id {db_id} to read parameters!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    parameters = loads(task_data.parameters or "{}")
#    vector1 = parameters.get("vector1", [])
#    vector2 = parameters.get("vector2", [])
#    tolerance = parameters.get("tolerance", 1e-10)
#
#    TASK_LOGGER.info(f"Loaded input parameters: vector1={vector1}, vector2={vector2}, tolerance={tolerance}")

    TASK_LOGGER.info(f"Parameters are: {parameters}")

    return "output"

#    if not vector1 or not vector2:
#        raise ValueError("Vectors must be provided and cannot be empty.")
#
#    try:
#        vec1 = np.array(vector1, dtype=float)
#        vec2 = np.array(vector2, dtype=float)
#        result = are_vectors_orthogonal(vec1, vec2, tolerance)
#        output_message = "Vectors are orthogonal." if result else "Vectors are not orthogonal."
#
#        with SpooledTemporaryFile(mode="w") as output:
#            output.write(output_message)
#            STORE.persist_task_result(
#                db_id, output, "orthogonality_result.txt", "text/plain", "custom/orthogonality-output"
#            )
#
#        return output_message
#
#    except Exception as e:
#        TASK_LOGGER.error(f"Error in orthogonality task: {e}")
#        raise