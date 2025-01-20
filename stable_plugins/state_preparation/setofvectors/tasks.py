import json
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
    Encodes a given list of complex vectors into a .qcd (QuantumCircuitDescriptor)
    using the specified encoding strategy.
    """

    TASK_LOGGER.info(f"Starting vector-encoding task with db_id={db_id}")
    task_data: Optional[ProcessingTask] = ProcessingTask.get_by_id(db_id)
    if not task_data:
        msg = f"No task data for DB ID {db_id}!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    parameters = loads(task_data.parameters or "{}")
    vectors = parameters.get("vectors", [])
    strategy_id = parameters.get("strategy_id")

    # Convert input to Python complex
    python_vectors = [[complex(re, im) for (re, im) in vector] for vector in vectors]

    TASK_LOGGER.info(f"Encoding {len(python_vectors)} vectors...")

    strategy = EncodingRegistry.get_strategy(strategy_id)

    # Perform encoding
    qasm_code, circuit_borders = strategy.encode(python_vectors, options=None)

    # Construct a QuantumCircuitDescriptor structure
    qcd_output = {
        "circuit": qasm_code,
        "metadata": {
            "strategy_id": strategy_id,
            "circuit_divisions": circuit_borders,
        },
    }

    # Save as a .qcd file (JSON-based)
    with SpooledTemporaryFile(mode="w") as qcd_file:
        json.dump(qcd_output, qcd_file, indent=4)
        qcd_file.seek(0)
        STORE.persist_task_result(
            db_id,
            qcd_file,
            "quantum_circuit_descriptor.qcd",
            "application/x-qcd",
            "application/json",
        )

    TASK_LOGGER.info("Vector encoding completed successfully.")
    return "Encoded vectors into a .qcd (QASM + metadata)."
