import numpy as np


def beam_splitter(transmission=0.5):
    """
    Create a 2x2 beam splitter unitary matrix.

    transmission:
        Fraction of intensity transmitted.
        Must be between 0 and 1.
    """

    if transmission < 0 or transmission > 1:
        raise ValueError("Transmission must be between 0 and 1.")

    t = np.sqrt(transmission)
    r = np.sqrt(1 - transmission)

    return np.array([
        [t, r],
        [r, -t]
    ], dtype=complex)