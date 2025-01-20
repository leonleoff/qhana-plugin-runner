import struct

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from .encoding_strategy import EncodingStrategy


class SplitComplexBinaryEncoding(EncodingStrategy):
    """
    Implementation of an encoding strategy that separates complex numbers
    into real and imaginary parts.
    """

    @property
    def id(self) -> str:
        return "split_complex_binary_encoding"

    def encode(self, vectors: list):
        """
        Encodes a list of complex vectors into QASM code + metadata.

        Returns:
            qasm_code (str),
            circuit_divisions (list)
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

        circuit_divisions = []
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
            circuit_divisions.append(vector_borders)

        total_qubits = len(qbits)
        # Build QASM
        qasm_code = 'OPENQASM 2.0;\ninclude "qelib1.inc";\n\n'
        qasm_code += f"qreg q[{total_qubits}];\n\n"
        for index, bit_val in enumerate(qbits):
            if bit_val == 1:
                qasm_code += f"x q[{index}];\n"

        return qasm_code, circuit_divisions

    def decode(self, qasm_code: str, circuit_divisions):
        """
        Decodes the original vectors from the QASM code + metadata by simulating the circuit statevector.

        Args:
            qasm_code (str): The QASM representation of the circuit.
            circuit_divisions: Metadata about the divisions in the circuit.
            options (dict): Additional decoding options. Example: {'probability_tolerance': 1e-5}

        Returns:
            list: Decoded vectors, each being a list of complex numbers.
        """
        # Default options
        if options is None:
            options = {}
        probability_tolerance = options.get("probability_tolerance", 1e-5)

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
        for vector_borders in circuit_divisions:
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
