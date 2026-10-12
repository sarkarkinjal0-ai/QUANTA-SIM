from noise import add_phase_noise


phase = 1.0
noise_strength = 0.1


print("Original phase:")
print(phase)

print("\nNoisy phases:")

for i in range(5):

    noisy_phase = add_phase_noise(
        phase,
        noise_strength
    )

    print(noisy_phase)
    