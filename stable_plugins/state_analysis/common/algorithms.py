from typing import List

import numpy as np

DEFAULT_TOLERANCE = 1e-10


def are_vectors_linearly_dependent(
    vectors: List[np.ndarray], tolerance: float = DEFAULT_TOLERANCE
) -> bool:
    """
    Checks if a list of vectors is linearly dependent.

    Args:
        vectors (List[np.ndarray]): A list of NumPy arrays representing vectors.
        tolerance (float): A small tolerance for numerical stability (default 1e-10).

    Returns:
        bool: True if the vectors are linearly dependent, False otherwise.

    Raises:
        ValueError: If the list of vectors is empty or if the vectors have different shapes.
        TypeError: If any element in the list is not a NumPy array.
    """

    # Set default for tolerance
    if tolerance is None:
        tolerance = DEFAULT_TOLERANCE

    # Validate input
    if not vectors:
        raise ValueError("The input list of vectors is empty.")

    if not all(isinstance(vec, np.ndarray) for vec in vectors):
        raise TypeError("All elements in the input list must be NumPy arrays.")

    if not all(vec.shape == vectors[0].shape for vec in vectors):
        raise ValueError(f"All vectors must have the same shape. All vectors={vectors}")

    try:
        # Convert the list of vectors into a matrix where each vector is a row
        matrix = np.vstack(vectors)

        # Calculate the rank of the matrix
        rank = np.linalg.matrix_rank(matrix, tol=tolerance)

        # If the rank is smaller than the number of vectors, they are linearly dependent
        return rank < len(vectors)
    except np.linalg.LinAlgError as e:
        raise RuntimeError(f"An error occurred while computing the matrix rank: {e}")


def analyze_lineardependenceinhx(
    states: List[np.ndarray],
    dim_A: int,
    dim_B: int,
    singular_value_tolerance: float = DEFAULT_TOLERANCE,
    linear_independence_tolerance: float = DEFAULT_TOLERANCE,
) -> bool:
    """
    Performs Schmidt decomposition for a list of states, collects relevant basis vectors
    based on singular values, and checks if these basis vectors are linearly independent.

    Args:
        states (List[np.ndarray]): List of states as flat vectors.
        dim_A (int): Dimension of subsystem A.
        dim_B (int): Dimension of subsystem B.
        singular_value_tolerance (float): Threshold to exclude small singular values.
        linear_independence_tolerance (float): Tolerance for determining the matrix rank.

    Returns:
        bool: True if the collected basis vectors are linearly dependent, False otherwise.

    Raises:
        ValueError: If any state has dimensions that do not match `dim_A * dim_B`.
        TypeError: If `states` is not a list of NumPy arrays.
    """
    # Set default for tolerance
    if singular_value_tolerance is None:
        singular_value_tolerance = DEFAULT_TOLERANCE
    if linear_independence_tolerance is None:
        linear_independence_tolerance = DEFAULT_TOLERANCE

    # Input validation
    if not isinstance(states, list):
        raise TypeError("`states` must be a list of NumPy arrays.")
    if not all(isinstance(state, np.ndarray) for state in states):
        raise TypeError("All elements in `states` must be NumPy arrays.")
    if not all(state.size == dim_A * dim_B for state in states):
        raise ValueError("Each state must have dimensions matching `dim_A * dim_B`.")

    # Collect all relevant basis vectors
    collected_basis = []

    for state in states:
        try:
            # Reshape the state into matrix form
            state_matrix = state.reshape((dim_A, dim_B))

            # Perform Singular Value Decomposition (SVD)
            u, s, vh = np.linalg.svd(state_matrix)

            # Filter basis vectors based on singular values
            filtered_basis = []
            for index, singular_value in enumerate(s):
                if singular_value > singular_value_tolerance:
                    basis = u[index]
                    print("gefundene basis", basis)
                    filtered_basis.append(basis)

            # Collect filtered basis vectors
            for base in filtered_basis:
                collected_basis.append(base)
        except np.linalg.LinAlgError as e:
            raise RuntimeError(
                f"An error occurred during SVD of a state: {state}: {e}"
            ) from e

    # Check linear independence of the collected basis vectors
    if collected_basis:
        return are_vectors_linearly_dependent(
            collected_basis, linear_independence_tolerance
        )

    # No vectors -> Independent by default
    return False


def are_vectors_orthogonal(
    vec1: np.ndarray, vec2: np.ndarray, tolerance: float = DEFAULT_TOLERANCE
) -> bool:
    """
    Checks whether two NumPy vectors are orthogonal, considering complex conjugates for complex vectors.

    Args:
        vec1 (np.ndarray): The first vector.
        vec2 (np.ndarray): The second vector.
        tolerance (float): The tolerance value for checking orthogonality (default is 1e-10).

    Returns:
        bool: True if the vectors are orthogonal, False otherwise.

    Raises:
        ValueError: If the vectors do not have the same dimension.
        TypeError: If the inputs are not NumPy arrays or cannot be interpreted as such.
    """
    # Set default for tolerance
    if tolerance is None:
        tolerance = DEFAULT_TOLERANCE

    # Input validation
    if not isinstance(vec1, np.ndarray) or not isinstance(vec2, np.ndarray):
        raise TypeError("Both inputs must be NumPy arrays.")

    if vec1.ndim != 1 or vec2.ndim != 1:
        raise ValueError(
            f"Both inputs must be 1-dimensional arrays (vectors). vec1: {vec1}, vec2: {vec2}"
        )

    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have the same dimension.")

    try:
        # Compute the dot product using the complex conjugate of vec1
        dot_product = np.vdot(vec1, vec2)  # Handles complex vectors correctly
    except Exception as e:
        raise RuntimeError(f"An error occurred while computing the dot product: {e}")

    # Check if the dot product is close to zero within the specified tolerance
    is_orthogonal = abs(dot_product) <= tolerance

    return is_orthogonal


def compute_schmidt_rank(
    state: np.ndarray, dim_A: int, dim_B: int, tolerance: float = DEFAULT_TOLERANCE
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

    Raises:
        ValueError: If the dimensions `dim_A * dim_B` do not match the size of `state`.
        TypeError: If the input `state` is not a NumPy array or if dimensions are invalid.
    """
    # Set default for tolerance
    if tolerance is None:
        tolerance = DEFAULT_TOLERANCE

    # Input validation
    if not isinstance(state, np.ndarray):
        raise TypeError("The input `state` must be a NumPy array.")
    if not isinstance(dim_A, int) or not isinstance(dim_B, int):
        raise TypeError("`dim_A` and `dim_B` must be integers.")
    if dim_A <= 0 or dim_B <= 0:
        raise ValueError("`dim_A` and `dim_B` must be positive integers.")
    if state.size != dim_A * dim_B:
        raise ValueError("The size of `state` must match the product `dim_A * dim_B`.")

    try:
        # Step 1: Reshape the state vector into a matrix of shape (dim_A, dim_B)
        matrix = state.reshape((dim_A, dim_B))

        # U, S, Vh are the unitary matrices and singular values
        U, S, Vh = np.linalg.svd(matrix)

        # Step 3: Count the number of singular values greater than the tolerance
        schmidt_rank = np.sum(S > tolerance)
    except np.linalg.LinAlgError as e:
        raise RuntimeError(f"An error occurred during the SVD computation: {e}")

    return schmidt_rank
