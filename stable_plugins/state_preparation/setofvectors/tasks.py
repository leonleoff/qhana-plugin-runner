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

    # Lade die Parameter
    parameters = loads(task_data.parameters or "{}")
    vectors = parameters.get("vectors", [])  # an array of arrays of [re,im] ?

    # Wandle in Python-Complex-Listen um
    # Sofern noch nicht komplex:
    python_vectors = []
    for vec in vectors:
        # "vec" = list of [re, im]
        complex_nums = []
        for pair in vec:
            re, im = pair
            complex_nums.append(complex(re, im))
        python_vectors.append(complex_nums)

    TASK_LOGGER.info(f"Encoding {len(python_vectors)} vectors...")

    # Rufe encoding auf

    strategy_id = "split_complex_binary_encoding"
    strategy = EncodingRegistry.get_strategy(strategy_id)

    qasm_code, circuit_borders = strategy.encode(python_vectors, None)

    # Erstelle die QuantumCircuitDescriptor-Struktur
    qcd_output = {
        "circuit": qasm_code,
        "metadata": {
            "strategy_id": "split_complex_binary_encoding",
            "circuit_divisions": circuit_borders,
        },
    }

    # Speichere als QuantumCircuitDescriptor-Datei (.qcd)
    with SpooledTemporaryFile(mode="w") as qcd_file:
        json.dump(qcd_output, qcd_file, indent=4)  # Formatiert für bessere Lesbarkeit
        qcd_file.seek(0)
        STORE.persist_task_result(
            db_id,
            qcd_file,
            "quantum_circuit_descriptor.qcd",  # Dateiname mit passender Endung
            "application/x-qcd",  # Eigener MIME-Typ
            "application/json",  # Unterliegende Datenstruktur ist JSON
        )

    TASK_LOGGER.info("Vector encoding completed successfully.")
    return "Successfully encoded vectors into QASM + metadata."
