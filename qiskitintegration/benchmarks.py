"""
QUANTA-SIM: Quantum Circuit Framework
Module: qiskitintegration.benchmarks
Role: 4/5 - Qiskit Integration (Digital Quantum Side)

This module provides quantitative verification and benchmarking metrics comparing:
- Digital quantum simulation results against analytical optical physics predictions.
- Metrics calculated:
  * Total Variation Distance (TVD)
  * Classical Fidelity / Bhattacharyya Coefficient
  * Hellinger Distance
  * Quantum Pure State Fidelity (|⟨ψ_opt|ψ_qiskit⟩|²)
  * Circuit metadata (Depth, Total Gates, 1-Qubit vs 2-Qubit Breakdown)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector


@dataclass
class BenchmarkReport:
    """
    Comprehensive quantitative verification and circuit complexity report.
    
    Attributes:
        total_variation_distance: TVD = 0.5 * sum(|P_opt - P_qiskit|), bounded in [0, 1].
        classical_fidelity: Bhattacharyya coefficient = sum(sqrt(P_opt * P_qiskit)), bounded in [0, 1].
        hellinger_distance: sqrt(1 - classical_fidelity), bounded in [0, 1].
        quantum_fidelity: Pure state fidelity |<psi_opt|psi_qiskit>|^2 (if statevectors available).
        circuit_depth: Longest critical path in gate execution.
        total_gates: Total count of quantum logic gates.
        single_qubit_gates: Count of 1-qubit gates (H, RZ, RY, X, S, etc.).
        two_qubit_gates: Count of multi-qubit entangling gates (CX, CZ, UnitaryGate 4x4, etc.).
        gate_breakdown: Detailed dictionary of gate counts per operation name.
        num_qubits: Total qubits allocated.
        num_clbits: Total measurement classical bits.
        optical_probabilities: Theoretical target optical probabilities.
        qiskit_probabilities: Digital quantum measured or statevector probabilities.
        shots: Number of measurement shots (None if exact statevector).
    """
    total_variation_distance: float
    classical_fidelity: float
    hellinger_distance: float
    quantum_fidelity: Optional[float]
    circuit_depth: int
    total_gates: int
    single_qubit_gates: int
    two_qubit_gates: int
    gate_breakdown: Dict[str, int]
    num_qubits: int
    num_clbits: int
    optical_probabilities: Dict[int, float]
    qiskit_probabilities: Dict[int, float]
    shots: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary format for Streamlit or JSON export."""
        return {
            "metrics": {
                "total_variation_distance": self.total_variation_distance,
                "classical_fidelity": self.classical_fidelity,
                "hellinger_distance": self.hellinger_distance,
                "quantum_fidelity": self.quantum_fidelity,
            },
            "circuit_metadata": {
                "circuit_depth": self.circuit_depth,
                "total_gates": self.total_gates,
                "single_qubit_gates": self.single_qubit_gates,
                "two_qubit_gates": self.two_qubit_gates,
                "gate_breakdown": self.gate_breakdown,
                "num_qubits": self.num_qubits,
                "num_clbits": self.num_clbits,
                "shots": self.shots,
            },
            "probability_comparison": {
                "optical_theory": self.optical_probabilities,
                "qiskit_simulation": self.qiskit_probabilities,
            }
        }

    def to_dataframe(self) -> pd.DataFrame:
        """
        Produce a summary DataFrame comparing optical vs Qiskit probabilities per mode.
        """
        modes = sorted(self.optical_probabilities.keys() | self.qiskit_probabilities.keys())
        rows = []
        for m in modes:
            p_opt = float(self.optical_probabilities.get(m, 0.0))
            p_qis = float(self.qiskit_probabilities.get(m, 0.0))
            delta = abs(p_opt - p_qis)
            rows.append({
                "Optical Mode": f"Mode {m}",
                "Optical Theory (P_opt)": float(f"{p_opt:.5f}"),
                "Qiskit Result (P_qiskit)": float(f"{p_qis:.5f}"),
                "Absolute Error (|ΔP|)": float(f"{delta:.5f}"),
                "Relative Error (%)": f"{(delta / max(p_opt, 1e-9)) * 100.0:.2f}%" if p_opt > 1e-9 else "N/A"
            })
        return pd.DataFrame(rows)


class QuantumBenchmarks:
    """
    Mathematical metrics calculator for comparing quantum circuits against optical physics models.
    """

    @staticmethod
    def total_variation_distance(
        p_theory: Union[np.ndarray, List[float], Dict[Any, float]],
        p_measured: Union[np.ndarray, List[float], Dict[Any, float]]
    ) -> float:
        """
        Calculate Total Variation Distance (TVD) between two probability distributions:
            TVD(P, Q) = 0.5 * sum(|P(x) - Q(x)|)
        
        Bounded strictly in [0.0, 1.0]. A value of 0.0 indicates perfect agreement.
        """
        p, q = QuantumBenchmarks._align_distributions(p_theory, p_measured)
        return float(0.5 * np.sum(np.abs(p - q)))

    @staticmethod
    def classical_fidelity(
        p_theory: Union[np.ndarray, List[float], Dict[Any, float]],
        p_measured: Union[np.ndarray, List[float], Dict[Any, float]]
    ) -> float:
        """
        Calculate Classical Fidelity (Bhattacharyya coefficient):
            BC(P, Q) = sum(sqrt(P(x) * Q(x)))
            
        Bounded in [0.0, 1.0]. A value of 1.0 indicates identical distributions.
        """
        p, q = QuantumBenchmarks._align_distributions(p_theory, p_measured)
        return float(np.sum(np.sqrt(np.clip(p * q, 0.0, 1.0))))

    @staticmethod
    def hellinger_distance(
        p_theory: Union[np.ndarray, List[float], Dict[Any, float]],
        p_measured: Union[np.ndarray, List[float], Dict[Any, float]]
    ) -> float:
        """
        Calculate Hellinger Distance:
            H(P, Q) = (1 / sqrt(2)) * sqrt(sum((sqrt(P(x)) - sqrt(Q(x)))^2))
                    = sqrt(1 - BC(P, Q))
        """
        bc = QuantumBenchmarks.classical_fidelity(p_theory, p_measured)
        return float(np.sqrt(np.clip(1.0 - bc, 0.0, 1.0)))

    @staticmethod
    def quantum_state_fidelity(
        state_a: Union[np.ndarray, Statevector],
        state_b: Union[np.ndarray, Statevector]
    ) -> float:
        """
        Calculate Quantum State Fidelity between two pure statevectors:
            F(psi, phi) = |<psi | phi>|^2
        """
        if isinstance(state_a, Statevector):
            vec_a = state_a.data
        else:
            vec_a = np.asarray(state_a, dtype=complex)

        if isinstance(state_b, Statevector):
            vec_b = state_b.data
        else:
            vec_b = np.asarray(state_b, dtype=complex)

        # Normalize
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a > 1e-12:
            vec_a = vec_a / norm_a
        if norm_b > 1e-12:
            vec_b = vec_b / norm_b

        inner_product = np.vdot(vec_a, vec_b)
        return float(np.abs(inner_product) ** 2)

    @staticmethod
    def analyze_circuit(circuit: QuantumCircuit) -> Dict[str, Any]:
        """
        Analyze circuit depth and categorize gate breakdown (single-qubit vs multi-qubit).
        """
        depth = circuit.depth()
        total_gates = circuit.size()
        ops_dict = dict(circuit.count_ops())

        # Exclude non-unitary auxiliary operations like barrier or measure from core gate counts
        pure_gate_ops = {k: v for k, v in ops_dict.items() if k not in ("barrier", "measure")}

        # Categorize single-qubit vs 2+ qubit gates
        single_qubit = 0
        multi_qubit = 0

        for instruction in circuit.data:
            op_name = instruction.operation.name
            if op_name in ("barrier", "measure"):
                continue
            num_qubits = len(instruction.qubits)
            if num_qubits == 1:
                single_qubit += 1
            else:
                multi_qubit += 1

        return {
            "depth": depth,
            "total_gates": total_gates,
            "pure_gate_count": sum(pure_gate_ops.values()),
            "single_qubit_gates": single_qubit,
            "two_qubit_gates": multi_qubit,
            "gate_breakdown": ops_dict,
            "num_qubits": circuit.num_qubits,
            "num_clbits": circuit.num_clbits,
        }

    @staticmethod
    def generate_report(
        circuit: Union[QuantumCircuit, Dict[Any, float]],
        optical_theory_probs: Union[Dict[Any, float], QuantumCircuit],
        qiskit_mode_probs: Optional[Union[Dict[Any, float], QuantumCircuit]] = None,
        optical_statevector: Optional[np.ndarray] = None,
        qiskit_statevector: Optional[np.ndarray] = None,
        shots: Optional[int] = None
    ) -> BenchmarkReport:
        """
        Generate a complete BenchmarkReport cross-validating optical theory and Qiskit digital execution.
        Supports both argument orders:
          - (circuit, optical_theory_probs, qiskit_mode_probs)
          - (optical_theory_probs, qiskit_mode_probs, circuit)
        """
        # Resolve argument ordering polymorphism
        qc: QuantumCircuit
        opt_probs_raw: Dict[Any, float]
        qis_probs_raw: Dict[Any, float]

        if isinstance(circuit, QuantumCircuit):
            qc = circuit
            opt_probs_raw = optical_theory_probs  # type: ignore[assignment]
            qis_probs_raw = qiskit_mode_probs if qiskit_mode_probs is not None else {}  # type: ignore[assignment]
        elif isinstance(qiskit_mode_probs, QuantumCircuit):
            qc = qiskit_mode_probs
            opt_probs_raw = circuit  # type: ignore[assignment]
            qis_probs_raw = optical_theory_probs  # type: ignore[assignment]
        else:
            raise TypeError("generate_report requires a Qiskit QuantumCircuit as either the first or third argument.")

        # Ensure uniform integer keys for optical modes
        opt_probs_clean: Dict[int, float] = {int(k): float(v) for k, v in opt_probs_raw.items()}
        qis_probs_clean: Dict[int, float] = {int(k): float(v) for k, v in qis_probs_raw.items()}

        tvd = QuantumBenchmarks.total_variation_distance(opt_probs_clean, qis_probs_clean)
        fidelity_c = QuantumBenchmarks.classical_fidelity(opt_probs_clean, qis_probs_clean)
        hellinger = QuantumBenchmarks.hellinger_distance(opt_probs_clean, qis_probs_clean)

        # Quantum fidelity if statevectors provided
        q_fidelity: Optional[float] = None
        if optical_statevector is not None and qiskit_statevector is not None:
            if len(optical_statevector) == len(qiskit_statevector):
                q_fidelity = QuantumBenchmarks.quantum_state_fidelity(optical_statevector, qiskit_statevector)

        circuit_info = QuantumBenchmarks.analyze_circuit(qc)

        return BenchmarkReport(
            total_variation_distance=tvd,
            classical_fidelity=fidelity_c,
            hellinger_distance=hellinger,
            quantum_fidelity=q_fidelity,
            circuit_depth=circuit_info["depth"],
            total_gates=circuit_info["total_gates"],
            single_qubit_gates=circuit_info["single_qubit_gates"],
            two_qubit_gates=circuit_info["two_qubit_gates"],
            gate_breakdown=circuit_info["gate_breakdown"],
            num_qubits=circuit_info["num_qubits"],
            num_clbits=circuit_info["num_clbits"],
            optical_probabilities=opt_probs_clean,
            qiskit_probabilities=qis_probs_clean,
            shots=shots
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _align_distributions(
        dist_a: Union[np.ndarray, List[float], Dict[Any, float]],
        dist_b: Union[np.ndarray, List[float], Dict[Any, float]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Helper to align two probability distributions into congruent numpy arrays."""
        if isinstance(dist_a, dict) and isinstance(dist_b, dict):
            all_keys = sorted(set(dist_a.keys()) | set(dist_b.keys()))
            vec_a = np.array([dist_a.get(k, 0.0) for k in all_keys], dtype=float)
            vec_b = np.array([dist_b.get(k, 0.0) for k in all_keys], dtype=float)
        else:
            vec_a = np.asarray(dist_a, dtype=float)
            vec_b = np.asarray(dist_b, dtype=float)
            max_len = max(len(vec_a), len(vec_b))
            if len(vec_a) < max_len:
                vec_a = np.pad(vec_a, (0, max_len - len(vec_a)))
            if len(vec_b) < max_len:
                vec_b = np.pad(vec_b, (0, max_len - len(vec_b)))

        # Normalize distributions to ensure strict probability spaces
        sum_a = np.sum(vec_a)
        sum_b = np.sum(vec_b)
        if sum_a > 1e-12:
            vec_a = vec_a / sum_a
        if sum_b > 1e-12:
            vec_b = vec_b / sum_b

        return vec_a, vec_b
