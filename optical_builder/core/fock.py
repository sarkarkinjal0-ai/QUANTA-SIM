import numpy as np


def hom_interference(theta: float = np.pi / 4) -> dict:
    """Outcome probabilities for |1,1> entering a beam splitter.

    At theta = pi/4 (50:50 BS), the |1,1> outcome cancels (HOM dip).
    """
    r = 1j * np.sin(theta)
    t = np.cos(theta)

    p_20 = np.abs(np.sqrt(2) * r * t) ** 2
    p_11 = np.abs(t**2 + r**2) ** 2
    p_02 = np.abs(np.sqrt(2) * r * t) ** 2

    total = p_20 + p_11 + p_02
    return {
        "|2,0>": float(p_20 / total),
        "|1,1>": float(p_11 / total),
        "|0,2>": float(p_02 / total),
    }