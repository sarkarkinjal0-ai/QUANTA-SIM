import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from noise import simulate_noisy_mzi


phase = 1.0
noise_strength = 0.1


for i in range(5):

    noisy_phase, state, probabilities = simulate_noisy_mzi(
        phase,
        noise_strength
    )

    print(f"\nTrial {i + 1}")

    print("Noisy phase:")
    print(noisy_phase)

    print("Output probabilities:")
    print(probabilities)

    print("Total probability:")
    print(probabilities.sum())