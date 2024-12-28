import numpy as np

def compute_schmidt_rank(state: np.ndarray, dim_A: int, dim_B: int, tolerance: float = 1e-10) -> int:
    """
    Computes the Schmidt rank of a bipartite quantum state using singular value decomposition (SVD).

    Args:
        state (np.ndarray): The state vector representing the bipartite quantum system.
        dim_A (int): Dimension of subsystem A.
        dim_B (int): Dimension of subsystem B.
        tolerance (float): Threshold below which singular values are considered zero (default: 1e-10).

    Returns:
        int: The Schmidt rank of the state, i.e., the number of non-zero Schmidt coefficients.
    """
    # Step 1: Reshape the state vector into a matrix of shape (dim_A, dim_B)
    # Each row corresponds to a basis state of subsystem A
    # Each column corresponds to a basis state of subsystem B
    matrix = state.reshape((dim_A, dim_B))
    
    # Step 2: Perform singular value decomposition (SVD) on the matrix
    # U, S, Vh are the unitary matrices and singular values
    U, S, Vh = np.linalg.svd(matrix)
    
    # Step 3: Count the number of singular values greater than the tolerance
    # Non-zero singular values correspond to Schmidt coefficients
    schmidt_rank = np.sum(S > tolerance)
    
    return schmidt_rank