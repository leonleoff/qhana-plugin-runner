import json
import struct
from json import loads
from tempfile import SpooledTemporaryFile
from typing import Optional

from celery.utils.log import get_task_logger

from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.storage import STORE

from . import VectorEncodingPlugin

TASK_LOGGER = get_task_logger(__name__)


def binary_encoding(vectors: list):
    """
    Encodes a list of complex vectors into QASM code + metadata.

    Returns:
        qasm_code (str),
        circuit_borders (list),
        qbits (list of 0/1).
    """

    def float_to_bits_list(value: float) -> list:
        """Converts a float into a list of bits using IEEE 754 standard (single precision)."""
        packed = struct.pack(">f", value)  # big-endian 32-bit float
        bits = []
        for byte in packed:
            bits.extend([int(bit) for bit in f"{byte:08b}"])
        # optional: remove trailing zeros
        while bits and bits[-1] == 0:
            bits.pop()
        return bits if bits else [0]

    circuit_borders = []
    qbits = []
    qbit_index = 0

    for vector in vectors:  # vector: list of complex numbers
        vector_borders = []
        for complex_number in vector:
            number_borders = []

            # real part
            real_bits = float_to_bits_list(complex_number.real)
            lower_border = qbit_index
            qbit_index += len(real_bits)
            upper_border = qbit_index
            number_borders.append([lower_border, upper_border])
            qbits.extend(real_bits)

            # imag part
            imag_bits = float_to_bits_list(complex_number.imag)
            lower_border = qbit_index
            qbit_index += len(imag_bits)
            upper_border = qbit_index
            number_borders.append([lower_border, upper_border])
            qbits.extend(imag_bits)

            vector_borders.append(number_borders)
        circuit_borders.append(vector_borders)

    total_qubits = len(qbits)
    # Build QASM
    qasm_code = 'OPENQASM 2.0;\ninclude "qelib1.inc";\n\n'
    qasm_code += f"qreg q[{total_qubits}];\n\n"
    for index, bit_val in enumerate(qbits):
        if bit_val == 1:
            qasm_code += f"x q[{index}];\n"

    return qasm_code, circuit_borders, qbits


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
    qasm_code, circuit_borders, qbits = binary_encoding(python_vectors)

    # Speichere QASM als "encoded_circuit.qasm"
    with SpooledTemporaryFile(mode="w") as qasm_file:
        qasm_file.write(str(qasm_code))
        qasm_file.seek(0)
        STORE.persist_task_result(
            db_id,
            qasm_file,
            "encoded_circuit.qasm",
            "executable/circuit",
            "text/x-qasm",
        )

    # Speichere circuit_borders als JSON
    circuit_borders_dict = {
        "circuitBorders": circuit_borders,
        "encodedQbits": qbits,
    }
    with SpooledTemporaryFile(mode="w") as borders_file:
        json.dump(circuit_borders_dict, borders_file)
        borders_file.seek(0)
        STORE.persist_task_result(
            db_id,
            borders_file,
            "circuit_borders.json",
            "application/json",
            "application/json",
        )

    TASK_LOGGER.info("Vector encoding completed successfully.")
    return "Successfully encoded vectors into QASM + metadata."
