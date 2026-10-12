import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

import numpy as np

from experiments.mzi import phase_sweep
from qiskit_mzi import simulate_qiskit_mzi
from visualization.plots import plot_mzi_comparison


# Generate phase values
phases = np.linspace(
    0,
    2 * np.pi,
    100
)


# QUANTA-SIM optical MZI
_, optical_0, _ = phase_sweep(
    points=100
)


# Qiskit MZI
qiskit_0 = []

for phase in phases:

    _, probabilities = simulate_qiskit_mzi(
        phase
    )

    qiskit_0.append(
        probabilities[0]
    )

qiskit_0 = np.array(qiskit_0)


# Plot comparison
plot_mzi_comparison(
    phases,
    optical_0,
    qiskit_0
)