from tempfile import SpooledTemporaryFile

from typing import Optional
from json import loads

from celery.utils.log import get_task_logger

import numpy as np

from . import HelloWorld
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask

from qhana_plugin_runner.storage import STORE

TASK_LOGGER = get_task_logger(__name__)

@CELERY.task(name="classical_state_analysis.orthogonality_task", bind=True)
def orthogonality_task(self, db_id: int) -> str:
    TASK_LOGGER.info(f"Starting orthogonality task with db id '{db_id}'")
    task_data: Optional[ProcessingTask] = ProcessingTask.get_by_id(id_=db_id)

    if task_data is None:
        msg = f"Could not load task data with id {db_id} to read parameters!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    parameters = loads(task_data.parameters or "{}")
    vector1 = parameters.get("vector1", [])
    vector2 = parameters.get("vector2", [])
    tolerance = parameters.get("tolerance", 1e-10)

    TASK_LOGGER.info(f"Loaded input parameters: vector1={vector1}, vector2={vector2}, tolerance={tolerance}")

    if not vector1 or not vector2:
        raise ValueError("Vectors must be provided and cannot be empty.")

    try:
        vec1 = np.array(vector1, dtype=float)
        vec2 = np.array(vector2, dtype=float)
        result = are_vectors_orthogonal(vec1, vec2, tolerance)
        output_message = "Vectors are orthogonal." if result else "Vectors are not orthogonal."

        with SpooledTemporaryFile(mode="w") as output:
            output.write(output_message)
            STORE.persist_task_result(
                db_id, output, "orthogonality_result.txt", "text/plain", "custom/orthogonality-output"
            )

        return output_message

    except Exception as e:
        TASK_LOGGER.error(f"Error in orthogonality task: {e}")
        raise

def are_vectors_orthogonal(vec1: np.ndarray, vec2: np.ndarray, tolerance: float = 1e-10) -> bool:
    """
    Checks whether two NumPy vectors are orthogonal by calculating their dot product using a for loop.

    Args:
        vec1 (np.ndarray): The first vector.
        vec2 (np.ndarray): The second vector.
        tolerance (float): The tolerance value for checking orthogonality (default is 1e-10).

    Returns:
        bool: True if the vectors are orthogonal, False otherwise.
    """
    # Ensure the vectors have the same length
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have the same dimension.")
    
    # Initialize the dot product
    dot_product = 0.0

    # Calculate the dot product using a for loop
    for i in range(len(vec1)):
        dot_product += vec1[i] * vec2[i]

    # Check if the dot product is close to zero within the specified tolerance
    return abs(dot_product) < tolerance