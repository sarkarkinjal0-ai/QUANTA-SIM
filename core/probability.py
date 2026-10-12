import numpy as np


def calculate_probabilities(state):
    """
    Calculate measurement probabilities from a quantum state.
    """
    state = np.asarray(state, dtype=complex)

    probabilities = np.abs(state) ** 2

    total = np.sum(probabilities)

    if not np.isclose(total, 1.0):
        probabilities = probabilities / total

    return probabilities


def probability_amplitudes(state):
    """
    Return the probability amplitudes of a state.
    """
    return np.asarray(state, dtype=complex)