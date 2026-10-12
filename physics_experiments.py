import numpy as np
from photon_noise_engine import PhotonNoiseEngine, NoiseConfig

class InterferometryExperiments:
    """
    Interferometry & Experiments role.
    Experiment orchestration consumes the Photon & Noise Engine; it does not
    implement stochastic photon physics itself.
    """
    @staticmethod
    def run_mzi_sweep(
        imperfect_reflectivity=0.45,
        noise_std=0.3,
        reflectivity_std=0.0,
        shots=None,
        seed=42,
    ):
        engine = PhotonNoiseEngine(
            noise=NoiseConfig(
                phase_drift_std=noise_std,
                reflectivity_std=reflectivity_std,
                shots=shots,
            ),
            seed=seed,
        )
        return engine.mzi_sweep(
            reflectivity=imperfect_reflectivity,
            phase_drift_std=noise_std,
            reflectivity_std=reflectivity_std,
            noisy=True,
            shots=shots,
        )

    @staticmethod
    def run_hom_analysis(
        imperfect_reflectivity=0.45,
        reflectivity_std=0.0,
        shots=None,
        seed=42,
    ):
        engine = PhotonNoiseEngine(
            noise=NoiseConfig(reflectivity_std=reflectivity_std, shots=shots),
            seed=seed,
        )
        ideal = engine.simulate_hom(reflectivity=0.5, noisy=False, shots=shots)
        imperfect = engine.simulate_hom(
            reflectivity=imperfect_reflectivity,
            reflectivity_std=reflectivity_std,
            noisy=reflectivity_std > 0,
            shots=shots,
        )
        return {
            "ideal_coincidence": ideal["probabilities"]["|1,1>"],
            "imperfect_coincidence": imperfect["probabilities"]["|1,1>"],
            "ideal_probabilities": ideal["probabilities"],
            "imperfect_probabilities": imperfect["probabilities"],
            "imperfect_reflectivity": imperfect["reflectivity"],
            "sampled_counts": imperfect["sampled_counts"],
        }

    @staticmethod
    def run_advanced_mzi(
        phase=0.0,
        reflectivity=0.5,
        phase_drift_std=0.0,
        reflectivity_std=0.0,
        seed=42,
    ):
        engine = PhotonNoiseEngine(
            noise=NoiseConfig(
                phase_drift_std=phase_drift_std,
                reflectivity_std=reflectivity_std,
            ),
            seed=seed,
        )
        return engine.simulate_mzi(
            phase,
            reflectivity=reflectivity,
            phase_drift_std=phase_drift_std,
            reflectivity_std=reflectivity_std,
            noisy=(phase_drift_std > 0 or reflectivity_std > 0),
        )
