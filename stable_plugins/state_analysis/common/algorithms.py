import numpy as np


def are_vectors_linearly_dependent(
    vectors: list[np.ndarray], tolerance: float = 1e-10
) -> bool:
    """
    Checks if a list of vectors is linearly dependent.

    Args:
        vectors (list[np.ndarray]): A list of NumPy arrays representing vectors.
        tolerance (float): A small tolerance for numerical stability (default 1e-10).

    Returns:
        bool: True if the vectors are linearly dependent, False otherwise.
    """
    # Convert the list of vectors into a matrix where each vector is a row
    matrix = np.vstack(vectors)

    # Calculate the rank of the matrix
    rank = np.linalg.matrix_rank(matrix, tol=tolerance)

    # If the rank is smaller than the number of vectors, they are linearly dependent
    return rank < len(vectors)


def analyze_lineardependenceinhx(
    states: list[np.ndarray],
    dim_A: int,
    dim_B: int,
    singular_value_tolerance: float = 1e-10,
    linear_independence_tolerance: float = 1e-10,
) -> bool:
    """
    Performs Schmidt decomposition for a list of states, collects relevant basis vectors
    based on singular values, and checks if these basis vectors are linearly independent.

    Args:
        states (list[np.ndarray]): List of states as flat vectors.
        dim_A (int): Dimension of the H_X space.
        dim_B (int): Dimension of the H_R space.
        svdTolerance (float): Threshold to exclude small singular values.
        lindepTolerance (float): Tolerance for determining the matrix rank.

    Returns:
        bool: Whether the collected basis vectors are linearly independent.
    """
    # Collect all relevant basis vectors
    collected_basis = []

    for state in states:
        # Validate input dimensions
        if state.size != dim_A * dim_B:
            raise ValueError("The dimensions of a state do not match dim_A and dim_B.")

        # Reshape the state into matrix form
        state_matrix = state.reshape((dim_A, dim_B))

        # Perform Singular Value Decomposition (SVD)
        u, s, vh = np.linalg.svd(state_matrix)

        # Filter basis vectors based on singular values
        significant_indices = np.where(s > singular_value_tolerance)[0]
        filtered_basis = u[:, significant_indices]

        # Collect filtered basis vectors
        collected_basis.append(filtered_basis)

        # Check linear independence of the combined basis vectors

    if collected_basis:
        return are_vectors_linearly_dependent(
            collected_basis, linear_independence_tolerance
        )
    else:
        return False  # No vectors -> Trivial case, independent


def are_vectors_orthogonal(
    vec1: np.ndarray, vec2: np.ndarray, tolerance: float = 1e-10
) -> bool:
    """
    Checks whether two NumPy vectors are orthogonal, considering complex conjugates for complex vectors.

    Args:
        vec1 (np.ndarray): The first vector.
        vec2 (np.ndarray): The second vector.
        tolerance (float): The tolerance value for checking orthogonality (default is 1e-10).

    Returns:
        bool: True if the vectors are orthogonal, False otherwise.
    """
    # Ensure the vectors have the same length
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have the same dimension.")

    # Compute the dot product using the complex conjugate of vec1
    dot_product = np.vdot(
        vec1, vec2
    )  # Equivalent to sum(conj(vec1[i]) * vec2[i] for i in range(len(vec1)))

    # Check if the dot product is close to zero within the specified tolerance
    return abs(dot_product) <= tolerance


def compute_schmidt_rank(
    state: np.ndarray, dim_A: int, dim_B: int, tolerance: float = 1e-10
) -> int:
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
