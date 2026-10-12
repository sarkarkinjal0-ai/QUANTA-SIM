import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from optics.beam_splitter import beam_splitter
from optics.mode_network import embed_two_mode_component
from visualization.plots import plot_unitary_magnitude


bs = beam_splitter(0.5)

matrix = embed_two_mode_component(
    bs,
    modes=4,
    mode_a=0,
    mode_b=2
)

print("4-mode Unitary:")
print(matrix)

plot_unitary_magnitude(matrix)