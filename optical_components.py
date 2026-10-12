import numpy as np
from photon_noise_engine import PhotonNoiseEngine

class ComponentLibrary:
    """
    QUANTA-SIM optical component facade.
    Deterministic matrices remain compatible with the original team API;
    stochastic versions are exposed by PhotonNoiseEngine.
    """
    @staticmethod
    def beam_splitter(reflectivity=0.5):
        r_amp = np.sqrt(reflectivity)
        t_amp = np.sqrt(1.0 - reflectivity)
        return np.array([[t_amp, 1j * r_amp],
                         [1j * r_amp, t_amp]], dtype=complex)

    @staticmethod
    def beam_splitter_5050():
        return ComponentLibrary.beam_splitter(reflectivity=0.5)

    @staticmethod
    def phase_shifter(phi, phase_drift_std=0.0):
        actual_phi = np.random.normal(loc=phi, scale=phase_drift_std) if phase_drift_std else phi
        return np.array([[np.exp(1j * actual_phi), 0],
                         [0, 1]], dtype=complex)

    @staticmethod
    def noisy_beam_splitter(reflectivity=0.5, reflectivity_std=0.0, seed=None):
        engine = PhotonNoiseEngine(noise=None, seed=seed)
        return engine.noisy_beam_splitter(reflectivity, reflectivity_std)

    @staticmethod
    def noisy_phase_shifter(phi, phase_drift_std=0.0, seed=None):
        engine = PhotonNoiseEngine(noise=None, seed=seed)
        return engine.noisy_phase_shifter(phi, phase_drift_std)
