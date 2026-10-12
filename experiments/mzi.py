import numpy as np

from optics.beam_splitter import beam_splitter
from optics.phase_shifter import phase_shifter
from optics.circuit import OpticalCircuit


def create_mzi(phase=0.0):
    """
    Create a Mach-Zehnder interferometer.

    The MZI consists of:
    1. First 50:50 beam splitter
    2. Phase shifter
    3. Second 50:50 beam splitter
    """

    circuit = OpticalCircuit(modes=2)

    bs1 = beam_splitter(0.5)
    ps = phase_shifter(phase)
    bs2 = beam_splitter(0.5)

    circuit.add_component("First 50:50 Beam Splitter", bs1)
    circuit.add_component("Phase Shifter", ps)
    circuit.add_component("Second 50:50 Beam Splitter", bs2)

    return circuit


def simulate_mzi(phase=0.0):
    """
    Send a photon through the Mach-Zehnder interferometer.
    """

    circuit = create_mzi(phase)

    input_state = np.array([1, 0], dtype=complex)

    output_state = circuit.run(input_state)

    probabilities = np.abs(output_state) ** 2

    return output_state, probabilities
def phase_sweep(start=0.0, stop=2 * np.pi, points=100):
    """
    Calculate MZI output probabilities for a range of phase values.
    """

    phases = np.linspace(start, stop, points)

    output_0 = []
    output_1 = []

    for phase in phases:
        _, probabilities = simulate_mzi(phase)

        output_0.append(probabilities[0])
        output_1.append(probabilities[1])

    return phases, np.array(output_0), np.array(output_1)