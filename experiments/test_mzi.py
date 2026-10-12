import numpy as np
from experiments.mzi import simulate_mzi


def test_mzi_probabilities_sum_to_one():
    output_state, probabilities = simulate_mzi(0.0)

    assert np.isclose(np.sum(probabilities), 1.0)


def test_mzi_output_at_zero_phase():
    output_state, probabilities = simulate_mzi(0.0)

    assert np.allclose(probabilities, [1.0, 0.0])


def test_mzi_probabilities_are_valid():
    output_state, probabilities = simulate_mzi(np.pi / 2)

    assert np.all(probabilities >= 0)
    assert np.all(probabilities <= 1)