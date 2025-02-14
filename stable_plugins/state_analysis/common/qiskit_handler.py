from typing import List

import numpy as np

try:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import DensityMatrix, partial_trace
except ImportError:
    pass


def generate_reduced_substatevectors(
    qasm_circuit: str, qubit_intervals: List[List[int]]
) -> List[np.ndarray]:
    """
    Generates reduced substatevectors from a given QASM circuit and a list of qubit intervals.

    Parameters:
        qasm_circuit (str): The QASM string representation of a quantum circuit.
        qubit_intervals (List[List[int]]): List of intervals, where each interval is [start, end].

    Returns:
        List[np.ndarray]: List of reduced substatevectors.
    """

    circuit = QuantumCircuit.from_qasm_str(qasm_circuit)
    last_qubit_index = circuit.num_qubits - 1

    # Validate input intervals
    start, end = qubit_intervals[-1]
    if end > last_qubit_index:
        raise ValueError(
            f"The last Interval ends at {end}, which exceeds the last qubit index ({last_qubit_index})."
        )
    density = DensityMatrix.from_instruction(circuit)
    density_matrices = []

    for i, interval in enumerate(qubit_intervals):
        lower, upper = interval
        density, change_dim = trace_out_qubits(0, lower - 1, density)
        if change_dim:
            last_qubit_index -= lower
            for j, tup in enumerate(qubit_intervals):
                qubit_intervals[j][0] -= lower
                qubit_intervals[j][1] -= lower

        density_of_state, _ = trace_out_qubits(
            upper - lower + 1, last_qubit_index, density
        )
        density_matrices.append(density_of_state)

    output = []
    for density in density_matrices:
        dmatrix = density
        eigenvals, eigenvecs = np.linalg.eig(dmatrix)
        idx = np.where(np.isclose(eigenvals, 1, atol=1e-6))[0]

        if len(idx) == 0:
            raise Exception(
                "Cannot see interval of qubit as an independent state because it has entanglement with other qubits outside of the interval"
            )

        sub_vec = eigenvecs[:, idx[0]]
        output.append(sub_vec)

    return output


def trace_out_qubits(lower: int, upper: int, density_matrix):
    """
    Performs a partial trace over a specified range of qubits in a density matrix.

    This function takes a lower bound `lower`, an upper bound `upper`, and a density matrix `density_matrix`.
    - If `lower <= upper`, it traces out all qubits in the range `[lower, upper]` (inclusive).
    - If no qubits are traced out (`lower > upper`), the function returns the original density matrix and `False`.
    - Otherwise, it returns the reduced density matrix and `True`.

    The function also verifies that the specified qubit range is within the valid range of the system.

    Parameters:
        lower (int): The lower bound (inclusive) of the qubit indices to trace out.
        upper (int): The upper bound (inclusive) of the qubit indices to trace out.
        density_matrix (DensityMatrix): The density matrix of the quantum system.

    Returns:
        tuple (DensityMatrix, bool):
            - The reduced density matrix if `lower <= upper`, otherwise the original matrix.
            - A boolean indicating whether any qubits were traced out.

    Raises:
        ValueError: If the given qubit range is out of bounds.

    Example:
        >>> from qiskit.quantum_info import DensityMatrix
        >>> density = DensityMatrix.from_label('00')
        >>> reduced_density, changed = trace_out_qubits(0, 0, density)
    """
    num_qubits = density_matrix.num_qubits  # Get total number of qubits
    if lower > upper:
        return density_matrix, False  # No qubits to trace out

    # Ensure the range is valid
    if lower < 0 or upper >= num_qubits:
        raise ValueError(f"Qubit indices out of range: must be in [0, {num_qubits-1}]")

    qubits_to_trace_out = list(range(lower, upper + 1))

    reduced_density = partial_trace(density_matrix, qubits_to_trace_out)
    return reduced_density, True


testdata = [
    # whole state
    {
        "id": 0,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[4];
        x q[3];
        """,
        "metadata": [[0, 3]],
        "expected": [
            [
                # 0
                0 + 0j,
                0 + 0j,
                0 + 0j,
                0 + 0j,
                # 4
                0 + 0j,
                0 + 0j,
                0 + 0j,
                0 + 0j,
                # 8
                1 + 0j,
                0 + 0j,
                0 + 0j,
                0 + 0j,
                # 12
                0 + 0j,
                0 + 0j,
                0 + 0j,
                0 + 0j,
                # 16
            ]
        ],
    },
    # middle part of state not beginning at 0 not ending at 3
    {
        "id": 1,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[4];
        x q[3];
        """,
        "metadata": [[1, 2]],
        "expected": [
            [
                1 + 0j,
                0 + 0j,
                0 + 0j,
                0 + 0j,
            ],
        ],
    },
    # two parts of state
    {
        "id": 2,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[4];
        x q[3];
        """,
        "metadata": [[0, 1], [2, 3]],
        "expected": [
            [
                1 + 0j,
                0 + 0j,
                0 + 0j,
                0 + 0j,
            ],
            [
                0 + 0j,
                0 + 0j,
                1 + 0j,
                0 + 0j,
            ],
        ],
    },
    # small part of state
    {
        "id": 3,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[4];
        x q[3];
        """,
        "metadata": [[2, 2]],
        "expected": [
            [
                1 + 0j,
                0 + 0j,
            ],
        ],
    },
    # small part of state
    {
        "id": 4,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[4];
        x q[3];
        """,
        "metadata": [[3, 3]],
        "expected": [
            [
                0 + 0j,
                1 + 0j,
            ],
        ],
    },
    # a lot of small parts of state
    {
        "id": 5,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[4];
        x q[3];
        """,
        "metadata": [[0, 0], [1, 1], [2, 2], [3, 3]],
        "expected": [
            [
                1 + 0j,
                0 + 0j,
            ],
            [
                1 + 0j,
                0 + 0j,
            ],
            [
                1 + 0j,
                0 + 0j,
            ],
            [
                0 + 0j,
                1 + 0j,
            ],
        ],
    },
    # entangeld part of state
    {
        "id": 6,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[4];
        h q[1];
        cx q[1], q[2];
        """,
        "metadata": [[1, 2]],
        "expected": [(1 / np.sqrt(2)) * np.array([1, 0, 0, 1])],
    },
    # bigger part of entangled state
    {
        "id": 7,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[4];
        h q[1];
        cx q[1], q[2];
        """,
        "metadata": [[0, 2]],
        "expected": [(1 / np.sqrt(2)) * np.array([1, 0, 0, 0, 0, 0, 1, 0])],
    },
    # erro because entanglemet is crossing the borders
    {
        "id": 8,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[4];
        h q[1];
        cx q[1], q[2];
        """,
        "metadata": [[0, 1]],
        "expected": None,
        "throws": True,
    },
    # basic case
    {
        "id": 9,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[2];
        """,
        "metadata": [[0, 0], [1, 1]],
        "expected": [[1 + 0j, 0 + 0j], [1 + 0j, 0 + 0j]],
    },
    {
        # basic case
        "id": 10,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[2];
        x q[0];
        """,
        "metadata": [[0, 1]],
        "expected": [[0 + 0j, 1 + 0j, 0 + 0j, 0 + 0j]],
    },
    {
        # basic case
        "id": 11,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[2];
        x q[0];
        x q[1];
        """,
        "metadata": [[0, 1]],
        "expected": [[0 + 0j, 0 + 0j, 0 + 0j, 1 + 0j]],
    },
    {
        "id": 12,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[3];
        // Keine Gates -> Zustand |000>
        """,
        "metadata": [[0, 2]],
        "expected": [[1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j, 0 + 0j, 0 + 0j, 0 + 0j, 0 + 0j]],
    },
]


for test in testdata:
    id = test.get("id")
    qasm = test.get("qasmfilecontent")
    meta = test.get("metadata")
    expected = test.get("expected")
    throws: bool = test.get("throws", False)

    try:
        output = generate_reduced_substatevectors(qasm, meta)

    except Exception as e:
        if not throws:
            raise e

    if not throws:
        for out_vec, exp_vec in zip(output, expected):
            if not np.allclose(out_vec, exp_vec, atol=1e-6):
                raise ValueError(f"Mismatch in output vector: {out_vec} != {exp_vec}")
    print(f"Passed test with id: {id}")
