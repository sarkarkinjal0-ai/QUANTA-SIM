"""
QUANTA-SIM: Quantum Circuit Framework
Simulating Photonic Interference & Linear Optical Transformations through Quantum Circuits
Module: qiskitintegration (Role 4/5: Qiskit Integration - Digital Quantum Side)

This package exposes the complete bridge between linear optics and digital quantum circuits.
"""

__version__ = "1.0.0"
__author__ = "QUANTA-SIM Project Team (VIT Chennai Engineering Physics)"

from .converters import (
    BeamSplitterConvention,
    ModeEncoding,
    get_beam_splitter_matrix,
    get_phase_shifter_matrix,
    decompose_unitary_zyz,
    verify_zyz_decomposition,
    apply_zyz_to_circuit,
    embed_unitary_dense,
    embed_givens_dual_rail,
    optical_state_to_qubit_amplitudes,
    qubit_counts_to_mode_probabilities,
)

from .circuit_builder import (
    QiskitOpticalCircuit,
    MZISweepResult,
    HOMSweepResult,
)

from .simulator import (
    DigitalQuantumEngine,
    SimulationResult,
)

from .benchmarks import (
    QuantumBenchmarks,
    BenchmarkReport,
)

from .visuals import (
    plot_circuit,
    plot_probability_comparison,
    plot_mzi_interference_sweep,
    plot_hom_dip,
    plot_gate_breakdown,
)

__all__ = [
    # Conventions & Encodings
    "BeamSplitterConvention",
    "ModeEncoding",
    # Matrices & Converters
    "get_beam_splitter_matrix",
    "get_phase_shifter_matrix",
    "decompose_unitary_zyz",
    "verify_zyz_decomposition",
    "apply_zyz_to_circuit",
    "embed_unitary_dense",
    "embed_givens_dual_rail",
    "optical_state_to_qubit_amplitudes",
    "qubit_counts_to_mode_probabilities",
    # Circuit Builder
    "QiskitOpticalCircuit",
    "MZISweepResult",
    "HOMSweepResult",
    # Simulator
    "DigitalQuantumEngine",
    "SimulationResult",
    # Benchmarking
    "QuantumBenchmarks",
    "BenchmarkReport",
    # Visualizations
    "plot_circuit",
    "plot_probability_comparison",
    "plot_mzi_interference_sweep",
    "plot_hom_dip",
    "plot_gate_breakdown",
]
