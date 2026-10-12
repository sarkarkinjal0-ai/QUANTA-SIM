import numpy as np

from comparison import compare_mzi


phases = [
    0,
    np.pi / 2,
    np.pi,
    3 * np.pi / 2
]


for phase in phases:

    optical, qiskit, match = compare_mzi(
        phase
    )

    print("\nPhase:")
    print(phase)

    print("Optical probabilities:")
    print(optical)

    print("Qiskit probabilities:")
    print(qiskit)

    print("Do they match?")
    print(match)