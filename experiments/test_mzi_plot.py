import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mzi import phase_sweep
from visualization.plots import plot_mzi_interference


phases, output_0, output_1 = phase_sweep(points=200)

plot_mzi_interference(
    phases,
    output_0,
    output_1
)