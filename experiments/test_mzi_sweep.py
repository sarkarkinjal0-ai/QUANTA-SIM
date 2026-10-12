import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

from mzi import phase_sweep


phases, output_0, output_1 = phase_sweep(points=5)


print("Phases:")
print(phases)

print("\nOutput 0 probabilities:")
print(output_0)

print("\nOutput 1 probabilities:")
print(output_1)

print("\nProbability check:")
print(output_0 + output_1)