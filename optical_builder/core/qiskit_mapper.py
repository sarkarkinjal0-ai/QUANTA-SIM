"""Map 2x2 optical unitaries (dual-rail, single photon) onto Qiskit circuits.

Encoding: photon in mode 0 -> |0>, photon in mode 1 -> |1>.
Optical matrices come from core/physics.py.
"""
import numpy as np
from qiskit import QuantumCircuit
from qiskit.synthesis import OneQubitEulerDecomposer
from qiskit_aer import AerSimulator


from core.physics import beam_splitter, phase_shifter, mzi_unitary, check_unitarity as is_unitary


# ---- exact (continuous) probabilities
def exact_probabilities(U, input_mode=0):
    """Return [P(mode0), P(mode1)] for a single photon entering input_mode."""
    amp = U[:, input_mode]
    return np.abs(amp) ** 2


# ---- circuit synthesis
def unitary_to_circuit(U, input_mode=0, decompose=True, measure=True):
    """Build a 1-qubit QuantumCircuit implementing U.

    decompose=True  -> ZYZ Euler decomposition (Rz, Ry, Rz + global phase)
    decompose=False -> a single custom unitary gate
    """
    if not is_unitary(U):
        raise ValueError("Matrix is not unitary")
    qc = QuantumCircuit(1, 1 if measure else 0)
    if input_mode == 1:
        qc.x(0)
    if decompose:
        qc.compose(OneQubitEulerDecomposer("ZYZ")(U), inplace=True)
    else:
        qc.unitary(U, [0], label="MZI")
    if measure:
        qc.measure(0, 0)
    return qc


def mzi_circuit(phi, theta1=np.pi / 4, theta2=np.pi / 4, input_mode=0, decompose=True):
    return unitary_to_circuit(mzi_unitary(phi, theta1, theta2), input_mode, decompose)


# ---- shot-based execution
def run_shots(qc, shots=1024, seed=None):
    """Run on qiskit-aer; return dict {'mode0': p0, 'mode1': p1, 'counts': counts}."""
    sim = AerSimulator(seed_simulator=seed)
    counts = sim.run(qc, shots=shots).result().get_counts()
    n0, n1 = counts.get("0", 0), counts.get("1", 0)
    return {"mode0": n0 / shots, "mode1": n1 / shots, "counts": counts}


def sweep_phase(phis, shots=1024, phase_noise_std=0.0, bs_drift_std=0.0,
                theta1=np.pi / 4, theta2=np.pi / 4, seed=None):
    """Compare exact vs shot-sampled P(mode0) across phases, with optional noise.

    phase_noise_std : std-dev of phase jitter (rad), applied per phase point
    bs_drift_std    : std-dev of beam-splitter angle drift (rad)
    Returns dict with arrays: phi, exact, ideal, sampled.
    """
    rng = np.random.default_rng(seed)
    exact, ideal, sampled = [], [], []
    for phi in phis:
        ideal.append(exact_probabilities(mzi_unitary(phi, theta1, theta2))[0])
        dphi = rng.normal(0, phase_noise_std) if phase_noise_std else 0.0
        t1 = theta1 + (rng.normal(0, bs_drift_std) if bs_drift_std else 0.0)
        t2 = theta2 + (rng.normal(0, bs_drift_std) if bs_drift_std else 0.0)
        U = mzi_unitary(phi + dphi, t1, t2)
        exact.append(exact_probabilities(U)[0])
        sampled.append(run_shots(unitary_to_circuit(U), shots)["mode0"])
    return {"phi": np.asarray(phis), "ideal": np.array(ideal),
            "exact": np.array(exact), "sampled": np.array(sampled)}


def visibility(p):
    p = np.asarray(p)
    return (p.max() - p.min()) / (p.max() + p.min())
