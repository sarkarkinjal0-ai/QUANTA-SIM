import numpy as np


def embed_two_mode_component(component, modes, mode_a, mode_b):
    """
    Embed a 2x2 optical component into a larger
    multi-mode system.

    Example:
        modes = 4
        mode_a = 0
        mode_b = 2

    applies the 2x2 component between modes 0 and 2.
    """

    component = np.asarray(component, dtype=complex)

    if component.shape != (2, 2):
        raise ValueError("Component must be a 2x2 matrix.")

    if modes < 2:
        raise ValueError("At least 2 modes are required.")

    if mode_a < 0 or mode_a >= modes:
        raise ValueError("Invalid first mode.")

    if mode_b < 0 or mode_b >= modes:
        raise ValueError("Invalid second mode.")

    if mode_a == mode_b:
        raise ValueError("The two modes must be different.")

    result = np.eye(modes, dtype=complex)

    result[mode_a, mode_a] = component[0, 0]
    result[mode_a, mode_b] = component[0, 1]
    result[mode_b, mode_a] = component[1, 0]
    result[mode_b, mode_b] = component[1, 1]

    return result
def embed_phase_shifter(phase, modes, target_mode):
    """
    Create a phase shifter acting on one mode
    inside a multi-mode optical system.
    """

    if modes < 2:
        raise ValueError("At least 2 modes are required.")

    if target_mode < 0 or target_mode >= modes:
        raise ValueError("Invalid target mode.")

    result = np.eye(modes, dtype=complex)

    result[target_mode, target_mode] = np.exp(1j * phase)

    return result