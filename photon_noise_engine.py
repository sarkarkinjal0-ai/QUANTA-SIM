"""
QUANTA-SIM — Photon & Noise Engine
Role: Photon & Noise Engine - Advanced Simulation

This module is the stochastic/non-ideal simulation layer between the
deterministic Core Physics engine and downstream interferometry/Qiskit code.

Responsibilities:
- Single-photon evolution with optional phase and beam-splitter noise.
- Two-photon Fock-space/Hong-Ou-Mandel amplitudes.
- Parameterized optical imperfections.
- Finite-shot sampling from theoretical probability distributions.
- Reproducible Monte-Carlo realizations via NumPy Generator.

The engine deliberately accepts/returns NumPy arrays and dictionaries so it
can be consumed by both the physics-experiment and Qiskit integration roles.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import numpy as np

from core_engine import CorePhysicsEngine, QuantumState


@dataclass
class NoiseConfig:
    """Controls stochastic optical imperfections.

    phase_drift_std:
        Standard deviation of Gaussian phase drift, in radians.
    reflectivity_std:
        Standard deviation of Gaussian beam-splitter reflectivity error.
    shots:
        Optional number of finite measurement shots.
    """
    phase_drift_std: float = 0.0
    reflectivity_std: float = 0.0
    shots: Optional[int] = None

    def validate(self) -> None:
        if self.phase_drift_std < 0:
            raise ValueError("phase_drift_std must be >= 0")
        if self.reflectivity_std < 0:
            raise ValueError("reflectivity_std must be >= 0")
        if self.shots is not None and self.shots <= 0:
            raise ValueError("shots must be a positive integer")


@dataclass
class PhotonSimulationResult:
    """Structured result shared by experiments/UI and Qiskit benchmarking."""
    state: np.ndarray
    probabilities: np.ndarray
    noisy: bool
    metadata: Dict[str, float]

    def probability_dict(self) -> Dict[int, float]:
        return {i: float(p) for i, p in enumerate(self.probabilities)}


class PhotonNoiseEngine:
    """
    Advanced photon/noise simulation engine.

    The deterministic matrix evolution is delegated to CorePhysicsEngine.
    This class owns the stochastic realization and multi-photon layer.
    """

    def __init__(
        self,
        num_modes: int = 2,
        noise: Optional[NoiseConfig] = None,
        seed: Optional[int] = 42,
    ):
        self.core = CorePhysicsEngine(num_modes=num_modes)
        self.noise = noise or NoiseConfig()
        self.noise.validate()
        self.rng = np.random.default_rng(seed)
        self.seed = seed

    # ---------------------------- Noise primitives ----------------------------

    def sample_phase(self, phase: float, std: Optional[float] = None) -> float:
        """Return phase + Gaussian environmental drift."""
        sigma = self.noise.phase_drift_std if std is None else float(std)
        if sigma < 0:
            raise ValueError("phase noise standard deviation must be >= 0")
        return float(phase + self.rng.normal(0.0, sigma)) if sigma else float(phase)

    def sample_reflectivity(
        self, reflectivity: float, std: Optional[float] = None
    ) -> float:
        """Return a physically bounded noisy beam-splitter reflectivity."""
        r = float(reflectivity)
        if not 0.0 <= r <= 1.0:
            raise ValueError("reflectivity must lie in [0, 1]")
        sigma = self.noise.reflectivity_std if std is None else float(std)
        if sigma < 0:
            raise ValueError("reflectivity noise standard deviation must be >= 0")
        if sigma:
            r += float(self.rng.normal(0.0, sigma))
        return float(np.clip(r, 0.0, 1.0))

    def noisy_beam_splitter(
        self, reflectivity: float = 0.5, std: Optional[float] = None
    ) -> np.ndarray:
        return self.core.create_beam_splitter(
            self.sample_reflectivity(reflectivity, std)
        )

    def noisy_phase_shifter(
        self, phase: float, std: Optional[float] = None
    ) -> np.ndarray:
        actual = self.sample_phase(phase, std)
        # 2-mode relative phase operator; unlike the core 1x1 helper this is
        # directly usable in a 2-mode optical circuit.
        return np.array(
            [[1.0 + 0j, 0.0 + 0j],
             [0.0 + 0j, np.exp(1j * actual)]],
            dtype=complex,
        )

    # ---------------------------- Single photon ----------------------------

    def simulate_single_photon(
        self,
        initial_state: Sequence[complex],
        components: Sequence[np.ndarray],
        *,
        noisy: bool = False,
    ) -> PhotonSimulationResult:
        """
        Evolve a single photon through a supplied sequence of full-space
        unitaries. Noise is expected to have been injected while constructing
        the component matrices, keeping this method deterministic.
        """
        state = QuantumState(initial_state)
        unitaries = [np.asarray(u, dtype=complex) for u in components]
        for u in unitaries:
            if u.shape != (self.core.num_modes, self.core.num_modes):
                raise ValueError(
                    f"Each unitary must be {self.core.num_modes}x{self.core.num_modes}; got {u.shape}"
                )
            CorePhysicsEngine(num_modes=self.core.num_modes).validate_unitary(u) if hasattr(
                CorePhysicsEngine, "validate_unitary"
            ) else None
        final = self.core.evolve_state(state, unitaries)
        return PhotonSimulationResult(
            state=final.amplitudes.copy(),
            probabilities=final.get_probabilities(),
            noisy=noisy,
            metadata={"num_modes": float(self.core.num_modes)},
        )

    def simulate_mzi(
        self,
        phase: float,
        *,
        reflectivity: float = 0.5,
        phase_drift_std: Optional[float] = None,
        reflectivity_std: Optional[float] = None,
        noisy: bool = False,
    ) -> PhotonSimulationResult:
        """Run a two-mode MZI for one phase value."""
        if noisy:
            r1 = self.sample_reflectivity(reflectivity, reflectivity_std)
            r2 = self.sample_reflectivity(reflectivity, reflectivity_std)
            phi = self.sample_phase(phase, phase_drift_std)
        else:
            r1 = r2 = float(reflectivity)
            phi = float(phase)

        bs1 = self.core.create_beam_splitter(r1)
        bs2 = self.core.create_beam_splitter(r2)
        ps = self.noisy_phase_shifter(phi, std=0.0)

        return self.simulate_single_photon(
            [1.0, 0.0], [bs1, ps, bs2], noisy=noisy
        )

    def mzi_sweep(
        self,
        phases: Optional[Sequence[float]] = None,
        *,
        reflectivity: float = 0.5,
        phase_drift_std: Optional[float] = None,
        reflectivity_std: Optional[float] = None,
        noisy: bool = True,
        shots: Optional[int] = None,
    ) -> Dict[str, np.ndarray]:
        """Generate ideal/noisy MZI curves and optional finite-shot samples."""
        phase_values = (
            np.linspace(0.0, 2.0 * np.pi, 100)
            if phases is None
            else np.asarray(phases, dtype=float)
        )
        ideal = np.array(
            [self.simulate_mzi(p, reflectivity=reflectivity, noisy=False).probabilities
             for p in phase_values]
        )
        noisy_values = np.array(
            [self.simulate_mzi(
                p,
                reflectivity=reflectivity,
                phase_drift_std=phase_drift_std,
                reflectivity_std=reflectivity_std,
                noisy=noisy,
            ).probabilities for p in phase_values]
        )
        result = {
            "phi_values": phase_values,
            "p0_ideal": ideal[:, 0],
            "p1_ideal": ideal[:, 1],
            "p0_noisy": noisy_values[:, 0],
            "p1_noisy": noisy_values[:, 1],
        }
        if shots:
            result["p0_sampled"], result["p1_sampled"] = self.sample_binary_curve(
                noisy_values[:, 0], shots
            )
        return result

    # ---------------------------- Two photons / HOM ----------------------------

    @staticmethod
    def calculate_hom_amplitudes(unitary: np.ndarray) -> Dict[str, complex]:
        """
        Exact two-photon Fock amplitudes for input |1,1> through a 2x2 unitary:
          |2,0>: sqrt(2) a b
          |1,1>: a d + b c
          |0,2>: sqrt(2) c d
        """
        U = np.asarray(unitary, dtype=complex)
        if U.shape != (2, 2):
            raise ValueError("HOM calculation requires a 2x2 unitary")
        a, b = U[0, 0], U[0, 1]
        c, d = U[1, 0], U[1, 1]
        return {
            "|2,0>": np.sqrt(2.0) * a * b,
            "|1,1>": a * d + b * c,
            "|0,2>": np.sqrt(2.0) * c * d,
        }

    @classmethod
    def hom_probabilities(cls, unitary: np.ndarray) -> Dict[str, float]:
        amps = cls.calculate_hom_amplitudes(unitary)
        probs = {k: float(abs(v) ** 2) for k, v in amps.items()}
        total = sum(probs.values())
        if total > 0:
            probs = {k: v / total for k, v in probs.items()}
        return probs

    def simulate_hom(
        self,
        *,
        reflectivity: float = 0.5,
        reflectivity_std: Optional[float] = None,
        noisy: bool = False,
        shots: Optional[int] = None,
    ) -> Dict[str, object]:
        """Simulate the two-photon |1,1> HOM experiment."""
        r = (
            self.sample_reflectivity(reflectivity, reflectivity_std)
            if noisy else float(reflectivity)
        )
        U = self.core.create_beam_splitter(r)
        probabilities = self.hom_probabilities(U)
        sampled = self.sample_distribution(
            list(probabilities.keys()), list(probabilities.values()), shots
        ) if shots else None
        return {
            "unitary": U,
            "reflectivity": r,
            "amplitudes": self.calculate_hom_amplitudes(U),
            "probabilities": probabilities,
            "sampled_counts": sampled,
            "noisy": noisy,
        }

    # ---------------------------- Finite sampling ----------------------------

    def sample_distribution(
        self,
        outcomes: Sequence[str],
        probabilities: Sequence[float],
        shots: int,
    ) -> Dict[str, int]:
        """Sample detector counts with multinomial finite-shot noise."""
        if shots <= 0:
            raise ValueError("shots must be positive")
        p = np.asarray(probabilities, dtype=float)
        p = np.clip(p, 0.0, None)
        if p.sum() <= 0:
            raise ValueError("probabilities must have positive sum")
        p /= p.sum()
        counts = self.rng.multinomial(int(shots), p)
        return {str(k): int(v) for k, v in zip(outcomes, counts)}

    def sample_binary_curve(
        self, p0_values: Sequence[float], shots: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Finite-shot sample of a binary detector curve."""
        p0 = np.clip(np.asarray(p0_values, dtype=float), 0.0, 1.0)
        counts0 = self.rng.binomial(int(shots), p0)
        p0_sampled = counts0 / float(shots)
        return p0_sampled, 1.0 - p0_sampled

    def noise_summary(self) -> Dict[str, object]:
        return {"seed": self.seed, **asdict(self.noise)}


    # ---------------------------- Optical Builder integration ----------------------------

    def _component_unitary_with_noise(self, component, phase_noise_std=0.0,
                                      reflectivity_noise_std=0.0, noisy=False):
        """Convert an Optical Builder component into a full-space noisy unitary."""
        kind = component.kind
        if kind == "BS":
            theta = float(component.param)
            r = float(np.sin(theta) ** 2)
            if noisy:
                r = self.sample_reflectivity(r, reflectivity_noise_std)
            return self.core.embed_operator(
                self.core.create_beam_splitter(r), list(component.modes)
            )
        if kind == "PS":
            phi = float(component.param)
            if noisy:
                phi = self.sample_phase(phi, phase_noise_std)
            local = np.array([[np.exp(1j * phi)]], dtype=complex)
            return self.core.embed_operator(local, [component.modes[0]])
        raise ValueError(f"Unsupported optical component kind: {kind}")

    def simulate_circuit(self, *, input_mode=0, components=(), noisy=False,
                         phase_noise_std=0.0, reflectivity_noise_std=0.0,
                         shots=None):
        """Run a circuit created by OpticalCircuit through the shared photon engine."""
        if not 0 <= input_mode < self.core.num_modes:
            raise ValueError("input_mode out of range")
        if not components:
            components = []
        unitaries = [
            self._component_unitary_with_noise(
                c, phase_noise_std, reflectivity_noise_std, noisy
            )
            for c in components
        ]
        if not unitaries:
            U = self.core.get_identity()
            state = np.eye(self.core.num_modes, dtype=complex)[:, input_mode]
        else:
            U = self.core.compute_total_unitary(unitaries)
            state = U[:, input_mode]
        probabilities = np.abs(state) ** 2
        sampled_counts = None
        if shots is not None:
            labels = [f"Mode {i}" for i in range(self.core.num_modes)]
            sampled_counts = self.sample_distribution(labels, probabilities, shots)
        return {
            "unitary": U,
            "state": state,
            "probabilities": probabilities,
            "sampled_counts": sampled_counts,
            "noisy": noisy,
        }

    @staticmethod
    def _two_photon_output_probabilities(U, in_a=0, in_b=1):
        """General N-mode two-photon probabilities via 2x2 permanents."""
        U=np.asarray(U,dtype=complex)
        n=U.shape[0]
        if U.ndim != 2 or U.shape[1] != n:
            raise ValueError("U must be square")
        if not (0 <= in_a < n and 0 <= in_b < n):
            raise ValueError("input mode out of range")
        out={}
        for i,j in __import__('itertools').combinations_with_replacement(range(n),2):
            perm=U[i,in_a]*U[j,in_b] + U[i,in_b]*U[j,in_a]
            norm=(2 if i==j else 1)*(2 if in_a==in_b else 1)
            pattern=[0]*n; pattern[i]+=1; pattern[j]+=1
            out[tuple(pattern)] = float(abs(perm)**2/norm)
        total=sum(out.values())
        if total>0:
            out={k:v/total for k,v in out.items()}
        return out

    def simulate_two_photon_circuit(self, in_a, in_b, components, *, shots=None):
        unitaries=[self._component_unitary_with_noise(c) for c in components]
        U=self.core.compute_total_unitary(unitaries) if unitaries else self.core.get_identity()
        probs=self._two_photon_output_probabilities(U,in_a,in_b)
        sampled=self.sample_distribution(
            [str(k) for k in probs], list(probs.values()), shots
        ) if shots else None
        return {"unitary":U,"probabilities":probs,"sampled_counts":sampled}


# Backwards-compatible aliases for team code.
AdvancedPhotonEngine = PhotonNoiseEngine
TwoPhotonFockEngine = PhotonNoiseEngine
