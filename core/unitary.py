import numpy as np


def apply_unitary(state, unitary):
    """
    Apply a unitary matrix to a quantum state.
    """
    state = np.asarray(state, dtype=complex)
    unitary = np.asarray(unitary, dtype=complex)

    if unitary.shape[1] != len(state):
        raise ValueError("Matrix and state dimensions do not match.")

    return unitary @ state


def is_unitary(matrix, tolerance=1e-10):
    """
    Check whether a matrix is unitary.
    """
    matrix = np.asarray(matrix, dtype=complex)

    identity = np.eye(matrix.shape[0])

    return np.allclose(
        matrix.conj().T @ matrix,
        identity,
        atol=tolerance
    )