import numpy as np

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector


def compare_beam_splitter():
    """
    Compare the QUANTA-SIM optical beam splitter
    with the equivalent Qiskit Hadamard operation.
    """

    # Optical beam splitter result
    optical_state = np.array([
        1 / np.sqrt(2),
        1 / np.sqrt(2)
    ], dtype=complex)

    optical_probabilities = np.abs(
        optical_state
    ) ** 2

    # Qiskit equivalent
    circuit = QuantumCircuit(1)
    circuit.h(0)

    qiskit_state = Statevector.from_instruction(
        circuit
    )

    qiskit_probabilities = qiskit_state.probabilities()

    # Compare probabilities
    match = np.allclose(
        optical_probabilities,
        qiskit_probabilities
    )

    return (
        optical_probabilities,
        qiskit_probabilities,
        match
    )
def compare_mzi(phase):
    """
    Compare the QUANTA-SIM optical MZI
    with the equivalent Qiskit MZI.
    """

    import sys
    import os

    sys.path.append(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )
    )

    from experiments.mzi import simulate_mzi
    from quantum.qiskit_mzi import simulate_qiskit_mzi

    # Optical MZI
    _, optical_probabilities = simulate_mzi(
        phase
    )

    # Qiskit MZI
    _, qiskit_probabilities = simulate_qiskit_mzi(
        phase
    )

    match = np.allclose(
        optical_probabilities,
        qiskit_probabilities
    )

    return (
        optical_probabilities,
        qiskit_probabilities,
        match
    )