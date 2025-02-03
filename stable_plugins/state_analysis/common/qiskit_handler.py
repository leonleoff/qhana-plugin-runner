import numpy as np

try:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
except ImportError:
    # If Qiskit is not installed, the user will need to install it.
    pass


# from qasm code to statevector
def toNpVector(qasm_code: str):
    qc = QuantumCircuit.from_qasm_str(qasm_code)
    state = Statevector.from_instruction(qc)
    state_np = np.array(state.data)
    return state_np
