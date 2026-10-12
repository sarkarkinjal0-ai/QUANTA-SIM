import numpy as np

from mode_network import embed_phase_shifter


phase = np.pi / 2

matrix = embed_phase_shifter(
    phase,
    modes=4,
    target_mode=2
)

print("4-mode phase shifter:")
print(matrix)

print("\nMatrix shape:")
print(matrix.shape)

print("\nIs unitary?")

identity = np.eye(4)

print(
    np.allclose(
        matrix.conj().T @ matrix,
        identity
    )
)