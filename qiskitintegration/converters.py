"""
QUANTA-SIM: Quantum Circuit Framework
Module: qiskitintegration.converters
Role: 4/5 - Qiskit Integration (Digital Quantum Side)

This module implements linear-optical to gate-based quantum computing conversions:
1. Optical component matrix representations (50:50 / variable beam splitters, phase shifters).
2. Beam splitter phase convention toggles (Real-symmetric / Hadamard, Imaginary / Dielectric, Rotation).
3. Exact single-qubit Euler Z-Y-Z matrix decomposition for arbitrary 2x2 optical unitaries into native Qiskit gates.
4. Optical mode to qubit state mapping logic (Single-qubit 2-mode, Dense log2(N), Dual-rail unary occupation).
5. Two-qubit Givens embedding for dual-rail linear optical networks.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Gate
from qiskit.circuit.library import PhaseGate, RZGate, RYGate, UnitaryGate


class BeamSplitterConvention(str, Enum):
    """
    Phase conventions for linear optical beam splitters:
    
    1. REAL_SYMMETRIC (Hadamard):
       U_BS = (1/sqrt(2)) * [[1,  1],
                             [1, -1]]
       Parameter theta:
       U_BS(theta) = [[cos(theta),  sin(theta)],
                      [sin(theta), -cos(theta)]]
       For 50:50 (theta = pi/4), this is the standard Hadamard gate H.

    2. IMAGINARY_SYMMETRIC (Dielectric plate / Quarter-wave):
       U_BS = (1/sqrt(2)) * [[1, i],
                             [i, 1]]
       Parameter theta:
       U_BS(theta) = [[cos(theta),   i*sin(theta)],
                      [i*sin(theta), cos(theta)  ]]
       Equivalently realized in Qiskit via: S @ H @ S or RX(-pi/2) * exp(i*pi/4).

    3. ROTATION (SO(2) / Continuous rotation):
       U_BS(theta) = [[cos(theta), -sin(theta)],
                      [sin(theta),  cos(theta)]]
       Realized directly in Qiskit via RY(2*theta).
    """
    REAL_SYMMETRIC = "real_symmetric"
    IMAGINARY_SYMMETRIC = "imaginary_symmetric"
    ROTATION = "rotation"


class ModeEncoding(str, Enum):
    """
    Optical-to-qubit spatial mode encoding schemes:
    
    1. SINGLE_QUBIT:
       Maps 2 optical modes directly to 1 qubit:
       Mode 0 (|1, 0> optical) -> |0> qubit
       Mode 1 (|0, 1> optical) -> |1> qubit
       
    2. DENSE:
       Maps N optical modes to ceil(log2(N)) qubits using standard binary index:
       Mode 0 -> |00...0>
       Mode 1 -> |00...1>
       Mode k -> binary(k)
       
    3. DUAL_RAIL:
       Maps N optical modes to N qubits (unary occupation basis):
       Mode 0 (|1,0,0,0>) -> |1000>
       Mode 1 (|0,1,0,0>) -> |0100>
       Mode k             -> |...1...> (k-th qubit excited)
    """
    SINGLE_QUBIT = "single_qubit"
    DENSE = "dense"
    DUAL_RAIL = "dual_rail"


def get_beam_splitter_matrix(
    theta: float = np.pi / 4,
    phi: float = 0.0,
    convention: Union[BeamSplitterConvention, str] = BeamSplitterConvention.REAL_SYMMETRIC
) -> np.ndarray:
    """
    Construct the 2x2 unitary matrix for an optical beam splitter.

    Parameters:
        theta: Mixing / splitting angle (rad). theta = pi/4 corresponds to 50:50 split.
               Transmissivity T = cos^2(theta), Reflectivity R = sin^2(theta).
        phi: Additional internal phase shift on reflection (default 0.0).
        convention: BeamSplitterConvention (REAL_SYMMETRIC, IMAGINARY_SYMMETRIC, ROTATION).

    Returns:
        np.ndarray: 2x2 complex unitary matrix.
    """
    if isinstance(convention, str):
        convention = BeamSplitterConvention(convention)

    c = np.cos(theta)
    s = np.sin(theta)

    if convention == BeamSplitterConvention.REAL_SYMMETRIC:
        # Standard symmetric real reflection matrix (Hadamard at theta=pi/4)
        matrix = np.array([
            [c, s * np.exp(1j * phi)],
            [s, -c * np.exp(1j * phi)]
        ], dtype=complex)
    elif convention == BeamSplitterConvention.IMAGINARY_SYMMETRIC:
        # Symmetric phase reflection (Quarter-wave / Dielectric interface)
        matrix = np.array([
            [c, 1j * s * np.exp(1j * phi)],
            [1j * s, c * np.exp(1j * phi)]
        ], dtype=complex)
    elif convention == BeamSplitterConvention.ROTATION:
        # Standard SO(2) rotation matrix
        matrix = np.array([
            [c, -s * np.exp(1j * phi)],
            [s,  c * np.exp(1j * phi)]
        ], dtype=complex)
    else:
        raise ValueError(f"Unsupported beam splitter convention: {convention}")

    # Check unitarity
    identity_diff = np.linalg.norm(matrix.conj().T @ matrix - np.eye(2))
    if identity_diff > 1e-10:
        raise ValueError(f"Generated beam splitter matrix is not unitary! Diff: {identity_diff}")

    return matrix


def get_phase_shifter_matrix(phi: float) -> np.ndarray:
    """
    Construct the 2x2 unitary matrix for an optical phase shifter on Mode 1.

    Parameters:
        phi: Relative optical phase shift (rad).

    Returns:
        np.ndarray: [[1, 0], [0, exp(i*phi)]]
    """
    return np.array([
        [1.0 + 0.0j, 0.0 + 0.0j],
        [0.0 + 0.0j, np.exp(1j * phi)]
    ], dtype=complex)


def decompose_unitary_zyz(U: np.ndarray) -> Tuple[float, float, float, float]:
    """
    Perform exact analytical Z-Y-Z Euler decomposition of an arbitrary 2x2 unitary matrix U.

    Any U in U(2) can be decomposed into:
        U = exp(i * alpha) * RZ(beta) * RY(gamma) * RZ(delta)
    where:
        RZ(angle) = [[exp(-i*angle/2), 0],
                     [0, exp(i*angle/2)]]
        RY(angle) = [[cos(angle/2), -sin(angle/2)],
                     [sin(angle/2),  cos(angle/2)]]
        alpha: Global phase shift (rad).
        beta, gamma, delta: Euler rotation angles (rad).

    Parameters:
        U: 2x2 complex numpy array satisfying U^dagger U = I.

    Returns:
        Tuple of (alpha, beta, gamma, delta) as floats in radians.
    """
    if U.shape != (2, 2):
        raise ValueError(f"Input matrix must be 2x2, received shape {U.shape}")

    # Verify unitarity
    if np.linalg.norm(U.conj().T @ U - np.eye(2)) > 1e-6:
        raise ValueError("Matrix is not unitary within tolerance 1e-6")

    # Step 1: Extract global phase alpha such that det(U / exp(i*alpha)) = 1 (in SU(2))
    det_u = np.linalg.det(U)
    alpha = 0.5 * float(np.angle(det_u))

    # Scale to SU(2)
    u_su2 = U * np.exp(-1j * alpha)

    # Step 2: Extract gamma from magnitude of matrix elements
    # u_su2[0, 0] = cos(gamma / 2) * exp(-i * (beta + delta) / 2)
    # u_su2[1, 0] = sin(gamma / 2) * exp(i * (beta - delta) / 2)
    cos_half_gamma = np.clip(np.abs(u_su2[0, 0]), 0.0, 1.0)
    sin_half_gamma = np.clip(np.abs(u_su2[1, 0]), 0.0, 1.0)
    gamma = 2.0 * float(np.arctan2(sin_half_gamma, cos_half_gamma))

    # Step 3: Extract beta and delta from phase angles
    tol = 1e-10
    if sin_half_gamma < tol:
        # gamma is ~ 0: diagonal matrix, beta and delta degenerate
        # u_su2[0, 0] = exp(-i * (beta + delta) / 2)
        b_plus_d = -2.0 * float(np.angle(u_su2[0, 0]))
        beta = b_plus_d
        delta = 0.0
    elif cos_half_gamma < tol:
        # gamma is ~ pi: off-diagonal matrix
        # u_su2[1, 0] = exp(i * (beta - delta) / 2)
        b_minus_d = 2.0 * float(np.angle(u_su2[1, 0]))
        beta = b_minus_d
        delta = 0.0
    else:
        # Standard non-degenerate case:
        arg_00 = float(np.angle(u_su2[0, 0]))
        arg_10 = float(np.angle(u_su2[1, 0]))
        arg_01 = float(np.angle(u_su2[0, 1]))
        arg_11 = float(np.angle(u_su2[1, 1]))

        # From SU(2) parameterization:
        # u_su2[0, 0] =  cos(gamma/2) * exp(-i * (beta + delta) / 2)
        # u_su2[1, 1] =  cos(gamma/2) * exp( i * (beta + delta) / 2)
        # u_su2[1, 0] =  sin(gamma/2) * exp( i * (beta - delta) / 2)
        # u_su2[0, 1] = -sin(gamma/2) * exp(-i * (beta - delta) / 2)

        beta_plus_delta = arg_11 - arg_00
        beta_minus_delta = 2.0 * arg_10

        beta = float(0.5 * (beta_plus_delta + beta_minus_delta))
        delta = float(0.5 * (beta_plus_delta - beta_minus_delta))

    # Validate reconstructed matrix
    if not verify_zyz_decomposition(U, alpha, beta, gamma, delta, tol=1e-6):
        # Fallback refinement if precision requires phase wrapping
        # Test alternative angle branch
        alt_beta = beta % (2 * np.pi)
        alt_delta = delta % (2 * np.pi)
        if verify_zyz_decomposition(U, alpha, alt_beta, gamma, alt_delta, tol=1e-6):
            beta, delta = alt_beta, alt_delta

    return alpha, beta, gamma, delta


def verify_zyz_decomposition(
    U: np.ndarray,
    alpha: float,
    beta: float,
    gamma: float,
    delta: float,
    tol: float = 1e-6
) -> bool:
    """
    Verify whether exp(i*alpha) * RZ(beta) * RY(gamma) * RZ(delta) reconstructs U.
    """
    rz_delta = np.array([
        [np.exp(-1j * delta / 2.0), 0.0],
        [0.0, np.exp(1j * delta / 2.0)]
    ], dtype=complex)

    ry_gamma = np.array([
        [np.cos(gamma / 2.0), -np.sin(gamma / 2.0)],
        [np.sin(gamma / 2.0),  np.cos(gamma / 2.0)]
    ], dtype=complex)

    rz_beta = np.array([
        [np.exp(-1j * beta / 2.0), 0.0],
        [0.0, np.exp(1j * beta / 2.0)]
    ], dtype=complex)

    u_recon = np.exp(1j * alpha) * (rz_beta @ ry_gamma @ rz_delta)
    diff = np.linalg.norm(U - u_recon)
    return bool(diff < tol)


def apply_zyz_to_circuit(
    circuit: QuantumCircuit,
    qubit: int,
    U: np.ndarray,
    adjust_global_phase: bool = True
) -> None:
    """
    Decompose 2x2 optical unitary U and append equivalent native RZ, RY, RZ gates to a QuantumCircuit.

    Parameters:
        circuit: Target Qiskit QuantumCircuit.
        qubit: Target qubit index.
        U: 2x2 unitary matrix.
        adjust_global_phase: If True, adds alpha to circuit.global_phase.
    """
    alpha, beta, gamma, delta = decompose_unitary_zyz(U)
    if adjust_global_phase:
        circuit.global_phase += alpha

    # Append gates in operational sequence: RZ(delta) -> RY(gamma) -> RZ(beta)
    if abs(delta) > 1e-12:
        circuit.rz(delta, qubit)
    if abs(gamma) > 1e-12:
        circuit.ry(gamma, qubit)
    if abs(beta) > 1e-12:
        circuit.rz(beta, qubit)


def embed_unitary_dense(U_opt: np.ndarray, target_num_qubits: Optional[int] = None) -> np.ndarray:
    """
    Embed an N x N optical unitary matrix into a 2^n x 2^n qubit unitary matrix (dense encoding).
    Any unused computational basis states are mapped via identity operators.

    Parameters:
        U_opt: N x N unitary matrix.
        target_num_qubits: Number of qubits n (default: ceil(log2(N))).

    Returns:
        np.ndarray: 2^n x 2^n complex unitary matrix.
    """
    N = U_opt.shape[0]
    if U_opt.shape != (N, N):
        raise ValueError(f"U_opt must be square, got {U_opt.shape}")

    min_qubits = int(np.ceil(np.log2(max(N, 2))))
    num_qubits = target_num_qubits if target_num_qubits is not None else min_qubits
    dim = 2 ** num_qubits

    if dim < N:
        raise ValueError(f"Target qubits {num_qubits} (dim {dim}) too small for optical modes {N}")

    U_qubit = np.eye(dim, dtype=complex)
    U_qubit[:N, :N] = U_opt

    # Unitarity check
    diff = np.linalg.norm(U_qubit.conj().T @ U_qubit - np.eye(dim))
    if diff > 1e-6:
        raise ValueError(f"Embedded qubit matrix is not unitary! Diff: {diff}")

    return U_qubit


def embed_givens_dual_rail(U_2x2: np.ndarray) -> np.ndarray:
    """
    Construct the 4x4 two-qubit Givens rotation unitary corresponding to a 2-mode optical beam splitter.
    
    In the dual-rail single-photon basis:
        |00>: Vacuum (0 photons) -> Invariant: |00> -> |00>
        |01>: Mode 1 single photon
        |10>: Mode 0 single photon
        |11>: Multi-photon state (unused in single-photon sector) -> Invariant: |11> -> |11>

    The optical beam splitter acts on {|10>, |01>} (Mode 0, Mode 1) as:
        [|10>]_out   [u00  u01] [|10>]_in
        [|01>]_out = [u10  u11] [|01>]_in

    Under Qiskit computational basis {|00>, |01>, |10>, |11>}:
        G = [[1,   0,   0,   0],
             [0, u11, u10,   0],
             [0, u01, u00,   0],
             [0,   0,   0,   1]]

    Parameters:
        U_2x2: 2x2 optical unitary transformation matrix.

    Returns:
        np.ndarray: 4x4 two-qubit unitary matrix.
    """
    if U_2x2.shape != (2, 2):
        raise ValueError(f"Expected 2x2 matrix, got {U_2x2.shape}")

    u00, u01 = U_2x2[0, 0], U_2x2[0, 1]
    u10, u11 = U_2x2[1, 0], U_2x2[1, 1]

    G = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, u11, u10, 0.0],
        [0.0, u01, u00, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ], dtype=complex)

    diff = np.linalg.norm(G.conj().T @ G - np.eye(4))
    if diff > 1e-6:
        raise ValueError(f"Embedded Givens matrix is not unitary: {diff}")

    return G


def optical_state_to_qubit_amplitudes(
    optical_amplitudes: np.ndarray,
    encoding: ModeEncoding = ModeEncoding.SINGLE_QUBIT
) -> np.ndarray:
    """
    Map an N-mode single-photon complex amplitude state vector to qubit state amplitudes.

    Parameters:
        optical_amplitudes: 1D array of shape (N,) representing optical mode amplitudes.
                            Sum of |a_k|^2 must be 1.0.
        encoding: ModeEncoding scheme (SINGLE_QUBIT, DENSE, DUAL_RAIL).

    Returns:
        np.ndarray: Normalized 2^n complex amplitude vector.
    """
    optical_amplitudes = np.asarray(optical_amplitudes, dtype=complex)
    N = len(optical_amplitudes)
    norm = np.linalg.norm(optical_amplitudes)
    if abs(norm - 1.0) > 1e-5:
        optical_amplitudes = optical_amplitudes / norm

    if encoding == ModeEncoding.SINGLE_QUBIT:
        if N != 2:
            raise ValueError(f"SINGLE_QUBIT encoding requires exactly 2 modes, got {N}")
        # Mode 0 -> |0>, Mode 1 -> |1>
        return optical_amplitudes.copy()

    elif encoding == ModeEncoding.DENSE:
        num_qubits = int(np.ceil(np.log2(max(N, 2))))
        dim = 2 ** num_qubits
        qubit_state = np.zeros(dim, dtype=complex)
        qubit_state[:N] = optical_amplitudes
        return qubit_state

    elif encoding == ModeEncoding.DUAL_RAIL:
        # N modes -> N qubits, with 1 photon total
        dim = 2 ** N
        qubit_state = np.zeros(dim, dtype=complex)
        for mode_idx, amp in enumerate(optical_amplitudes):
            # Mode k has 1 at bit k: 1 << mode_idx
            basis_idx = 1 << mode_idx
            qubit_state[basis_idx] = amp
        return qubit_state

    else:
        raise ValueError(f"Unknown mode encoding: {encoding}")


def qubit_counts_to_mode_probabilities(
    counts: Dict[str, int],
    total_modes: int,
    encoding: ModeEncoding = ModeEncoding.SINGLE_QUBIT
) -> Dict[int, float]:
    """
    Convert Qiskit measurement bitstring counts to optical mode probabilities.

    Parameters:
        counts: Dictionary of bitstrings and counts, e.g. {'0': 520, '1': 504}
        total_modes: Number of optical modes.
        encoding: ModeEncoding scheme used for circuit construction.

    Returns:
        Dict[int, float]: Mapping from optical mode index (0..N-1) to measured probability.
    """
    total_shots = sum(counts.values())
    if total_shots == 0:
        return {m: 0.0 for m in range(total_modes)}

    mode_probs = {m: 0.0 for m in range(total_modes)}

    for bitstring, count in counts.items():
        prob = count / total_shots
        # Clean bitstring (remove spaces if any)
        clean_bits = bitstring.replace(" ", "")

        if encoding == ModeEncoding.SINGLE_QUBIT:
            # Bit '0' -> Mode 0, Bit '1' -> Mode 1
            mode_idx = int(clean_bits[-1])
            if mode_idx < total_modes:
                mode_probs[mode_idx] += prob

        elif encoding == ModeEncoding.DENSE:
            # Binary integer value corresponds directly to mode index
            mode_idx = int(clean_bits, 2)
            if mode_idx < total_modes:
                mode_probs[mode_idx] += prob

        elif encoding == ModeEncoding.DUAL_RAIL:
            # Qiskit bitstring order is q_{n-1}...q_0
            # A valid single-photon detection has exactly one '1'
            if clean_bits.count("1") == 1:
                # Find position of '1' counting from right (q_0 = mode 0)
                reversed_bits = clean_bits[::-1]
                mode_idx = reversed_bits.index("1")
                if mode_idx < total_modes:
                    mode_probs[mode_idx] += prob

    return mode_probs
