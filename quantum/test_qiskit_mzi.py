import numpy as np

from qiskit_mzi import simulate_qiskit_mzi


for phase in [
    0,
    np.pi / 2,
    np.pi,
    3 * np.pi / 2
]:

    state, probabilities = simulate_qiskit_mzi(
        phase
    )

    print("\nPhase:")
    print(phase)

    print("State:")
    print(state)

    print("Probabilities:")
    print(probabilities)

    print("Total probability:")
    print(probabilities.sum())