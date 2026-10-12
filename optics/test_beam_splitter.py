import numpy as np
from optics.beam_splitter import beam_splitter


def test_50_50_beam_splitter():
    bs = beam_splitter(0.5)

    assert bs.shape == (2, 2)
    assert np.allclose(bs.conj().T @ bs, np.eye(2))


def test_70_30_beam_splitter():
    bs = beam_splitter(0.7)

    assert bs.shape == (2, 2)
    assert np.allclose(bs.conj().T @ bs, np.eye(2))


def test_invalid_transmission():
    import pytest

    with pytest.raises((ValueError, AssertionError)):
        beam_splitter(1.5)