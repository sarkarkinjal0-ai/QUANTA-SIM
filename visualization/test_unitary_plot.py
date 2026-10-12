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
from visualization.plots import plot_unitary_magnitude


matrix = beam_splitter(0.5)

print("Beam Splitter Unitary:")
print(matrix)

plot_unitary_magnitude(matrix)