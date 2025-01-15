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
    TASK_LOGGER.info(f"Starting schmidtrank task with db id '{db_id}'")
    task_data = ProcessingTask.get_by_id(id_=db_id)
    if not task_data:
        msg = f"Could not load task data with id {db_id}!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    parameters = loads(task_data.parameters or "{}")
    state = parameters.get("vector", [])
    dim_A = parameters.get("dimA", 0)
    dim_B = parameters.get("dimB", 0)
    tolerance = parameters.get("tolerance", 1e-10)

    TASK_LOGGER.info(
        f"Parameters: state={state}, dim_A={dim_A}, dim_B={dim_B}, tolerance={tolerance}"
    )

    try:
        # Convert state to numpy array
        try:
            state_array = np.array([complex(real, imag) for real, imag in state])
        except ValueError as e:
            msg = f"Failed to cast 'state' elements to complex numbers: {e}"
            TASK_LOGGER.error(msg)
            raise ValueError(msg)

        # Validate dimensions
        if len(state_array) != dim_A * dim_B:
            msg = f"Dimension mismatch: len(state)={len(state_array)} does not match dim_A * dim_B = {dim_A * dim_B}."
            TASK_LOGGER.error(msg)
            raise ValueError(msg)

        # Call the compute_schmidt_rank function
        result = compute_schmidt_rank(
            state=state_array, dim_A=dim_A, dim_B=dim_B, tolerance=tolerance
        )

        # Save the result as a file
        with SpooledTemporaryFile(mode="w") as output:
            output.write(f"{result}")
            output.seek(0)  # Reset file pointer
            STORE.persist_task_result(
                db_id,
                output,
                "out.txt",  # Filename
                "custom/schmidtrank-output",  # Data type
                "text/plain",  # Content-Type
            )

        return f"{result}"

    except Exception as e:
        TASK_LOGGER.error(f"Error in schmidtrank task: {e}")
        raise
