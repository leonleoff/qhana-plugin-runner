import json
import struct
from json import loads
from tempfile import SpooledTemporaryFile
from typing import Optional

from celery.utils.log import get_task_logger
from common.encoding_registry import EncodingRegistry
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.storage import STORE

from . import VectorEncodingPlugin

TASK_LOGGER = get_task_logger(__name__)


@CELERY.task(
    name=f"{VectorEncodingPlugin.instance.identifier}.vector_encoding_task", bind=True
)
def vector_encoding_task(self, db_id: int) -> str:
    """
    Main Celery task that encodes the given vectors into QASM code
    and stores the results in the QHAna storage.
    """
    TASK_LOGGER.info(f"Starting vector-encoding task with db_id={db_id}")
    task_data: Optional[ProcessingTask] = ProcessingTask.get_by_id(db_id)
    if not task_data:
        msg = f"Task data with ID {db_id} not found!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    # Load task parameters
    parameters = loads(task_data.parameters or "{}")
    vectors = parameters.get("vectors", [])  # Array of arrays of [re, im] pairs
    strategy_id = parameters.get("strategy_id")

    # Convert vectors into Python complex numbers
    python_vectors = [[complex(re, im) for re, im in vector] for vector in vectors]

    TASK_LOGGER.info(f"Encoding {len(python_vectors)} vectors...")

    # Get the encoding strategy
    strategy = EncodingRegistry.get_strategy(strategy_id)

    # Perform encoding
    qasm_code, circuit_borders = strategy.encode(python_vectors, None)

    # Create the QuantumCircuitDescriptor structure
    qcd_output = {
        "circuit": qasm_code,
        "metadata": {
            "strategy_id": strategy_id,  # Use .value to get the string representation
            "circuit_divisions": circuit_borders,
        },
    }

    # Save as QuantumCircuitDescriptor file (.qcd)
    with SpooledTemporaryFile(mode="w") as qcd_file:
        json.dump(qcd_output, qcd_file, indent=4)  # Formatted for readability
        qcd_file.seek(0)
        STORE.persist_task_result(
            db_id,
            qcd_file,
            "quantum_circuit_descriptor.qcd",  # File name with appropriate extension
            "application/x-qcd",  # Custom MIME type
            "application/json",  # Underlying data structure is JSON
        )

    TASK_LOGGER.info("Vector encoding completed successfully.")
    return "Successfully encoded vectors into QASM + metadata."
