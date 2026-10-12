import numpy as np


def phase_shifter(phase):
    """
    Create a 2x2 phase-shifter unitary matrix.

    phase:
        Phase shift in radians.
    """

    return np.array([
        [np.exp(1j * phase), 0],
        [0, 1]
    ], dtype=complex)