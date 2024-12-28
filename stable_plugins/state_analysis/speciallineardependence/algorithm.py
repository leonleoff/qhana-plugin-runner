import numpy as np

def analyze_schmidt_basis(state: np.ndarray, dim_A: int, dim_B: int, tolerance: float = 1e-10) -> bool:
    """
    Führt die Schmidt-Zerlegung eines Zustands durch, filtert Basisvektoren basierend
    auf den Singularwerten und überprüft, ob diese linear unabhängig sind.

    Args:
        state (np.ndarray): Der Zustand als flacher Vektor.
        dim_x (int): Dimension des H_X-Raums.
        dim_r (int): Dimension des H_R-Raums.
        tolerance (float): Schwellenwert, um kleine Singularwerte auszuschließen.

    Returns:
        dict: Ein Dictionary mit den folgenden Schlüsseln:
            - 'filtered_basis': Die gefilterten Basisvektoren im H_X-Raum.
            - 'singular_values': Die Singularwerte der Zerlegung.
            - 'is_independent': Ob die gefilterten Basisvektoren linear unabhängig sind.
    """
    # Zustand in Matrixform umformen
    state = state.reshape((dim_A, dim_B))

    # SVD durchführen
    u, s, vh = np.linalg.svd(state)

    # Filtere die Basisvektoren basierend auf den Singularwerten
    significant_indices = np.where(s > tolerance)[0]
    filtered_basis = u[:, significant_indices]  # Nur relevante Basisvektoren behalten

    # Überprüfung der linearen Unabhängigkeit
    rank = np.linalg.matrix_rank(filtered_basis)
    is_independent = rank == filtered_basis.shape[1]  # Rang sollte Anzahl der Vektoren entsprechen

    return  is_independent