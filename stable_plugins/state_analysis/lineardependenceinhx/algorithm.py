import numpy as np


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

    # Combine all collected basis vectors into a single matrix
    if collected_basis:
        combined_basis = np.vstack(collected_basis)
    else:
        combined_basis = np.array([])

    # Check linear independence of the combined basis vectors
    if combined_basis.size > 0:
        rank = np.linalg.matrix_rank(combined_basis, tol=linear_independence_tolerance)
        return rank < len(combined_basis)
    else:
        return False  # No vectors -> Trivial case, independent


# Example usage
if __name__ == "__main__":
    # Example states
    state1 = np.random.rand(6)  # Flat vector for dim_A=2, dim_B=3
    state2 = np.random.rand(6)

    result = analyze_lineardependenceinhx([state1, state2], dim_A=2, dim_B=3)

    print("Are the vectors linearly independent?", result)
