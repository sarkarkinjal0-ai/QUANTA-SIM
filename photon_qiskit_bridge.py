
"""
Optional Qiskit bridge for the Photon & Noise Engine.

This file keeps Qiskit-specific code out of the optical physics engine while
allowing the engine's probabilities to be benchmarked against Aer shots.
"""
from __future__ import annotations
from typing import Dict, Optional
import numpy as np

from photon_noise_engine import PhotonNoiseEngine, NoiseConfig


def benchmark_mzi_with_qiskit(
    phase: float,
    *,
    reflectivity: float = 0.5,
    shots: int = 8192,
    noisy_optical: bool = False,
    phase_drift_std: float = 0.0,
    reflectivity_std: float = 0.0,
    seed: int = 42,
) -> Dict[str, object]:
    """
    Compare PhotonNoiseEngine optical probabilities with Qiskit Aer shots.

    The same imaginary-symmetric beam-splitter convention is used on both
    sides, so the comparison is a like-for-like physical transformation.
    """
    from qiskitintegration import (
        BeamSplitterConvention,
        DigitalQuantumEngine,
        QiskitOpticalCircuit,
        QuantumBenchmarks,
    )

    theta = float(np.arcsin(np.sqrt(np.clip(reflectivity, 0.0, 1.0))))
    engine = PhotonNoiseEngine(
        noise=NoiseConfig(
            phase_drift_std=phase_drift_std,
            reflectivity_std=reflectivity_std,
        ),
        seed=seed,
    )

    optical = engine.simulate_mzi(
        phase,
        reflectivity=reflectivity,
        phase_drift_std=phase_drift_std,
        reflectivity_std=reflectivity_std,
        noisy=noisy_optical,
    )

    qc = QiskitOpticalCircuit.build_mzi(
        phi=phase,
        input_mode=0,
        bs1_theta=theta,
        bs2_theta=theta,
        convention=BeamSplitterConvention.IMAGINARY_SYMMETRIC,
        add_measurement=True,
    )

    digital = DigitalQuantumEngine(seed=seed).run_shots(
        qc,
        num_shots=shots,
    )

    report = QuantumBenchmarks.generate_report(
        optical.probability_dict(),
        digital.mode_probabilities,
        qc,
        shots=shots,
    )

    return {
        "optical_probabilities": optical.probability_dict(),
        "qiskit_probabilities": digital.mode_probabilities,
        "counts": digital.counts,
        "tvd": report.total_variation_distance,
        "classical_fidelity": report.classical_fidelity,
        "hellinger_distance": report.hellinger_distance,
        "report": report,
        "circuit": qc,
    }
