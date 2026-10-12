import numpy as np


def hom_interference(distinguishability=0.0):
    """
    Calculate HOM interference with photon distinguishability.

    distinguishability:
        0.0 -> completely indistinguishable photons
        1.0 -> completely distinguishable photons
    """

    if distinguishability < 0 or distinguishability > 1:
        raise ValueError(
            "Distinguishability must be between 0 and 1."
        )

    # 50:50 beam splitter
    t = 1 / np.sqrt(2)
    r = 1 / np.sqrt(2)

    # Ideal indistinguishable-photon amplitudes
    amplitude_20 = np.sqrt(2) * t * r
    amplitude_11 = t**2 - r**2
    amplitude_02 = np.sqrt(2) * t * r

    ideal_probabilities = np.abs([
        amplitude_20,
        amplitude_11,
        amplitude_02
    ]) ** 2

    # Completely distinguishable photons
    distinguishable_probabilities = np.array([
        0.25,
        0.50,
        0.25
    ])

    # Interpolate between the two cases
    probabilities = (
        (1 - distinguishability) * ideal_probabilities
        + distinguishability * distinguishable_probabilities
    )

    return probabilities
def hom_dip(points=100):
    """
    Generate HOM coincidence data
    for different levels of distinguishability.
    """

    distinguishabilities = np.linspace(0, 1, points)

    coincidence_probabilities = []

    for d in distinguishabilities:

        probabilities = hom_interference(d)

        coincidence_probabilities.append(
            probabilities[1]
        )

    return (
        distinguishabilities,
        np.array(coincidence_probabilities)
    )