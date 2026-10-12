import numpy as np


class FockState:
    """
    Represents photon occupation numbers
    across multiple optical modes.

    Example:
        [1, 0] -> one photon in mode 0
        [0, 1] -> one photon in mode 1
        [1, 1] -> one photon in each mode
        [2, 0] -> two photons in mode 0
    """

    def __init__(self, occupations):
        self.occupations = np.asarray(
            occupations,
            dtype=int
        )

        if np.any(self.occupations < 0):
            raise ValueError(
                "Photon occupation numbers cannot be negative."
            )

    def photon_number(self):
        """
        Return the total number of photons.
        """

        return int(np.sum(self.occupations))

    def modes(self):
        """
        Return the number of optical modes.
        """

        return len(self.occupations)

    def __str__(self):
        return str(self.occupations)