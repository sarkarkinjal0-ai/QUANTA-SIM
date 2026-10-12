"""Integrated Optical Builder.

The builder remains responsible for constructing circuits. Simulation is
delegated to the shared Photon & Noise Engine so there is one source of truth
for photon evolution and stochastic noise.
"""
from dataclasses import dataclass
from itertools import combinations_with_replacement
import numpy as np

from core_engine import CorePhysicsEngine
from photon_noise_engine import PhotonNoiseEngine

@dataclass
class Component:
    kind: str
    modes: tuple
    param: float

    def label(self):
        if self.kind == "BS":
            return f"BS(modes {self.modes[0]},{self.modes[1]}; theta={self.param:.2f})"
        return f"PS(mode {self.modes[0]}; phi={self.param:.2f})"

class OpticalCircuit:
    def __init__(self, n_modes=2):
        if not 2 <= n_modes <= 4:
            raise ValueError("n_modes must be between 2 and 4")
        self.n_modes=n_modes
        self.components=[]

    def add_beam_splitter(self, mode_a, mode_b, theta=np.pi/4):
        if mode_a == mode_b or not (0 <= mode_a < self.n_modes and 0 <= mode_b < self.n_modes):
            raise ValueError("Beam splitter requires two distinct valid modes")
        if not 0 <= theta <= np.pi/2:
            raise ValueError("theta must lie in [0, pi/2]")
        self.components.append(Component("BS",(mode_a,mode_b),float(theta)))
        return self

    def add_phase_shifter(self, mode, phi):
        if not 0 <= mode < self.n_modes:
            raise ValueError("mode out of range")
        self.components.append(Component("PS",(mode,),float(phi)))
        return self

    def remove_last(self):
        if self.components: self.components.pop()

    def clear(self): self.components.clear()

    def component_unitary(self, comp):
        core=CorePhysicsEngine(self.n_modes)
        if comp.kind=="BS":
            return core.embed_operator(core.create_beam_splitter(np.sin(comp.param)**2), list(comp.modes))
        local=np.array([[np.exp(1j*comp.param)]],dtype=complex)
        return core.embed_operator(local,[comp.modes[0]])

    def total_unitary(self):
        core=CorePhysicsEngine(self.n_modes)
        return core.compute_total_unitary([self.component_unitary(c) for c in self.components])

    def is_unitary(self):
        U=self.total_unitary()
        return np.allclose(U.conj().T@U,np.eye(self.n_modes),atol=1e-8)

    def depth_summary(self):
        return {
            "components":len(self.components),
            "beam_splitters":sum(c.kind=="BS" for c in self.components),
            "phase_shifters":sum(c.kind=="PS" for c in self.components),
        }

    def full_component_unitaries(self):
        return [self.component_unitary(c) for c in self.components]

    # ---- Shared Photon & Noise Engine interface
    def simulate_single_photon(self, input_mode=0, *, phase_noise_std=0.0,
                               reflectivity_noise_std=0.0, noisy=False, seed=42,
                               shots=None):
        engine=PhotonNoiseEngine(self.n_modes, seed=seed)
        return engine.simulate_circuit(
            input_mode=input_mode,
            components=self.components,
            noisy=noisy,
            phase_noise_std=phase_noise_std,
            reflectivity_noise_std=reflectivity_noise_std,
            shots=shots,
        )

    def single_photon_probabilities(self, input_mode=0):
        return self.simulate_single_photon(input_mode=input_mode).probabilities

    def simulate_two_photon(self, in_a=0, in_b=1, *, shots=None, seed=42):
        engine=PhotonNoiseEngine(self.n_modes, seed=seed)
        return engine.simulate_two_photon_circuit(in_a,in_b,self.components,shots=shots)

    def two_photon_probabilities(self, in_a=0, in_b=1):
        return self.simulate_two_photon(in_a,in_b)["probabilities"]

def pattern_label(pattern):
    return "|" + ",".join(str(n) for n in pattern) + ">"

def mzi_circuit(phi, theta1=np.pi/4, theta2=np.pi/4):
    return (OpticalCircuit(2)
        .add_beam_splitter(0,1,theta1)
        .add_phase_shifter(0,phi)
        .add_beam_splitter(0,1,theta2))
