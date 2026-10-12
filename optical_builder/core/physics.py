import numpy as np


def beam_splitter(theta: float) -> np.ndarray:
    """Returns 2x2 unitary matrix for a beam splitter with splitting angle theta."""
    return np.array(
        [[np.cos(theta), 1j * np.sin(theta)], [1j * np.sin(theta), np.cos(theta)]],
        dtype=complex,
    )


def phase_shifter(phi: float) -> np.ndarray:
    """Returns 2x2 unitary matrix for a phase shifter on mode 0."""
    return np.array([[np.exp(1j * phi), 0], [0, 1]], dtype=complex)


def mzi_unitary(
    phi: float, theta1: float = np.pi / 4, theta2: float = np.pi / 4
) -> np.ndarray:
    """Computes total 2x2 unitary matrix for a Mach-Zehnder Interferometer (MZI)."""
    bs1 = beam_splitter(theta1)
    ps = phase_shifter(phi)
    bs2 = beam_splitter(theta2)
    return bs2 @ ps @ bs1


def check_unitarity(matrix: np.ndarray, tol: float = 1e-6) -> bool:
    """Verifies matrix unitarity (U-dagger times U equals identity)."""
    identity = np.eye(matrix.shape[0])
    product = matrix.conj().T @ matrix
    return np.allclose(product, identity, atol=tol)