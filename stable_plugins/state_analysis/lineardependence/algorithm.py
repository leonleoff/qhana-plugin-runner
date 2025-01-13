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
