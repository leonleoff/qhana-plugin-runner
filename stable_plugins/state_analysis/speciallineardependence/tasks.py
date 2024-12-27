from tempfile import SpooledTemporaryFile

from typing import Optional
from json import loads

from celery.utils.log import get_task_logger

import numpy as np

from .algorithm import are_vectors_special_linearly_dependent
from . import ClassicalStateAnalysisSpeciallineardependence
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask

from qhana_plugin_runner.storage import STORE

TASK_LOGGER = get_task_logger(__name__)

@CELERY.task(name=f"{ClassicalStateAnalysisSpeciallineardependence.instance.identifier}.schmidtrank_task", bind=True)
def speciallineardependence_task(self, db_id: int) -> str:
    TASK_LOGGER.info(f"Starting speciallineardependence task with db id '{db_id}'")
    task_data = ProcessingTask.get_by_id(id_=db_id)
    if not task_data:
        msg = f"Could not load task data with id {db_id}!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    parameters = loads(task_data.parameters or "{}")
    state = parameters.get("state", [])
    dim_A = parameters.get("dim_A", 0)
    dim_B = parameters.get("dim_B", 0)
    tolerance = parameters.get("tolerance", 1e-10)

    TASK_LOGGER.info(f"Parameters: state={state}, dim_A={dim_A}, dim_B={dim_B}, tolerance={tolerance}")

    try:
        # Convert state to numpy array
        state_array = np.array(state, dtype=complex)

        # Call the are_vectors_special_linearly_dependent function
        result = are_vectors_special_linearly_dependent(state=state_array, dim_A=dim_A, dim_B=dim_B, tolerance=tolerance)

        output_message = f"The vectors are {'linearly dependent' if result else 'not linearly dependent'}."

        # Save the result to a file
        with SpooledTemporaryFile(mode="w") as output:
            output.write(output_message)
            output.seek(0)  # Reset file pointer
            STORE.persist_task_result(
                db_id,
                output,
                "out.txt",  # Filename
                "custom/special-dependency-output",  # Data type
                "text/plain",  # Content-Type
            )

        return output_message

    except Exception as e:
        TASK_LOGGER.error(f"Error in schmidtrank task: {e}")
        raise