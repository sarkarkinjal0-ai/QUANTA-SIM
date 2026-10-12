import numpy as np

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector


def simulate_qiskit_mzi(phase=0.0):
    """
    Simulate a Mach-Zehnder interferometer
    using Qiskit.

    Optical analogue:
        Beam Splitter
        -> Phase Shifter
        -> Beam Splitter
    """

    circuit = QuantumCircuit(1)

    # First beam splitter
    circuit.h(0)

    # Phase shift
    circuit.rz(phase, 0)

    # Second beam splitter
    circuit.h(0)

    # Final state
    state = Statevector.from_instruction(circuit)

    probabilities = state.probabilities()

    return state, probabilities