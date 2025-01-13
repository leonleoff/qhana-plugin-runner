import numpy as np


def are_vectors_orthogonal(
    vec1: np.ndarray, vec2: np.ndarray, tolerance: float = 1e-10
) -> bool:
    """
    Checks whether two NumPy vectors are orthogonal by calculating their dot product using a for loop.

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

    # Initialize the dot product
    dot_product = 0.0

    # Calculate the dot product using a for loop
    for i in range(len(vec1)):
        dot_product += vec1[i] * vec2[i]

    # Check if the dot product is close to zero within the specified tolerance
    return abs(dot_product) < tolerance
