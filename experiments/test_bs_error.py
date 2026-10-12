import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from noise import add_beam_splitter_error


transmission = 0.5
error_strength = 0.05


print("Ideal transmission:")
print(transmission)

print("\nActual transmissions:")

for i in range(5):

    actual = add_beam_splitter_error(
        transmission,
        error_strength
    )

    print(actual)