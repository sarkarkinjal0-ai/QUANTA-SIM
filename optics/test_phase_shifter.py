import numpy as np

from phase_shifter import phase_shifter


phase = np.pi / 2

matrix = phase_shifter(phase)

print("Phase:")
print(phase)

print("\nPhase Shifter Matrix:")
print(matrix)