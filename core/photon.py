import numpy as np


class PhotonState:
    """
    Represents a single photon distributed across optical modes.
    """

    def __init__(self, modes=2, input_mode=0):
        if modes < 2:
            raise ValueError("At least 2 optical modes are required.")

        if input_mode < 0 or input_mode >= modes:
            raise ValueError("Invalid input mode.")

        self.modes = modes

        self.state = np.zeros(modes, dtype=complex)
        self.state[input_mode] = 1.0

    def probabilities(self):
        """
        Calculate the probability of finding the photon
        in each optical mode.
        """

        probabilities = np.abs(self.state) ** 2

        total = np.sum(probabilities)

        if not np.isclose(total, 1.0):
            probabilities = probabilities / total

        return probabilities

    def apply_unitary(self, unitary):
        """
        Apply an optical unitary matrix to the photon state.
        """

        unitary = np.asarray(unitary, dtype=complex)

        if unitary.shape != (self.modes, self.modes):
            raise ValueError(
                f"Unitary must be {self.modes}x{self.modes}."
            )

        self.state = unitary @ self.state

    def __str__(self):
        return str(self.state)