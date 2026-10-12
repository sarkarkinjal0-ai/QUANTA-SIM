import numpy as np

from probability import calculate_probabilities


state = np.array([
    1 / np.sqrt(2),
    1 / np.sqrt(2)
], dtype=complex)


print("State:")
print(state)

print("\nProbabilities:")
print(calculate_probabilities(state))

print("\nTotal probability:")
print(np.sum(calculate_probabilities(state)))