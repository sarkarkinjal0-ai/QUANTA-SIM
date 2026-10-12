import numpy as np

from state import basis_state
from unitary import apply_unitary, is_unitary


# 50:50 beam splitter
beam_splitter = (1 / np.sqrt(2)) * np.array([
    [1, 1],
    [1, -1]
], dtype=complex)


state = basis_state(0, 2)

new_state = apply_unitary(state, beam_splitter)

print("Beam splitter matrix:")
print(beam_splitter)

print("\nIs unitary?")
print(is_unitary(beam_splitter))

print("\nInput state:")
print(state)

print("\nOutput state:")
print(new_state)