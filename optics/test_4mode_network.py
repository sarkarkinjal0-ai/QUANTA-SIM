import numpy as np

from mode_network import embed_two_mode_component, embed_phase_shifter
from beam_splitter import beam_splitter


# Create a 4-mode input state
state = np.array([1, 0, 0, 0], dtype=complex)


# 50:50 beam splitter between mode 0 and mode 2
bs = embed_two_mode_component(
    beam_splitter(0.5),
    modes=4,
    mode_a=0,
    mode_b=2
)


# Phase shifter on mode 2
ps = embed_phase_shifter(
    np.pi / 2,
    modes=4,
    target_mode=2
)


# Apply beam splitter first
state_after_bs = bs @ state


# Apply phase shifter
final_state = ps @ state_after_bs


# Calculate probabilities
probabilities = np.abs(final_state) ** 2


print("Initial State:")
print(state)

print("\nState after Beam Splitter:")
print(state_after_bs)

print("\nFinal State:")
print(final_state)

print("\nFinal Probabilities:")
print(probabilities)

print("\nTotal Probability:")
print(np.sum(probabilities))