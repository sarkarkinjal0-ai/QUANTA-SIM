import numpy as np

class QuantumState:
    """
    Represents a quantum state in the physical simulation.
    """
    def __init__(self, amplitudes):
        """
        Initializes a quantum state with given complex amplitudes.
        
        Args:
            amplitudes (array-like): The probability amplitudes of the basis states.
        """
        self.amplitudes = np.array(amplitudes, dtype=np.complex128)
        self.normalize()

    def normalize(self):
        """Normalizes the state vector to ensure total probability equals 1.0 (Born's Rule)."""
        norm = np.linalg.norm(self.amplitudes)
        if norm > 0:
            self.amplitudes = self.amplitudes / norm

    def get_probabilities(self):
        """
        Returns the probability distribution of the state according to Born's rule.
        
        Returns:
            np.ndarray: An array of probabilities corresponding to each basis state.
        """
        return np.abs(self.amplitudes)**2

    def __repr__(self):
        return f"QuantumState(amplitudes={np.round(self.amplitudes, 3)})"


class CorePhysicsEngine:
    """
    Core mathematical formalism and physics engine for QUANTA-SIM.
    Handles N-mode unitary transformations and state evolution.
    """
    def __init__(self, num_modes):
        """
        Initializes the physics engine for an N-mode optical network.
        
        Args:
            num_modes (int): Number of distinct optical paths/modes in the system.
        """
        self.num_modes = num_modes

    def get_identity(self):
        """Returns an N x N identity matrix for the system."""
        return np.eye(self.num_modes, dtype=np.complex128)

    def embed_operator(self, operator, modes):
        """
        Embeds a k x k unitary operator into the full N x N unitary space of the system.
        
        Args:
            operator (np.ndarray): The k x k matrix representing the transformation.
            modes (list): List of integers specifying which modes the operator acts on.
            
        Returns:
            np.ndarray: The full N x N unitary matrix.
        """
        k = len(modes)
        if operator.shape != (k, k):
            raise ValueError(f"Operator shape {operator.shape} does not match the number of target modes {k}.")

        full_operator = self.get_identity()
        for i in range(k):
            for j in range(k):
                full_operator[modes[i], modes[j]] = operator[i, j]
                
        return full_operator

    def create_beam_splitter(self, reflectivity=0.5):
        """
        Generates a 2x2 beam splitter unitary matrix.
        
        Args:
            reflectivity (float): The reflection probability R. Default is 0.5 (50:50 BS).
            
        Returns:
            np.ndarray: A 2x2 complex unitary matrix.
        """
        t = np.sqrt(1 - reflectivity)
        r = np.sqrt(reflectivity) * 1j
        return np.array([
            [t, r],
            [r, t]
        ], dtype=np.complex128)

    def create_phase_shifter(self, phase_angle):
        """
        Generates a 1x1 phase shifter matrix.
        
        Args:
            phase_angle (float): Phase shift in radians.
            
        Returns:
            np.ndarray: A 1x1 complex unitary matrix.
        """
        return np.array([[np.exp(1j * phase_angle)]], dtype=np.complex128)
    
    def compute_total_unitary(self, unitaries):
        """
        Computes the total unitary matrix from a sequence of unitaries.
        U_total = U_n * ... * U_2 * U_1
        
        Args:
            unitaries (list of np.ndarray): List of full N x N unitary matrices in chronological order of application.
            
        Returns:
            np.ndarray: The cascaded N x N unitary matrix.
        """
        U_total = self.get_identity()
        # Matrix multiplication order: later operations are multiplied on the left.
        for U in unitaries:
            U_total = U @ U_total
        return U_total

    def evolve_state(self, initial_state, unitaries):
        """
        Evolves an initial quantum state through a cascade of unitary matrices.
        
        Args:
            initial_state (QuantumState): The input quantum state vector.
            unitaries (list of np.ndarray): Sequence of N x N unitaries to apply.
            
        Returns:
            QuantumState: The final computed state after all transformations.
        """
        if len(initial_state.amplitudes) != self.num_modes:
            raise ValueError(f"Initial state dimension {len(initial_state.amplitudes)} does not match number of modes {self.num_modes}.")

        total_unitary = self.compute_total_unitary(unitaries)
        final_amplitudes = total_unitary @ initial_state.amplitudes
            
        return QuantumState(final_amplitudes)

if __name__ == '__main__':
    # Quick test/example for a Mach-Zehnder Interferometer (MZI)
    engine = CorePhysicsEngine(num_modes=2)
    
    # 1. Initial State: photon in mode 0
    state_in = QuantumState([1, 0])
    
    # 2. Components
    bs1 = engine.embed_operator(engine.create_beam_splitter(), [0, 1])
    ps = engine.embed_operator(engine.create_phase_shifter(np.pi/2), [0])
    bs2 = engine.embed_operator(engine.create_beam_splitter(), [0, 1])
    
    # 3. Evolution
    state_out = engine.evolve_state(state_in, [bs1, ps, bs2])
    print("Final State:", state_out)
    print("Probabilities:", state_out.get_probabilities())
