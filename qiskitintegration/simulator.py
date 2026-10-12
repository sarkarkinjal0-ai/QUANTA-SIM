"""
QUANTA-SIM: Quantum Circuit Framework
Module: qiskitintegration.simulator
Role: 4/5 - Qiskit Integration (Digital Quantum Side)

This module provides the execution and simulation backend for digital quantum circuit models:
- Modern Qiskit 1.0+ and 2.x compatible architecture.
- Two simulation pathways:
  1. Exact Statevector Evolution: Computes exact complex amplitudes and theoretical probabilities.
  2. Shot-Based Sampling: Uses AerSimulator / primitives to model quantum measurement collapse,
     detector shot noise, and finite sampling statistics (100 to 100,000+ shots).
- Decoupled, clean dataclasses ready for Streamlit UI integration.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from .converters import ModeEncoding, qubit_counts_to_mode_probabilities


@dataclass
class SimulationResult:
    """
    Standardized result data structure returned by DigitalQuantumEngine.
    
    Attributes:
        circuit_name: Name or description of the simulated circuit.
        is_exact_statevector: True if derived from pure statevector evolution, False if sampled.
        probabilities: Dictionary mapping computational basis bitstrings to probabilities.
        mode_probabilities: Dictionary mapping optical mode indices (0, 1, ...) to probabilities.
        counts: Dictionary of raw measurement counts (None for pure statevector runs).
        statevector: Complex amplitude array (None for shot-only runs).
        shots: Total number of shots simulated (None for pure statevector).
        execution_time_ms: Wall-clock execution time in milliseconds.
        metadata: Additional diagnostic or physical information.
    """
    circuit_name: str
    is_exact_statevector: bool
    probabilities: Dict[str, float]
    mode_probabilities: Dict[int, float]
    counts: Optional[Dict[str, int]] = None
    statevector: Optional[np.ndarray] = None
    shots: Optional[int] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to a standard serializable dictionary."""
        return {
            "circuit_name": self.circuit_name,
            "is_exact_statevector": self.is_exact_statevector,
            "shots": self.shots,
            "execution_time_ms": self.execution_time_ms,
            "probabilities": self.probabilities,
            "mode_probabilities": self.mode_probabilities,
            "counts": self.counts,
            "statevector": self.statevector.tolist() if self.statevector is not None else None,
            "metadata": self.metadata
        }

    def to_dataframe(self) -> pd.DataFrame:
        """
        Export probability distributions as a clean Pandas DataFrame for Streamlit display.
        """
        rows = []
        for bitstring, prob in sorted(self.probabilities.items()):
            count = self.counts.get(bitstring, None) if self.counts else None
            rows.append({
                "State / Bitstring": f"|{bitstring}>",
                "Probability": float(prob),
                "Sampled Count": count if count is not None else "Exact",
                "Percentage": f"{prob * 100.0:.2f}%"
            })
        return pd.DataFrame(rows)


class DigitalQuantumEngine:
    """
    Execution engine managing digital statevector and shot-based quantum circuit simulations.
    """

    def __init__(self, default_shots: int = 1024, seed: Optional[int] = None) -> None:
        """
        Initialize the quantum simulation engine.

        Parameters:
            default_shots: Default number of measurement shots for sampling.
            seed: Optional random seed for reproducible stochastic simulations.
        """
        self.default_shots = default_shots
        self.seed = seed
        self._aer_simulator = AerSimulator()

    def run_statevector(
        self,
        circuit: QuantumCircuit,
        encoding: ModeEncoding = ModeEncoding.SINGLE_QUBIT,
        total_modes: int = 2
    ) -> SimulationResult:
        """
        Execute exact statevector evolution on the quantum circuit.
        
        Removes any terminal measurement operations before computing statevector to obtain
        the exact coherent quantum state and pure theoretical probability amplitudes.

        Parameters:
            circuit: Qiskit QuantumCircuit.
            encoding: ModeEncoding convention used to map qubits to optical modes.
            total_modes: Number of physical optical modes.

        Returns:
            SimulationResult containing complex state amplitudes and exact probabilities.
        """
        t_start = time.perf_counter()

        # Create a clean circuit copy stripped of measurement operations
        clean_qc = circuit.remove_final_measurements(inplace=False)
        if clean_qc is None:
            clean_qc = circuit.copy()

        # Compute exact statevector using Qiskit quantum_info
        sv = Statevector.from_instruction(clean_qc)
        sv_data = np.asarray(sv.data, dtype=complex)

        # Extract theoretical probabilities for each computational basis bitstring
        num_qubits = clean_qc.num_qubits
        probabilities: Dict[str, float] = {}
        for idx, amp in enumerate(sv_data):
            bitstr = format(idx, f"0{num_qubits}b")
            probabilities[bitstr] = float(np.abs(amp) ** 2)

        # Synthesize integer counts equivalent for uniform converter mapping
        pseudo_counts = {b: int(p * 1_000_000) for b, p in probabilities.items()}
        mode_probs = qubit_counts_to_mode_probabilities(pseudo_counts, total_modes, encoding)

        t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0

        return SimulationResult(
            circuit_name=circuit.name or "QuantumCircuit",
            is_exact_statevector=True,
            probabilities=probabilities,
            mode_probabilities=mode_probs,
            counts=None,
            statevector=sv_data,
            shots=None,
            execution_time_ms=t_elapsed_ms,
            metadata={
                "num_qubits": num_qubits,
                "circuit_depth": clean_qc.depth(),
                "encoding": encoding.value
            }
        )

    def run_shots(
        self,
        circuit: QuantumCircuit,
        num_shots: Optional[int] = None,
        encoding: ModeEncoding = ModeEncoding.SINGLE_QUBIT,
        total_modes: int = 2,
        seed: Optional[int] = None
    ) -> SimulationResult:
        """
        Execute shot-based sampling simulation modeling finite measurement statistics and shot noise.

        Automatically ensures terminal measurement operations are present.

        Parameters:
            circuit: Qiskit QuantumCircuit.
            num_shots: Number of measurement shots (default: self.default_shots).
            encoding: ModeEncoding convention.
            total_modes: Number of optical modes.
            seed: Optional seed for stochastic simulator run.

        Returns:
            SimulationResult containing empirical counts, frequencies, and shot noise metrics.
        """
        shots = num_shots if num_shots is not None else self.default_shots
        run_seed = seed if seed is not None else self.seed

        t_start = time.perf_counter()

        # Check if circuit has measurements; if not, clone and append measurements
        meas_qc = circuit.copy()
        has_measurements = any(inst.operation.name == "measure" for inst in meas_qc.data)
        if not has_measurements:
            if meas_qc.num_clbits == meas_qc.num_qubits and meas_qc.num_clbits > 0:
                meas_qc.measure(meas_qc.qubits, meas_qc.clbits)
            else:
                meas_qc.measure_all()

        # Transpile to AerSimulator target basis
        tqc = transpile(meas_qc, self._aer_simulator, optimization_level=1)

        # Run simulation with Aer
        job = self._aer_simulator.run(tqc, shots=shots, seed_simulator=run_seed)
        result = job.result()
        raw_counts = result.get_counts()

        # If raw_counts is a single dict or needs normalization
        if isinstance(raw_counts, list):
            raw_counts = raw_counts[0]

        counts: Dict[str, int] = {str(k).replace(" ", ""): int(v) for k, v in raw_counts.items()}

        # Compute empirical probabilities
        probabilities: Dict[str, float] = {k: v / float(shots) for k, v in counts.items()}

        # Map to optical modes
        mode_probs = qubit_counts_to_mode_probabilities(counts, total_modes, encoding)

        t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0

        return SimulationResult(
            circuit_name=circuit.name or "QuantumCircuit",
            is_exact_statevector=False,
            probabilities=probabilities,
            mode_probabilities=mode_probs,
            counts=counts,
            statevector=None,
            shots=shots,
            execution_time_ms=t_elapsed_ms,
            metadata={
                "num_qubits": meas_qc.num_qubits,
                "circuit_depth": meas_qc.depth(),
                "transpiled_depth": tqc.depth(),
                "encoding": encoding.value,
                "seed": run_seed
            }
        )
