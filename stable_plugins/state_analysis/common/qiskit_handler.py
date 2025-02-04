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
    last_qubit_index = circuit.num_qubits

    density_matrices = []

    for i, interval in enumerate(qubit_intervals):
        lower, upper = interval

        density, changeDim = traceOut(0, lower, density)
        last_qubit_index = last_qubit_index - lower
        densityOfState, check = traceOut(upper - lower + 1, last_qubit_index, density)

        density_matrices.append(densityOfState)
        if changeDim:
            for j, tuple in enumerate(qubit_intervals):
                qubit_intervals[j][0] = qubit_intervals[j][0] - (lower + 2)
                qubit_intervals[j][1] = qubit_intervals[j][1] - (lower + 2)

    output = []

    for density in density_matrices:
        dmatrix = density  # Annahme: Die Dichtematrix liegt im ._data-Attribut

        # Berechnung der Eigenwerte und Eigenvektoren
        eigenvals, eigenvecs = np.linalg.eig(dmatrix)

        # Prüfe, ob ein Eigenwert exakt oder numerisch nahe 1 ist
        idx = np.where(np.isclose(eigenvals, 1, atol=1e-6))[0]

        if len(idx) == 0:
            raise Exception(
                "Cannot see interval of qubit as an independent state "
                "because it has entanglement with other qubits outside of the interval"
            )

        # Falls mehrere Eigenwerte nahe 1 sind, nehmen wir den ersten gefundenen
        sub_vec = eigenvecs[:, idx[0]]

        # Speichere den Eigenvektor in der Output-Liste
        output.append(sub_vec)

    return output


def traceOut(a: int, b: int, density):
    qbitsTotraceOut = []
    for i in range(a, b):
        qbitsTotraceOut.append(i)
    if len(qbitsTotraceOut) == 0:
        return density, False
    return partial_trace(density, qbitsTotraceOut), True


testdata = [
    {
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[2];
        """,
        "metadata": [[0, 0], [1, 1]],
        "excepted": [[1 + 0j, 0 + 0j], [1 + 0j, 0 + 0j]],
    },
    {
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[4];
        """,
        "metadata": [[0, 1], [2, 3]],
        "excepted": [[1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j], [1 + 0j, 0 + 0j, 0 + 0j, 0 + 0j]],
    },
    {
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
        "excepted": [[1 + 0j]],
    },
    {
        "qasmfilecontent": """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[4];
        x q[3];
        x q[2];
        x q[1];
        x q[0];
        """,
        "metadata": [[3, 4]],
        "excepted": [[0 + 0j, 1 + 0j]],
    },
]
for test in testdata:
    qasm = test.get("qasmfilecontent")
    meta = test.get("metadata")
    exp = test.get("excepted")
    output = generate_reduced_substatevectors(qasm, meta)
    # TODO compare output
