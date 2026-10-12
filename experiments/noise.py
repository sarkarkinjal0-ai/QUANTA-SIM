import numpy as np

from experiments.mzi import simulate_mzi


def add_phase_noise(phase, noise_strength=0.1):
    """
    Add random phase noise to an optical phase.
    """

    if noise_strength < 0:
        raise ValueError(
            "Noise strength cannot be negative."
        )

    noise = np.random.uniform(
        -noise_strength,
        noise_strength
    )

    return phase + noise


def simulate_noisy_mzi(
    phase=0.0,
    noise_strength=0.1
):
    """
    Simulate an MZI with phase noise.
    """

    noisy_phase = add_phase_noise(
        phase,
        noise_strength
    )

    output_state, probabilities = simulate_mzi(
        noisy_phase
    )

    return (
        noisy_phase,
        output_state,
        probabilities
    )
def add_beam_splitter_error(
    transmission,
    error_strength=0.05
):
    """
    Add a random transmission error
    to a beam splitter.
    """

    if transmission < 0 or transmission > 1:
        raise ValueError(
            "Transmission must be between 0 and 1."
        )

    if error_strength < 0:
        raise ValueError(
            "Error strength cannot be negative."
        )

    error = np.random.uniform(
        -error_strength,
        error_strength
    )

    actual_transmission = transmission + error

    actual_transmission = np.clip(
        actual_transmission,
        0.0,
        1.0
    )

    return actual_transmission