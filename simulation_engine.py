"""Compatibility layer for the original simulation_engine API."""
from core_engine import QuantumState, CorePhysicsEngine
from photon_noise_engine import PhotonNoiseEngine

class SinglePhotonPipeline:
    """Legacy 2-mode pipeline backed by the Core Physics engine."""
    def __init__(self, initial_state):
        self.initial_state = QuantumState(initial_state)
        self.components = []
        self.total_unitary = None
        self.final_state = None

    def add_component(self, unitary_matrix):
        self.components.append(unitary_matrix)

    def cascade(self):
        if not self.components:
            raise ValueError("No components added to the circuit.")
        engine = CorePhysicsEngine(len(self.initial_state.amplitudes))
        self.total_unitary = engine.compute_total_unitary(self.components)
        return self.total_unitary

    def compute_state(self):
        engine = CorePhysicsEngine(len(self.initial_state.amplitudes))
        if self.total_unitary is None:
            self.cascade()
        self.final_state = engine.evolve_state(self.initial_state, self.components).amplitudes
        return self.final_state

    def extract_probabilities(self):
        if self.final_state is None:
            self.compute_state()
        return np.abs(self.final_state) ** 2

class MultiModeLogic:
    @staticmethod
    def expand_with_tensor_product(local_unitary, system_index, total_systems=2):
        identity = np.eye(2, dtype=complex)
        pieces = [local_unitary if i == system_index else identity for i in range(total_systems)]
        result = pieces[0]
        for piece in pieces[1:]:
            result = np.kron(result, piece)
        return result

    @staticmethod
    def validate_unitarity(matrix, tolerance=1e-10):
        matrix = np.asarray(matrix)
        if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
            raise ValueError("Matrix must be square")
        ok = np.allclose(matrix.conj().T @ matrix, np.eye(matrix.shape[0]), atol=tolerance)
        if not ok:
            raise ValueError("Matrix is not unitary!")
        return True

class TwoPhotonInterference:
    """Compatibility facade now delegated to the Photon & Noise Engine."""
    calculate_hom_amplitudes = staticmethod(PhotonNoiseEngine.calculate_hom_amplitudes)

# numpy is intentionally imported after the classes for compatibility.
import numpy as np
