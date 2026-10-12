"""
QUANTA-SIM: Quantum Circuit Framework
Module: qiskitintegration.circuit_builder
Role: 4/5 - Qiskit Integration (Digital Quantum Side)

This module provides the central high-level builder `QiskitOpticalCircuit` to translate
linear optical experiments into gate-based Qiskit quantum circuits (compatible with Qiskit 1.0+ and 2.x).

Key Features:
- Seamless construction of single-photon optical circuits.
- 50:50 and variable beam splitters with configurable phase conventions.
- Configurable phase shifters (PhaseGate / RZGate).
- Single-photon detectors (quantum measurement collapse).
- Pre-packaged architectures:
  * Mach-Zehnder Interferometer (MZI) with complete phase sweeps.
  * 2-Photon Hong-Ou-Mandel (HOM) analogue circuit demonstrating quantum bunching.
  * N-mode optical interferometer networks (dense log2(N) and dual-rail).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.library import PhaseGate, RZGate, RYGate, HGate, SGate, UnitaryGate

from .converters import (
    BeamSplitterConvention,
    ModeEncoding,
    get_beam_splitter_matrix,
    get_phase_shifter_matrix,
    apply_zyz_to_circuit,
    embed_givens_dual_rail,
    embed_unitary_dense
)


class QiskitOpticalCircuit:
    """
    Builder and wrapper for translating linear optical setups to Qiskit QuantumCircuits.
    
    Attributes:
        num_modes (int): Number of optical spatial modes in the experiment.
        encoding (ModeEncoding): Optical-to-qubit mapping scheme.
        circuit (QuantumCircuit): The underlying Qiskit circuit.
        num_qubits (int): Total qubits allocated.
        num_clbits (int): Total classical measurement bits allocated.
    """

    def __init__(
        self,
        num_modes: int = 2,
        encoding: Union[ModeEncoding, str] = ModeEncoding.SINGLE_QUBIT,
        name: str = "OpticalCircuit"
    ) -> None:
        """
        Initialize the quantum optical circuit.

        Parameters:
            num_modes: Number of physical optical paths / modes (default 2).
            encoding: ModeEncoding (SINGLE_QUBIT for 2 modes, DENSE or DUAL_RAIL for N modes).
            name: Circuit identifier name.
        """
        if isinstance(encoding, str):
            encoding = ModeEncoding(encoding)

        self.num_modes = num_modes
        self.encoding = encoding
        self.name = name

        # Determine qubit count based on encoding
        if self.encoding == ModeEncoding.SINGLE_QUBIT:
            if num_modes != 2:
                raise ValueError("SINGLE_QUBIT encoding is strictly for 2 optical modes. Use DENSE or DUAL_RAIL for N > 2.")
            self.num_qubits = 1
            self.num_clbits = 1
        elif self.encoding == ModeEncoding.DENSE:
            self.num_qubits = int(np.ceil(np.log2(max(num_modes, 2))))
            self.num_clbits = self.num_qubits
        elif self.encoding == ModeEncoding.DUAL_RAIL:
            self.num_qubits = num_modes
            self.num_clbits = num_modes
        else:
            raise ValueError(f"Unsupported encoding: {encoding}")

        self.qr = QuantumRegister(self.num_qubits, name="q")
        self.cr = ClassicalRegister(self.num_clbits, name="c")
        self.circuit = QuantumCircuit(self.qr, self.cr, name=self.name)

        # Track optical component metadata
        self.component_history: List[Dict[str, Union[str, float, int]]] = []

    def set_input_mode(self, mode_idx: int) -> "QiskitOpticalCircuit":
        """
        Prepare an initial single photon entering a specific optical mode.

        Parameters:
            mode_idx: Input mode index (0 <= mode_idx < num_modes).

        Returns:
            self for chaining.
        """
        if mode_idx < 0 or mode_idx >= self.num_modes:
            raise ValueError(f"Input mode {mode_idx} out of range for {self.num_modes} modes.")

        if self.encoding == ModeEncoding.SINGLE_QUBIT:
            # Mode 0 -> |0> (default ground state)
            # Mode 1 -> |1> (apply Pauli X)
            if mode_idx == 1:
                self.circuit.x(self.qr[0])

        elif self.encoding == ModeEncoding.DENSE:
            # Convert mode_idx to binary and flip appropriate qubits
            binary_str = format(mode_idx, f"0{self.num_qubits}b")
            for bit_pos, char in enumerate(reversed(binary_str)):
                if char == "1":
                    self.circuit.x(self.qr[bit_pos])

        elif self.encoding == ModeEncoding.DUAL_RAIL:
            # Single photon in mode_idx corresponds to exciting qubit mode_idx
            self.circuit.x(self.qr[mode_idx])

        self.component_history.append({"type": "input_state", "mode": mode_idx})
        return self

    def add_beam_splitter(
        self,
        mode_a: int = 0,
        mode_b: int = 1,
        theta: float = np.pi / 4,
        phi: float = 0.0,
        convention: Union[BeamSplitterConvention, str] = BeamSplitterConvention.REAL_SYMMETRIC,
        use_native_gates: bool = True
    ) -> "QiskitOpticalCircuit":
        """
        Append a 2-mode optical beam splitter to the circuit.

        Parameters:
            mode_a: First optical mode index.
            mode_b: Second optical mode index.
            theta: Splitting angle (theta = pi/4 for 50:50).
            phi: Internal phase offset (default 0.0).
            convention: BeamSplitterConvention (REAL_SYMMETRIC, IMAGINARY_SYMMETRIC, ROTATION).
            use_native_gates: If True, decomposes into native Qiskit gates (H, S, RZ, RY);
                              if False, injects custom UnitaryGate.

        Returns:
            self for chaining.
        """
        if isinstance(convention, str):
            convention = BeamSplitterConvention(convention)

        U_bs = get_beam_splitter_matrix(theta=theta, phi=phi, convention=convention)

        if self.encoding == ModeEncoding.SINGLE_QUBIT:
            target_qubit = 0
            if use_native_gates:
                is_50_50 = abs(theta - np.pi / 4) < 1e-9 and abs(phi) < 1e-9
                if convention == BeamSplitterConvention.REAL_SYMMETRIC and is_50_50:
                    # 50:50 Real symmetric beam splitter is exactly the Hadamard gate
                    self.circuit.h(self.qr[target_qubit])
                elif convention == BeamSplitterConvention.IMAGINARY_SYMMETRIC and is_50_50:
                    # S @ H @ S implements [[1, i], [i, 1]] / sqrt(2)
                    self.circuit.s(self.qr[target_qubit])
                    self.circuit.h(self.qr[target_qubit])
                    self.circuit.s(self.qr[target_qubit])
                elif convention == BeamSplitterConvention.ROTATION:
                    # Pure SO(2) rotation: RY(2*theta)
                    self.circuit.ry(2 * theta, self.qr[target_qubit])
                else:
                    # Exact Euler Z-Y-Z decomposition
                    apply_zyz_to_circuit(self.circuit, target_qubit, U_bs, adjust_global_phase=True)
            else:
                gate = UnitaryGate(U_bs, label=f"BS({convention.value[:4]})")
                self.circuit.append(gate, [self.qr[target_qubit]])

        elif self.encoding == ModeEncoding.DUAL_RAIL:
            # Dual-rail beam splitter acts as a 4x4 Givens rotation between qubits mode_a and mode_b
            G_4x4 = embed_givens_dual_rail(U_bs)
            givens_gate = UnitaryGate(G_4x4, label=f"BS_modes({mode_a},{mode_b})")
            self.circuit.append(givens_gate, [self.qr[mode_a], self.qr[mode_b]])

        elif self.encoding == ModeEncoding.DENSE:
            # In dense encoding for 2 modes, target_qubit = 0
            if self.num_modes == 2:
                apply_zyz_to_circuit(self.circuit, 0, U_bs, adjust_global_phase=True)
            else:
                # Controlled / embedded unitary for general dense network
                U_dense = embed_unitary_dense(U_bs, target_num_qubits=self.num_qubits)
                gate = UnitaryGate(U_dense, label=f"BS({mode_a},{mode_b})")
                self.circuit.append(gate, list(self.qr))

        self.component_history.append({
            "type": "beam_splitter",
            "mode_a": mode_a,
            "mode_b": mode_b,
            "theta": float(theta),
            "convention": convention.value
        })
        return self

    def add_phase_shifter(
        self,
        mode: int = 1,
        phi: float = 0.0,
        use_rz: bool = False
    ) -> "QiskitOpticalCircuit":
        """
        Append an optical phase shifter to a specific mode.

        In linear optics, PS(phi) adds relative phase exp(i*phi) to the mode.
        On qubits:
        - PhaseGate(phi) maps [[1, 0], [0, exp(i*phi)]] directly with 0 global phase.
        - RZ(phi) maps [[exp(-i*phi/2), 0], [0, exp(i*phi/2)]].

        Parameters:
            mode: Target optical mode (default: 1).
            phi: Optical phase shift (rad).
            use_rz: If True, uses RZ(phi); if False, uses PhaseGate(phi).

        Returns:
            self for chaining.
        """
        if self.encoding == ModeEncoding.SINGLE_QUBIT:
            target_qubit = 0
            if mode == 1:
                if use_rz:
                    self.circuit.rz(phi, self.qr[target_qubit])
                else:
                    self.circuit.p(phi, self.qr[target_qubit])
            elif mode == 0:
                # Phase shift on Mode 0 corresponds to relative negative phase on Mode 1
                if use_rz:
                    self.circuit.rz(-phi, self.qr[target_qubit])
                else:
                    # Global phase + phase on |0>
                    self.circuit.global_phase += phi
                    self.circuit.p(-phi, self.qr[target_qubit])

        elif self.encoding == ModeEncoding.DUAL_RAIL:
            # In dual-rail, phase shifter directly acts on qubit corresponding to that mode
            target_qubit = mode
            if use_rz:
                self.circuit.rz(phi, self.qr[target_qubit])
            else:
                self.circuit.p(phi, self.qr[target_qubit])

        elif self.encoding == ModeEncoding.DENSE:
            # Dense encoding applies diagonal phase operator
            U_ps = np.eye(2 ** self.num_qubits, dtype=complex)
            U_ps[mode, mode] = np.exp(1j * phi)
            gate = UnitaryGate(U_ps, label=f"PS(mode {mode})")
            self.circuit.append(gate, list(self.qr))

        self.component_history.append({
            "type": "phase_shifter",
            "mode": mode,
            "phi": float(phi)
        })
        return self

    def add_detectors(self, modes: Optional[List[int]] = None) -> "QiskitOpticalCircuit":
        """
        Add single-photon detector measurements to all or specified optical modes.

        Parameters:
            modes: List of mode indices to measure (None measures all modes).

        Returns:
            self for chaining.
        """
        if self.encoding in (ModeEncoding.SINGLE_QUBIT, ModeEncoding.DENSE):
            # All qubits measured to determine computational basis state
            self.circuit.measure(self.qr, self.cr)
        elif self.encoding == ModeEncoding.DUAL_RAIL:
            target_modes = modes if modes is not None else list(range(self.num_modes))
            for m in target_modes:
                self.circuit.measure(self.qr[m], self.cr[m])

        self.component_history.append({"type": "detectors"})
        return self

    def add_arbitrary_unitary(
        self,
        U: np.ndarray,
        use_euler: bool = True
    ) -> "QiskitOpticalCircuit":
        """
        Append an arbitrary optical unitary matrix U to the circuit.

        Parameters:
            U: Optical unitary matrix (2x2 for single qubit, or N x N for dense).
            use_euler: If True and 2x2, uses Euler ZYZ decomposition; otherwise UnitaryGate.

        Returns:
            self for chaining.
        """
        dim = U.shape[0]
        if dim == 2 and self.encoding == ModeEncoding.SINGLE_QUBIT:
            if use_euler:
                apply_zyz_to_circuit(self.circuit, 0, U, adjust_global_phase=True)
            else:
                self.circuit.append(UnitaryGate(U, label="U_arb"), [self.qr[0]])
        elif self.encoding == ModeEncoding.DENSE:
            U_dense = embed_unitary_dense(U, target_num_qubits=self.num_qubits)
            self.circuit.append(UnitaryGate(U_dense, label="U_dense"), list(self.qr))
        else:
            raise NotImplementedError("Arbitrary unitary injection currently supports SINGLE_QUBIT and DENSE.")

        self.component_history.append({"type": "arbitrary_unitary", "dim": dim})
        return self

    # =========================================================================
    # Pre-Packaged Scientific Architectures
    # =========================================================================

    @staticmethod
    def build_mach_zehnder(
        phase_phi: float,
        input_mode: int = 0,
        bs1_theta: float = np.pi / 4,
        bs2_theta: float = np.pi / 4,
        convention: Union[BeamSplitterConvention, str] = BeamSplitterConvention.REAL_SYMMETRIC,
        add_measurement: bool = True
    ) -> QuantumCircuit:
        """
        Construct a complete Mach-Zehnder Interferometer (MZI) quantum circuit.

        Pipeline Stages:
            1. Input State Injection: |1, 0> (Mode 0) or |0, 1> (Mode 1).
            2. Beam Splitter 1 (BS1): Splits photon into spatial superposition.
            3. Phase Shifter (PS): Applies internal phase shift phi to Mode 1.
            4. Beam Splitter 2 (BS2): Recombines probability amplitudes.
            5. Detectors: Quantum measurement collapse at output ports.

        Theoretical Probabilities (Real-symmetric convention, input Mode 0):
            P(Mode 0) = cos^2(phi / 2) = (1 + cos(phi)) / 2
            P(Mode 1) = sin^2(phi / 2) = (1 - cos(phi)) / 2

        Parameters:
            phase_phi: Internal phase shift angle (rad).
            input_mode: Optical launch mode (0 or 1).
            bs1_theta: Splitting angle for BS1 (pi/4 = 50:50).
            bs2_theta: Splitting angle for BS2 (pi/4 = 50:50).
            convention: Beam splitter convention (REAL_SYMMETRIC or IMAGINARY_SYMMETRIC).
            add_measurement: Whether to append classical measurement gates.

        Returns:
            QuantumCircuit: Fully synthesized Qiskit circuit.
        """
        opt_circuit = QiskitOpticalCircuit(
            num_modes=2,
            encoding=ModeEncoding.SINGLE_QUBIT,
            name=f"MZI_phi_{phase_phi:.2f}"
        )

        # Stage 1: Input photon launch
        opt_circuit.set_input_mode(input_mode)

        # Stage 2: BS1
        opt_circuit.add_beam_splitter(
            mode_a=0, mode_b=1,
            theta=bs1_theta,
            convention=convention,
            use_native_gates=True
        )

        # Stage 3: Controllable phase shift on Mode 1
        opt_circuit.add_phase_shifter(mode=1, phi=phase_phi)

        # Stage 4: BS2
        opt_circuit.add_beam_splitter(
            mode_a=0, mode_b=1,
            theta=bs2_theta,
            convention=convention,
            use_native_gates=True
        )

        # Stage 5: Detectors
        if add_measurement:
            opt_circuit.add_detectors()

        return opt_circuit.circuit

    @classmethod
    def build_mzi(
        cls,
        phi: float = 0.0,
        input_mode: int = 0,
        bs1_theta: float = np.pi / 4,
        bs2_theta: float = np.pi / 4,
        convention: Union[BeamSplitterConvention, str] = BeamSplitterConvention.REAL_SYMMETRIC,
        add_measurement: bool = True
    ) -> QuantumCircuit:
        """
        Convenience shorthand alias for build_mach_zehnder accepting phase as 'phi'.
        """
        return cls.build_mach_zehnder(
            phase_phi=phi,
            input_mode=input_mode,
            bs1_theta=bs1_theta,
            bs2_theta=bs2_theta,
            convention=convention,
            add_measurement=add_measurement
        )

    @staticmethod
    def build_hong_ou_mandel_2qubit(
        theta: float = np.pi / 4,
        delay_phase: float = 0.0,
        add_measurement: bool = True
    ) -> Tuple[QuantumCircuit, Dict[str, str]]:
        """
        Construct a 2-qubit digital quantum circuit demonstrating the 2-Photon Hong-Ou-Mandel (HOM) effect.

        Scientific Principle & Mapping:
            In linear optics, when two identical indistinguishable photons enter opposite ports
            of a 50:50 beam splitter, quantum interference completely cancels the coincidence outcome |1, 1>.
            The photons 'bunch' together, emerging in a superposition of |2, 0> and |0, 2>.

            We map the 3-dimensional 2-photon Fock subspace onto a 2-qubit computational basis:
                |00> <---> |2, 0> (Both photons emerge in Mode 0)
                |01> <---> |1, 1> (Coincidence state: 1 photon in Mode 0, 1 in Mode 1)
                |11> <---> |0, 2> (Both photons emerge in Mode 1)
                |10> <---> |aux>  (Orthogonal unused subspace)

            Circuit Architecture:
                1. Initial State Preparation:
                   Input is Fock state |1, 1>, mapped to computational basis |01>.
                   Prepared via X gate on qubit 0 (Qiskit endianness: |q1 q0> = |01>).
                2. Phase Shift / Delay Stage:
                   If delay_phase != 0, adds a relative phase shift mimicking temporal delay.
                3. Fock-Space Beam Splitter Transformation:
                   At 50:50 (theta = pi/4), the input |01> transforms into the bunched state:
                       |psi_out> = (1 / sqrt(2)) * (|00> - |11>)
                   Achieved via native gates: H(q0) -> CX(q0, q1) (or exact parameterized U4).
                4. Measurement:
                   Sampling produces ~50% |00> (|2,0>), ~50% |11> (|0,2>), and 0% |01> (|1,1>).

        Parameters:
            theta: Splitting angle (theta = pi/4 corresponds to 50:50 HOM dip minimum).
            delay_phase: Delay phase offset (0.0 corresponds to zero path delay / maximal indistinguishability).
            add_measurement: If True, appends measurement operations.

        Returns:
            Tuple[QuantumCircuit, Dict[str, str]]:
                - Synthesized Qiskit QuantumCircuit.
                - Mapping dictionary connecting qubit bitstrings to physical Fock states.
        """
        qr = QuantumRegister(2, name="q")
        cr = ClassicalRegister(2, name="c")
        qc = QuantumCircuit(qr, cr, name=f"HOM_2Photon_theta_{theta:.2f}")

        fock_mapping = {
            "00": "|2,0> (Bunched Mode 0)",
            "01": "|1,1> (Coincidence State)",
            "11": "|0,2> (Bunched Mode 1)",
            "10": "|aux> (Unoccupied)"
        }

        # Step 1: Prepare |01> corresponding to Fock |1, 1>
        qc.x(qr[0])

        # Step 2: Temporal delay / relative phase stage
        if abs(delay_phase) > 1e-9:
            qc.p(delay_phase, qr[0])

        # Step 3: Beam Splitter interaction
        # We construct the exact 3x3 Fock-space transformation matrix for arbitrary theta:
        c = np.cos(theta)
        s = np.sin(theta)
        
        # In basis {|2,0>, |1,1>, |0,2>}:
        # |2,0>_out = c^2 |2,0> - sqrt(2)cs |1,1> + s^2 |0,2>
        # |1,1>_out = sqrt(2)cs |2,0> + (c^2 - s^2) |1,1> - sqrt(2)cs |0,2>
        # |0,2>_out = s^2 |2,0> + sqrt(2)cs |1,1> + c^2 |0,2>
        #
        # Mapping to {|00>, |01>, |11>, |10>}:
        # basis index 0: |00> (|2,0>)
        # basis index 1: |01> (|1,1>)
        # basis index 2: |10> (|aux>)
        # basis index 3: |11> (|0,2>)
        
        U_fock_4x4 = np.eye(4, dtype=complex)
        
        # Col 0: image of |00> (|2,0>)
        U_fock_4x4[0, 0] = c ** 2
        U_fock_4x4[1, 0] = np.sqrt(2.0) * c * s
        U_fock_4x4[3, 0] = s ** 2
        
        # Col 1: image of |01> (|1,1>)
        U_fock_4x4[0, 1] = -np.sqrt(2.0) * c * s
        U_fock_4x4[1, 1] = (c ** 2) - (s ** 2)
        U_fock_4x4[3, 1] = np.sqrt(2.0) * c * s
        
        # Col 3: image of |11> (|0,2>)
        U_fock_4x4[0, 3] = s ** 2
        U_fock_4x4[1, 3] = -np.sqrt(2.0) * c * s
        U_fock_4x4[3, 3] = c ** 2

        # Verify unitarity
        diff = np.linalg.norm(U_fock_4x4.conj().T @ U_fock_4x4 - np.eye(4))
        if diff > 1e-6:
            raise ValueError(f"Fock 4x4 unitary matrix is not unitary: {diff}")

        # Inject into circuit
        hom_gate = UnitaryGate(U_fock_4x4, label=f"BS_Fock(θ={theta:.2f})")
        qc.append(hom_gate, [qr[0], qr[1]])

        # Step 4: Measurement
        if add_measurement:
            qc.measure(qr, cr)

        return qc, fock_mapping

    @classmethod
    def build_hom_analog(
        cls,
        mixing_angle: float = np.pi / 4,
        delay_phase: float = 0.0,
        add_measurement: bool = True
    ) -> Tuple[QuantumCircuit, Dict[str, str]]:
        """
        Convenience shorthand alias for build_hong_ou_mandel_2qubit accepting 'mixing_angle'.
        """
        return cls.build_hong_ou_mandel_2qubit(
            theta=mixing_angle,
            delay_phase=delay_phase,
            add_measurement=add_measurement
        )

    @classmethod
    def build_hom(
        cls,
        mixing_angle: float = np.pi / 4,
        delay_phase: float = 0.0,
        add_measurement: bool = True
    ) -> Tuple[QuantumCircuit, Dict[str, str]]:
        """
        Convenience shorthand alias for build_hong_ou_mandel_2qubit.
        """
        return cls.build_hong_ou_mandel_2qubit(
            theta=mixing_angle,
            delay_phase=delay_phase,
            add_measurement=add_measurement
        )

    @staticmethod
    def build_4mode_network(
        U_4x4: np.ndarray,
        input_mode: int = 0,
        add_measurement: bool = True
    ) -> QuantumCircuit:
        """
        Construct a dense 2-qubit quantum circuit simulating a 4-mode optical interferometer.

        Parameters:
            U_4x4: 4x4 complex unitary matrix representing the linear optical multiport.
            input_mode: Input mode index (0, 1, 2, or 3).
            add_measurement: If True, adds measurement gates.

        Returns:
            QuantumCircuit: 2-qubit circuit with measurement.
        """
        if U_4x4.shape != (4, 4):
            raise ValueError(f"Expected 4x4 matrix, got {U_4x4.shape}")

        opt_circ = QiskitOpticalCircuit(num_modes=4, encoding=ModeEncoding.DENSE, name="4Mode_Interferometer")
        opt_circ.set_input_mode(input_mode)
        opt_circ.add_arbitrary_unitary(U_4x4)
        if add_measurement:
            opt_circ.add_detectors()

        return opt_circ.circuit

    @classmethod
    def build_dense_4mode_network(
        cls,
        unitary_matrix: np.ndarray,
        input_mode: int = 0,
        add_measurement: bool = True
    ) -> QuantumCircuit:
        """
        Convenience shorthand alias for build_4mode_network.
        """
        return cls.build_4mode_network(
            U_4x4=unitary_matrix,
            input_mode=input_mode,
            add_measurement=add_measurement
        )

    @staticmethod
    def sweep_mach_zehnder(
        phases: Optional[np.ndarray] = None,
        num_points: int = 40,
        input_mode: int = 0,
        bs1_theta: float = np.pi / 4,
        bs2_theta: float = np.pi / 4,
        convention: Union[BeamSplitterConvention, str] = BeamSplitterConvention.REAL_SYMMETRIC,
        shots: Optional[int] = 2048,
        seed: Optional[int] = 42
    ) -> "MZISweepResult":
        """
        Execute an automated parameter sweep of the Mach-Zehnder Interferometer over phase phi from 0 to 2*pi.

        Computes both:
        1. Exact analytical optical transmission curves: P_0(phi) and P_1(phi).
        2. Qiskit digital quantum circuit simulation (sampled shots or statevector).

        Returns:
            MZISweepResult: Structured dataset containing angles, theoretical curves,
                            digital quantum data points, TVD per point, and fringe visibilities.
        """
        if isinstance(convention, str):
            convention = BeamSplitterConvention(convention)

        from .simulator import DigitalQuantumEngine

        phase_vals = np.linspace(0.0, 2.0 * np.pi, num_points) if phases is None else np.asarray(phases, dtype=float)

        engine = DigitalQuantumEngine(seed=seed)

        bs1_mat = get_beam_splitter_matrix(theta=bs1_theta, convention=convention)
        bs2_mat = get_beam_splitter_matrix(theta=bs2_theta, convention=convention)

        num_pts = len(phase_vals)
        opt_p0 = np.zeros(num_pts, dtype=float)
        opt_p1 = np.zeros(num_pts, dtype=float)
        qis_p0 = np.zeros(num_pts, dtype=float)
        qis_p1 = np.zeros(num_pts, dtype=float)
        tvd_arr = np.zeros(num_pts, dtype=float)

        in_vec = np.array([1.0, 0.0], dtype=complex) if input_mode == 0 else np.array([0.0, 1.0], dtype=complex)

        for i, phi in enumerate(phase_vals):
            # 1. Optical Theory
            ps_mat = get_phase_shifter_matrix(float(phi))
            u_total = bs2_mat @ ps_mat @ bs1_mat
            out_vec = u_total @ in_vec
            p0_th = float(np.abs(out_vec[0]) ** 2)
            p1_th = float(np.abs(out_vec[1]) ** 2)
            opt_p0[i] = p0_th
            opt_p1[i] = p1_th

            # 2. Qiskit Digital Simulation
            qc = QiskitOpticalCircuit.build_mach_zehnder(
                phase_phi=float(phi),
                input_mode=input_mode,
                bs1_theta=bs1_theta,
                bs2_theta=bs2_theta,
                convention=convention,
                add_measurement=(shots is not None)
            )

            if shots is not None:
                sim_res = engine.run_shots(qc, num_shots=shots, seed=seed)
            else:
                sim_res = engine.run_statevector(qc)

            p0_qis = sim_res.mode_probabilities.get(0, 0.0)
            p1_qis = sim_res.mode_probabilities.get(1, 0.0)
            qis_p0[i] = p0_qis
            qis_p1[i] = p1_qis

            # TVD at this phase point
            tvd_arr[i] = 0.5 * (abs(p0_th - p0_qis) + abs(p1_th - p1_qis))

        # Fringe visibility: V = (I_max - I_min) / (I_max + I_min)
        i_max_th, i_min_th = np.max(opt_p0), np.min(opt_p0)
        vis_th = float((i_max_th - i_min_th) / max(i_max_th + i_min_th, 1e-9))

        i_max_qis, i_min_qis = np.max(qis_p0), np.min(qis_p0)
        vis_qis = float((i_max_qis - i_min_qis) / max(i_max_qis + i_min_qis, 1e-9))

        return MZISweepResult(
            phases=phase_vals,
            optical_theory_p0=opt_p0,
            optical_theory_p1=opt_p1,
            qiskit_measured_p0=qis_p0,
            qiskit_measured_p1=qis_p1,
            tvd_per_point=tvd_arr,
            mean_tvd=float(np.mean(tvd_arr)),
            visibility_theory=vis_th,
            visibility_qiskit=vis_qis,
            shots=shots,
            convention=convention.value
        )

    @staticmethod
    def sweep_hong_ou_mandel(
        thetas: Optional[np.ndarray] = None,
        num_points: int = 35,
        delay_phase: float = 0.0,
        shots: Optional[int] = 2048,
        seed: Optional[int] = 42
    ) -> "HOMSweepResult":
        """
        Execute an automated parameter sweep of the 2-Photon Hong-Ou-Mandel effect
        over beam splitter mixing angle theta from 0 to pi/2.

        Demonstrates:
        1. Theoretical coincidence probability P(|1, 1>) = cos^2(2*theta).
        2. Theoretical bunching probabilities P(|2, 0>) = P(|0, 2>) = 0.5 * sin^2(2*theta).
        3. Digital quantum circuit simulation at each theta point.
        """
        from .simulator import DigitalQuantumEngine

        theta_vals = np.linspace(0.0, np.pi / 2.0, num_points) if thetas is None else np.asarray(thetas, dtype=float)

        engine = DigitalQuantumEngine(seed=seed)

        num_pts = len(theta_vals)
        th_coinc = np.zeros(num_pts, dtype=float)
        th_b00 = np.zeros(num_pts, dtype=float)
        th_b11 = np.zeros(num_pts, dtype=float)

        qis_coinc = np.zeros(num_pts, dtype=float)
        qis_b00 = np.zeros(num_pts, dtype=float)
        qis_b11 = np.zeros(num_pts, dtype=float)

        for i, th in enumerate(theta_vals):
            # Theoretical Fock state probabilities
            th_coinc[i] = float(np.cos(2.0 * th) ** 2)
            th_b00[i] = float(0.5 * (np.sin(2.0 * th) ** 2))
            th_b11[i] = float(0.5 * (np.sin(2.0 * th) ** 2))

            qc, _ = QiskitOpticalCircuit.build_hong_ou_mandel_2qubit(
                theta=float(th),
                delay_phase=delay_phase,
                add_measurement=(shots is not None)
            )

            if shots is not None:
                sim_res = engine.run_shots(qc, num_shots=shots, seed=seed)
            else:
                sim_res = engine.run_statevector(qc)

            qis_b00[i] = sim_res.probabilities.get("00", 0.0)
            qis_coinc[i] = sim_res.probabilities.get("01", 0.0)
            qis_b11[i] = sim_res.probabilities.get("11", 0.0)

        # Find dip index (near theta = pi/4)
        dip_idx = int(np.argmin(np.abs(theta_vals - (np.pi / 4.0))))
        tvd_at_dip = float(0.5 * (
            abs(th_coinc[dip_idx] - qis_coinc[dip_idx]) +
            abs(th_b00[dip_idx] - qis_b00[dip_idx]) +
            abs(th_b11[dip_idx] - qis_b11[dip_idx])
        ))

        return HOMSweepResult(
            thetas=theta_vals,
            theory_coincidence=th_coinc,
            qiskit_coincidence=qis_coinc,
            theory_bunched_00=th_b00,
            qiskit_bunched_00=qis_b00,
            theory_bunched_11=th_b11,
            qiskit_bunched_11=qis_b11,
            tvd_at_dip=tvd_at_dip,
            min_coincidence_theory=float(np.min(th_coinc)),
            min_coincidence_qiskit=float(qis_coinc[dip_idx]),
            shots=shots
        )


@dataclass
class MZISweepResult:
    """
    Results of an MZI phase sweep experiment.
    """
    phases: np.ndarray
    optical_theory_p0: np.ndarray
    optical_theory_p1: np.ndarray
    qiskit_measured_p0: np.ndarray
    qiskit_measured_p1: np.ndarray
    tvd_per_point: np.ndarray
    mean_tvd: float
    visibility_theory: float
    visibility_qiskit: float
    shots: Optional[int]
    convention: str

    def to_dataframe(self) -> pd.DataFrame:
        """Export sweep data to a Pandas DataFrame."""
        return pd.DataFrame({
            "Phase (rad)": self.phases,
            "Phase (deg)": np.degrees(self.phases),
            "Theory P0": self.optical_theory_p0,
            "Qiskit P0": self.qiskit_measured_p0,
            "Theory P1": self.optical_theory_p1,
            "Qiskit P1": self.qiskit_measured_p1,
            "TVD": self.tvd_per_point
        })


@dataclass
class HOMSweepResult:
    """
    Results of a 2-photon Hong-Ou-Mandel parameter sweep experiment.
    """
    thetas: np.ndarray
    theory_coincidence: np.ndarray
    qiskit_coincidence: np.ndarray
    theory_bunched_00: np.ndarray
    qiskit_bunched_00: np.ndarray
    theory_bunched_11: np.ndarray
    qiskit_bunched_11: np.ndarray
    tvd_at_dip: float
    min_coincidence_theory: float
    min_coincidence_qiskit: float
    shots: Optional[int]

    def to_dataframe(self) -> pd.DataFrame:
        """Export HOM sweep data to a Pandas DataFrame."""
        return pd.DataFrame({
            "Theta (rad)": self.thetas,
            "Theta (deg)": np.degrees(self.thetas),
            "Theory Coincidence |1,1>": self.theory_coincidence,
            "Qiskit Coincidence |01>": self.qiskit_coincidence,
            "Theory Bunched |2,0>": self.theory_bunched_00,
            "Qiskit Bunched |00>": self.qiskit_bunched_00,
            "Theory Bunched |0,2>": self.theory_bunched_11,
            "Qiskit Bunched |11>": self.qiskit_bunched_11
        })
