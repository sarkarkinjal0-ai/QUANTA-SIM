"""
QUANTA-SIM integrated demonstration.

The optical path is:
Core Physics -> Photon & Noise Engine -> Interferometry -> Qiskit benchmark.

Qiskit is optional for the first two demonstrations. If qiskit/qiskit-aer are
installed, the digital benchmark is also executed.
"""
import numpy as np
from photon_noise_engine import PhotonNoiseEngine, NoiseConfig
from physics_experiments import InterferometryExperiments

def main():
    print("\n=== QUANTA-SIM: Photon & Noise Engine ===")
    engine = PhotonNoiseEngine(
        noise=NoiseConfig(phase_drift_std=0.08, reflectivity_std=0.01),
        seed=42,
    )

    mzi = engine.simulate_mzi(
        np.pi / 3,
        reflectivity=0.5,
        noisy=True,
    )
    print("Noisy MZI probabilities:", np.round(mzi.probabilities, 6))
    print("Noisy MZI probability sum:", np.sum(mzi.probabilities))

    hom = engine.simulate_hom(
        reflectivity=0.5,
        noisy=False,
        shots=8192,
    )
    print("HOM probabilities:", {k: round(v, 6) for k, v in hom["probabilities"].items()})
    print("HOM sampled counts:", hom["sampled_counts"])

    exp = InterferometryExperiments.run_mzi_sweep(
        imperfect_reflectivity=0.45,
        noise_std=0.08,
        shots=8192,
    )
    print("MZI sweep points:", len(exp["phi_values"]))
    print("MZI noisy P0 range:", float(np.min(exp["p0_noisy"])), float(np.max(exp["p0_noisy"])))

    try:
        from qiskitintegration import (
            QiskitOpticalCircuit, DigitalQuantumEngine, QuantumBenchmarks
        )
        from photon_qiskit_bridge import benchmark_mzi_with_qiskit
        result = benchmark_mzi_with_qiskit(
            phase=np.pi / 3,
            reflectivity=0.5,
            shots=8192,
            noisy_optical=False,
            seed=42,
        )
        print(f"Qiskit TVD: {result['tvd']:.5f}")
        print(f"Qiskit Fidelity: {result['classical_fidelity']:.5f}")
        print(f"Hellinger: {result['hellinger_distance']:.5f}")
    except ImportError as exc:
        print("Qiskit benchmark skipped:", exc)

if __name__ == "__main__":
    main()
