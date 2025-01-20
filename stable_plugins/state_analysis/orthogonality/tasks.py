import json
import struct
from json import loads
from tempfile import SpooledTemporaryFile
from typing import Optional

import numpy as np
from celery.utils.log import get_task_logger
from qhana_plugin_runner.celery import CELERY
from qhana_plugin_runner.db.models.tasks import ProcessingTask
from qhana_plugin_runner.requests import get_mimetype, open_url
from qhana_plugin_runner.storage import STORE

# qiskit imports (make sure qiskit is installed!)
try:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
except ImportError as e:
    # If needed, raise or log an error
    pass

from common.algorithms import are_vectors_orthogonal

from . import ClassicalStateAnalysisOrthogonality

TASK_LOGGER = get_task_logger(__name__)


def decode_binary_to_vectors_from_qasm(
    qasm_code: str, circuit_borders: list, probability_tolerance: float
):
    """
    Decodes the original vectors from the QASM code + metadata by simulating the circuit statevector.

    Returns: list of vectors, each is a list[complex].
    """

    def bits_to_float(bits):
        # 32-bit => pad with zeros
        while len(bits) < 32:
            bits.append(0)
        byte_array = bytes(
            int("".join(map(str, bits[i : i + 8])), 2) for i in range(0, 32, 8)
        )
        return struct.unpack(">f", byte_array)[0]

    # Build circuit
    qc = QuantumCircuit.from_qasm_str(qasm_code)
    st = Statevector.from_instruction(qc)
    probabilities = st.probabilities_dict()

    # We have e.g. 7 qubits => each state is "xxx..." string => '1010110'
    # We pick the "dominant" state (or combine?)
    # For a simple approach: if a state has probability > probability_tolerance => set the bits
    # We'll just do an OR approach.
    num_qubits = qc.num_qubits
    qbits = [0] * num_qubits

    for state, prob in probabilities.items():
        if prob > probability_tolerance:
            # state is e.g. '0101' => reversed indexing
            # in Qiskit, state[0] is the least significant bit, I think.
            # We might need to confirm.
            # We'll do: reversed(state) => [ i in range(num_qubits) ]
            for i, bit in enumerate(reversed(state)):
                if bit == "1":
                    qbits[i] = 1

    # decode now
    vectors = []
    for vector_borders in circuit_borders:
        # each vector is a list of "number_borders" (real, imag)
        vector = []
        for number_borders in vector_borders:
            real_lower, real_upper = number_borders[0]  # [lower, upper]
            real_bits = qbits[real_lower:real_upper]
            real_part = bits_to_float(real_bits)

            imag_lower, imag_upper = number_borders[1]
            imag_bits = qbits[imag_lower:imag_upper]
            imag_part = bits_to_float(imag_bits)

            vector.append(complex(real_part, imag_part))
        vectors.append(vector)

    return vectors


@CELERY.task(
    name=f"{ClassicalStateAnalysisOrthogonality.instance.identifier}.orthogonality_task",
    bind=True,
)
def orthogonality_task(self, db_id: int) -> str:
    TASK_LOGGER.info(f"Starting 'orthogonality' task with database ID '{db_id}'.")

    # load
    task_data = ProcessingTask.get_by_id(id_=db_id)
    if not task_data:
        msg = f"Task data with ID {db_id} could not be loaded!"
        TASK_LOGGER.error(msg)
        raise KeyError(msg)

    parameters = loads(task_data.parameters or "{}")
    TASK_LOGGER.info(f"Parameters: {parameters}")

    # read from parameters
    vectors = parameters.get("vectors")  # e.g. [ [ [re,im], ... ], [ [re,im], ... ] ]
    circuit = parameters.get("circuit")  # e.g. "some://url"
    prob_tol = parameters.get("probability_tolerance") or 1e-5
    inner_tol = parameters.get("innerproduct_tolerance") or 1e-10

    # final: we want exactly 2 vectors to test orthogonality
    # approach:
    # 1) if vectors exist -> do the old way
    # 2) else if circuit exist -> decode from circuit
    # 3) call are_vectors_orthogonal

    try:
        if vectors is not None:
            # "vectors" is set of two complex vectors
            # transform to numpy
            new_set_of_vectors = []
            for vector in vectors:
                complex_numbers = [complex(pair[0], pair[1]) for pair in vector]
                new_set_of_vectors.append(np.array(complex_numbers))

            if len(new_set_of_vectors) != 2:
                raise ValueError(
                    "Exactly two vectors are required for orthogonality check!"
                )
            vec1, vec2 = new_set_of_vectors

        elif circuit is not None:
            # Fetch the circuit data using open_url
            with open_url(circuit) as circuit_response:
                content = circuit_response.text

            # Parse the JSON content
            circuit_json = json.loads(content)
            qasm_code = circuit_json["qasm_code"]
            circuit_borders = circuit_json["circuitBorders"]

            # Decode the vectors
            decoded_vectors = decode_binary_to_vectors_from_qasm(
                qasm_code, circuit_borders, probability_tolerance=prob_tol
            )

            if len(decoded_vectors) != 2:
                raise ValueError(
                    "Circuit must decode exactly two vectors for orthogonality check!"
                )

            vec1 = np.array(decoded_vectors[0])
            vec2 = np.array(decoded_vectors[1])
        else:
            raise ValueError("Neither vectors nor circuit input found!")

        # now do are_vectors_orthogonal
        result = are_vectors_orthogonal(vec1, vec2, tolerance=inner_tol)

        # Build output
        output_data = {
            "result": bool(result),
            "vectorsUsed": 2,
            "inputType": "vectors" if vectors else "circuit",
        }

        # persist
        with SpooledTemporaryFile(mode="w") as txt_file:
            txt_file.write(str(output_data))
            txt_file.seek(0)
            STORE.persist_task_result(
                db_id,
                txt_file,
                "out.txt",
                "custom/orthogonality-output",
                "text/plain",
            )

        with SpooledTemporaryFile(mode="w") as json_file:
            json.dump(output_data, json_file)
            json_file.seek(0)
            STORE.persist_task_result(
                db_id,
                json_file,
                "out.json",
                "custom/orthogonality-output",
                "application/json",
            )

        TASK_LOGGER.info(f"Orthogonality result: {output_data}")
        return json.dumps(output_data)

    except Exception as e:
        TASK_LOGGER.error(f"Error in orthogonality task: {e}")
        raise
