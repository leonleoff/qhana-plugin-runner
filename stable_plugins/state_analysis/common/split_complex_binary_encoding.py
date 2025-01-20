# split_complex_binary_encoding.py

import struct
from typing import Any, Dict, List, Tuple

import numpy as np

try:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
except ImportError:
    # If Qiskit is not installed, the user will need to install it.
    pass

from .encoding_strategy import EncodingStrategy


class SplitComplexBinaryEncoding(EncodingStrategy):
    """
    An encoding strategy that splits each complex number into separate real/imag parts
    and maps them onto qubits. Decoding is done by simulating the QASM circuit
    and reconstructing real/imag floats from the measured statevector.
    """

    @property
    def id(self) -> str:
        return "split_complex_binary_encoding"

    def encode(
        self, vectors: List[List[complex]], options: Dict[str, Any] = None
    ) -> Tuple[str, list]:
        """
        Converts a list of vectors (each a list of complex) into QASM + division metadata.
        """

        if options is None:
            options = {}

        def float_to_bits_list(value: float) -> list:
            packed = struct.pack(">f", value)  # 32-bit float in big-endian
            bits = []
            for byte in packed:
                bits.extend([int(bit) for bit in f"{byte:08b}"])
            # Optionally remove trailing zeros
            while bits and bits[-1] == 0:
                bits.pop()
            return bits if bits else [0]

        circuit_divisions = []
        qbits = []
        qbit_index = 0

        # Build qubit mapping
        for vector in vectors:
            vector_borders = []
            for comp_val in vector:
                pair_borders = []

                real_bits = float_to_bits_list(comp_val.real)
                real_lower = qbit_index
                qbit_index += len(real_bits)
                real_upper = qbit_index
                pair_borders.append([real_lower, real_upper])
                qbits.extend(real_bits)

                imag_bits = float_to_bits_list(comp_val.imag)
                imag_lower = qbit_index
                qbit_index += len(imag_bits)
                imag_upper = qbit_index
                pair_borders.append([imag_lower, imag_upper])
                qbits.extend(imag_bits)

                vector_borders.append(pair_borders)
            circuit_divisions.append(vector_borders)

        total_qubits = len(qbits)
        qasm_code = 'OPENQASM 2.0;\ninclude "qelib1.inc";\n\n'
        qasm_code += f"qreg q[{total_qubits}];\n\n"
        for idx, val in enumerate(qbits):
            if val == 1:
                qasm_code += f"x q[{idx}];\n"

        return qasm_code, circuit_divisions

    def decode(
        self, qasm_code: str, circuit_divisions: list, options: Dict[str, Any] = None
    ) -> List[List[complex]]:
        """
        Reconstructs the vectors from QASM code using circuit_divisions.
        A simple statevector simulation is performed, and bits with probability above
        `probability_tolerance` are set to 1, else 0.
        """

        if options is None:
            options = {}
        probability_tolerance = options.get("probability_tolerance", 1e-5)

        def bits_to_float(bits: list) -> float:
            while len(bits) < 32:
                bits.append(0)
            byte_array = bytes(
                int("".join(map(str, bits[i : i + 8])), 2) for i in range(0, 32, 8)
            )
            return struct.unpack(">f", byte_array)[0]

        qc = QuantumCircuit.from_qasm_str(qasm_code)
        st = Statevector.from_instruction(qc)
        probabilities = st.probabilities_dict()

        qbits = [0] * qc.num_qubits

        # For each basis state with prob > threshold, set bits to 1 in an OR-like fashion
        for state, prob in probabilities.items():
            if prob > probability_tolerance:
                for i, bit in enumerate(reversed(state)):
                    if bit == "1":
                        qbits[i] = 1

        # Rebuild vectors
        reconstructed = []
        for vector_borders in circuit_divisions:
            one_vec = []
            for real_imag_borders in vector_borders:
                (real_lower, real_upper) = real_imag_borders[0]
                real_bits = qbits[real_lower:real_upper]
                real_val = bits_to_float(real_bits)

                (imag_lower, imag_upper) = real_imag_borders[1]
                imag_bits = qbits[imag_lower:imag_upper]
                imag_val = bits_to_float(imag_bits)

                one_vec.append(complex(real_val, imag_val))
            reconstructed.append(one_vec)

        return reconstructed
