import numpy as np


class OpticalCircuit:
    def __init__(self, modes=2):
        self.modes = modes
        self.components = []

    def add_component(self, name, matrix):
        matrix = np.asarray(matrix, dtype=complex)

        if matrix.shape != (self.modes, self.modes):
            raise ValueError(
                f"Matrix must be {self.modes}x{self.modes}."
            )

        self.components.append((name, matrix))

    def overall_unitary(self):
        """
        Calculate the combined unitary matrix
        of all components in the circuit.
        """

        result = np.eye(self.modes, dtype=complex)

        for name, matrix in self.components:
            result = matrix @ result

        return result

    def show_components(self):
        """
        Display the components in the circuit.
        """

        if not self.components:
            print("Circuit is empty.")
            return

        print("Optical Circuit:")

        for i, (name, matrix) in enumerate(self.components, start=1):
            print(f"{i}. {name}")
    def run(self, state):
        """
        Send a quantum state through the optical circuit.
        """

        state = np.asarray(state, dtype=complex)

        if len(state) != self.modes:
            raise ValueError(
                f"State must have {self.modes} amplitudes."
            )

        return self.overall_unitary() @ state