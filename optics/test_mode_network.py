import numpy as np

from beam_splitter import beam_splitter
from mode_network import embed_two_mode_component


bs = beam_splitter(0.5)

four_mode_bs = embed_two_mode_component(
    bs,
    modes=4,
    mode_a=0,
    mode_b=2
)

print("4-mode beam splitter:")
print(four_mode_bs)

print("\nMatrix shape:")
print(four_mode_bs.shape)

print("\nIs unitary?")

identity = np.eye(4)

print(
    np.allclose(
        four_mode_bs.conj().T @ four_mode_bs,
        identity
    )
)