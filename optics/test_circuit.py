import numpy as np

from circuit import OpticalCircuit
from beam_splitter import beam_splitter
from phase_shifter import phase_shifter


circuit = OpticalCircuit(modes=2)

bs = beam_splitter(0.5)
ps = phase_shifter(np.pi / 2)

circuit.add_component("50:50 Beam Splitter", bs)
circuit.add_component("Phase Shifter", ps)

circuit.show_components()

print("\nOverall Unitary:")
print(circuit.overall_unitary())


# Input photon in mode 0
input_state = np.array([1, 0], dtype=complex)

output_state = circuit.run(input_state)

print("\nInput State:")
print(input_state)

print("\nOutput State:")
print(output_state)

print("\nOutput Probabilities:")
print(np.abs(output_state) ** 2)