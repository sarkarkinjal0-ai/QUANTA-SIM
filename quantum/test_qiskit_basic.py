from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector


# Create a 1-qubit circuit
circuit = QuantumCircuit(1)


# Apply Hadamard gate
circuit.h(0)


# Calculate the final state
state = Statevector.from_instruction(circuit)


print("Qiskit Circuit:")
print(circuit)


print("\nStatevector:")
print(state)


print("\nProbabilities:")
print(state.probabilities())