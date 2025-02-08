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
    circuit = QuantumCircuit.from_qasm_str(qasm_circuit)
    density = DensityMatrix.from_instruction(circuit)
    last_qubit_index = circuit.num_qubits -1
    density_matrices = []

    for i, interval in enumerate(qubit_intervals):
        lower, upper = interval
        density, change_dim = trace_out_qubits(0, lower - 1, density)
        if change_dim:
            last_qubit_index -= lower
            for j, tup in enumerate(qubit_intervals):
                qubit_intervals[j][0] -= lower
                qubit_intervals[j][1] -= lower

        density_of_state, _ = trace_out_qubits(upper - lower + 1, last_qubit_index, density)
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
     {
        "id": 0,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[4];
        x q[3];
        x q[2];
        x q[1];
        x q[0];
        """,
        "metadata": [[2, 3]],
        "expected": [[0 + 0j, 0 + 0j, 0 + 0j, 1 + 0j]],
    },
    {
        "id": 1,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[4];
        x q[3];
        x q[2];
        x q[1];
        x q[0];
        """,
        "metadata": [[3, 3]],
        "expected": [[0 + 0j, 1 + 0j]],
    },
     {
        "id": 2,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[2];
        """,
        "metadata": [[0, 0], [1, 1]],
        "expected": [[1 + 0j, 0 + 0j], [1 + 0j, 0 + 0j]],
    },
    {
        "id": 3,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[4];
        """,
        "metadata": [[0, 1], [2, 3]],
        "expected": [[1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j], [1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j]],
    },
   
    {
        "id": 4,
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[4];
        x q[3];
        x q[2];
        x q[1];
        x q[0];
        """,
        "metadata": [[4, 4]],
        "expected": [[1]],
    },
   
]

for test in testdata:
    id = test.get("id")
    qasm = test.get("qasmfilecontent")
    meta = test.get("metadata")
    expected = test.get("expected")
    output = generate_reduced_substatevectors(qasm, meta)

    for out_vec, exp_vec in zip(output, expected):
        if not np.allclose(out_vec, exp_vec, atol=1e-6):
            raise ValueError(f"Mismatch in output vector: {out_vec} != {exp_vec}")
    print(f"Passed test with id: {id}")
