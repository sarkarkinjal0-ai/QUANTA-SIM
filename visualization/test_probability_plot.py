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

from visualization.plots import plot_probability_histogram


# Example 4-mode probability distribution
probabilities = np.array([
    0.5,
    0.0,
    0.5,
    0.0
])

labels = [
    "Mode 0",
    "Mode 1",
    "Mode 2",
    "Mode 3"
]


plot_probability_histogram(
    probabilities,
    labels
)