from tempfile import SpooledTemporaryFile

from typing import Optional
from json import loads

from celery.utils.log import get_task_logger

import numpy as np
from .algorithm import compute_schmidt_rank
from . import ClassicalStateAnalysisSchmidtrank
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask

from qhana_plugin_runner.storage import STORE

TASK_LOGGER = get_task_logger(__name__)

@CELERY.task(name=f"{ClassicalStateAnalysisSchmidtrank.instance.identifier}.schmidtrank_task", bind=True)
def schmidtrank_task(self, db_id: int) -> str:
    TASK_LOGGER.info(f"Starting schmidtrank task with db id '{db_id}'")
    task_data = ProcessingTask.get_by_id(id_=db_id)
    
    parameters = loads(task_data.parameters or "{}")
    state = parameters.get("state", [])
    dim_A = parameters.get("dim_A", 0)
    dim_B = parameters.get("dim_B", 0)
    tolerance = parameters.get("tolerance", 1e-10)

    TASK_LOGGER.info(f"Parameters: state={state}, dim_A={dim_A}, dim_B={dim_B}, tolerance={tolerance}")
    
    try:
        # Convert state to numpy array
        state_array = []


        try:
            # Initialize an empty list to hold the complex numbers
            complex_list = []

            # Iterate over each element in the state
            for val in state:
                try:
                    # Try to parse the value as a complex number
                    complexN = complex(val)
                    complex_list.append(complexN)
                except ValueError:
                    raise ValueError(f"Invalid element in 'state': {val}") from e
            # Convert the list to a numpy array
            state_array = np.array(complex_list, dtype=complex)

        except ValueError as e:
            TASK_LOGGER.error(f"Failed to cast 'state' elements to complex numbers: {e}")
            raise ValueError(f"Invalid element in 'state': {e}")
        
        # Validate dimensions
        if len(state_array) != dim_A * dim_B:
            error_msg = (
                f"Dimension mismatch: len(state)={len(state_array)} does not match dim_A * dim_B = {dim_A * dim_B}."
            )
            TASK_LOGGER.error(error_msg)
            raise ValueError(error_msg)

        # Call the compute_schmidt_rank function
        result = compute_schmidt_rank(state=state_array, dim_A=dim_A, dim_B=dim_B, tolerance=tolerance)

        output_message = f"The Schmidt rank is {result}."

        # Save the result to a file
        with SpooledTemporaryFile(mode="w") as output:
            output.write(output_message)
            output.seek(0)  # Reset file pointer
            STORE.persist_task_result(
                db_id,
                output,
                "out.txt",  # Filename
                "custom/schmidtrank-output",  # Data type
                "text/plain",  # Content-Type
            )

        return output_message

    except Exception as e:
        TASK_LOGGER.error(f"Error in schmidtrank task: {e}")
        raise