import numpy as np


def normalize_state(state):
    """
    Normalize a quantum state vector.
    """
    state = np.asarray(state, dtype=complex)

    norm = np.linalg.norm(state)

    if norm == 0:
        raise ValueError("State vector cannot be zero.")

    return state / norm


def probabilities(state):
    """
    Calculate measurement probabilities from a state vector.
    """
    state = normalize_state(state)

    return np.abs(state) ** 2


def basis_state(index, dimension):
    """
    Create a basis state.

    Example:
    basis_state(0, 2) -> [1, 0]
    basis_state(1, 2) -> [0, 1]
    """
    if index < 0 or index >= dimension:
        raise ValueError("Invalid basis-state index.")

    state = np.zeros(dimension, dtype=complex)
    state[index] = 1

    return state