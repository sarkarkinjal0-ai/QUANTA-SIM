# QUANTA-SIM: Digital Quantum Simulation Wing (`qiskitintegration`)
**Role 4/5 — Qiskit Integration (Digital Quantum Side)**  
*VIT Chennai — Engineering Physics Group Project*

---

## 🔬 Scientific & Architectural Overview

The `qiskitintegration` package serves as the digital gate-based quantum computing wing of the **QUANTA-SIM** quantum optics simulation suite. It bridges continuous linear optical transformations (spatial modes, beam splitters, phase shifters, interferometers) with discrete qubit quantum circuits using **Qiskit (version 1.0+ and 2.x standards)**.

```
                  ┌──────────────────────────────────────────────┐
                  │ Person 1 & 2: Core Physics & Optical Builder │
                  │      (Unitary Matrices U, Physical Angles)    │
                  └──────────────────────┬───────────────────────┘
                                         │  (numpy.ndarray, Dict)
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        ROLE 4/5: DIGITAL QUANTUM BRIDGE CORE                           │
│                                                                                        │
│   ┌────────────────────────┐        ┌─────────────────────────┐                        │
│   │     converters.py      │───────▶│    circuit_builder.py   │                        │
│   │ • Mode Encodings       │        │ • QiskitOpticalCircuit  │                        │
│   │ • Euler ZYZ Synthesis  │        │ • MZI 4-Stage Pipeline  │                        │
│   │ • BS Phase Conventions │        │ • 2-Photon HOM Analogue │                        │
│   └────────────────────────┘        └────────────┬────────────┘                        │
│                                                  │                                     │
│                                                  ▼                                     │
│   ┌────────────────────────┐        ┌─────────────────────────┐                        │
│   │     benchmarks.py      │◀───────│       simulator.py      │                        │
│   │ • TVD & Hellinger Dist │        │ • DigitalQuantumEngine  │                        │
│   │ • Classical Fidelity   │        │ • Statevector Evolution │                        │
│   │ • Circuit Depth / Ops  │        │ • Aer Shot Sampling     │                        │
│   └────────────┬───────────┘        └─────────────────────────┘                        │
│                │                                                                       │
│                └───────────────────┐                                                   │
│                                    ▼                                                   │
│                       ┌────────────────────────┐                                       │
│                       │       visuals.py       │                                       │
│                       │ • Circuit Diagrams     │                                       │
│                       │ • MZI Fringes & TVD    │                                       │
│                       │ • HOM Bunching & Dip   │                                       │
│                       └────────────┬───────────┘                                       │
└────────────────────────────────────┼───────────────────────────────────────────────────┘
                                     │  (DataFrames, Dicts, Matplotlib Figures)
                                     ▼
                  ┌──────────────────────────────────────────────┐
                  │   Person 5: UI & Streamlit Dashboard Core    │
                  │     st.pyplot(fig), st.dataframe(df)         │
                  └──────────────────────────────────────────────┘
```

---

## 📁 Package Structure

```
quantumqiskil/
├── qiskitintegration/             # Core implementation package
│   ├── __init__.py                # Unified package exports & versioning
│   ├── converters.py              # Optical matrices, phase conventions, Euler ZYZ & mode mappings
│   ├── circuit_builder.py         # QiskitOpticalCircuit: MZI, HOM 2-qubit, and N-mode networks
│   ├── simulator.py               # DigitalQuantumEngine: Statevector and AerSimulator execution
│   ├── benchmarks.py              # QuantumBenchmarks: TVD, Bhattacharyya fidelity, gate counts
│   ├── visuals.py                 # Matplotlib plotting routines (Fringes, HOM dip, Histograms)
│   └── run_demo.py                # Local package shortcut runner
├── quanta_sim/
│   ├── __init__.py
│   └── quantum_bridge/            # Canonical project alias forwarding to qiskitintegration
│       └── __init__.py
├── artifacts/                     # Generated publication-quality figures (PNG)
│   ├── mzi_circuit.png
│   ├── mzi_probability_comparison.png
│   ├── mzi_interference_sweep.png
│   ├── hom_circuit.png
│   ├── hom_dip_curve.png
│   └── circuit_gate_breakdown.png
└── run_demo.py                    # Root automated verification demo script
```

---

## 📐 Mathematical Formalism & Physics Mappings

### 1. Spatial Mode to Qubit Encodings
- **Single-Qubit (2 Modes)**:
  $$\text{Mode } 0 \to |0\rangle, \quad \text{Mode } 1 \to |1\rangle$$
- **Dense Binary Encoding ($N$ Modes)**:
  $$\text{Mode } k \to |\text{binary}(k)\rangle, \quad \text{requires } \lceil\log_2 N\rceil \text{ qubits.}$$
- **Dual-Rail / Unary Occupation ($N$ Modes)**:
  $$\text{Mode } k \to |0 \dots 0 1_k 0 \dots 0\rangle, \quad \text{requires } N \text{ qubits.}$$

### 2. Beam Splitter Phase Conventions
Lossless beam splitter transformations $\begin{pmatrix} b_0 \\ b_1 \end{pmatrix} = U_{BS} \begin{pmatrix} a_0 \\ a_1 \end{pmatrix}$:
1. **Real-Symmetric / Hadamard (`BeamSplitterConvention.REAL_SYMMETRIC`)**:
   $$U_{BS} = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix} = H$$
2. **Imaginary-Symmetric / Dielectric Plate (`BeamSplitterConvention.IMAGINARY_SYMMETRIC`)**:
   $$U_{BS} = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & i \\ i & 1 \end{pmatrix} = S H S$$
3. **Continuous Rotation (`BeamSplitterConvention.ROTATION`)**:
   $$U_{BS}(\theta) = \begin{pmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{pmatrix} = RY(2\theta)$$

### 3. Exact Analytical Euler Z-Y-Z Decomposition
Any arbitrary 2x2 optical unitary matrix $U \in U(2)$ is analytically decomposed into:
$$U = e^{i\alpha} R_Z(\beta) R_Y(\gamma) R_Z(\delta)$$
where:
- $\alpha = \frac{1}{2} \arg(\det U)$
- $\gamma = 2 \arctan2(|u'_{10}|, |u'_{00}|)$ with $U' = U e^{-i\alpha} \in SU(2)$
- $\beta = \arg(u'_{11}) + \arg(u'_{10})$
- $\delta = \arg(u'_{11}) - \arg(u'_{10})$
Verified numerically: $\|U - U_{\text{reconstructed}}\| < 10^{-10}$.

### 4. 2-Photon Hong-Ou-Mandel (HOM) Analogue
Fock states for 2 photons across 2 modes are mapped to 2 qubits:
- $|2, 0\rangle \longleftrightarrow |00\rangle$ (Both photons bunched in Mode 0)
- $|1, 1\rangle \longleftrightarrow |01\rangle$ (Coincidence detection: 1 photon in Mode 0, 1 in Mode 1)
- $|0, 2\rangle \longleftrightarrow |11\rangle$ (Both photons bunched in Mode 1)

At $\theta = 45^\circ$ (50:50 beam splitter):
$$|\psi_{\text{out}}\rangle = \frac{1}{\sqrt{2}} |00\rangle - \frac{1}{\sqrt{2}} |11\rangle$$
- Coincidence $P(|1, 1\rangle) = 0.0$ (Signature HOM Dip!)
- Quantum bunching $P(|2,0\rangle) + P(|0,2\rangle) = 1.0$ (100% Bunching)

---

## 🚀 Quickstart for Team Members

### For Person 1/2 (Optical Engine Integration)
```python
from qiskitintegration import QiskitOpticalCircuit, BeamSplitterConvention
import numpy as np

# Construct an MZI using your physics parameters
circuit = QiskitOpticalCircuit.build_mach_zehnder(
    phase_phi=np.pi / 3,
    input_mode=0,
    convention=BeamSplitterConvention.REAL_SYMMETRIC
)
```

### For Person 5 (Streamlit Dashboard Integration)
```python
import streamlit as st
from qiskitintegration import (
    QiskitOpticalCircuit,
    DigitalQuantumEngine,
    plot_circuit,
    plot_probability_comparison,
    plot_mzi_interference_sweep
)

# 1. Sweep parameter
sweep_res = QiskitOpticalCircuit.sweep_mach_zehnder(num_points=30, shots=2048)

# 2. Render plot directly in Streamlit
fig = plot_mzi_interference_sweep(sweep_res)
st.pyplot(fig)

# 3. Display interactive DataFrame
st.dataframe(sweep_res.to_dataframe())
```

---

## 📊 Verification & Benchmarking
Run the complete standalone demo:
```bash
py run_demo.py
```
This executes:
1. MZI single-point statevector & shot simulation.
2. Full 360° MZI phase sweep with fringe visibility calculation.
3. Machine-precision Z-Y-Z Euler decomposition check.
4. 2-Photon HOM quantum bunching & coincidence dip sweep.
5. 4-mode optical multiport dense simulation.
6. Export of all 7 visualization artifacts to the `artifacts/` folder.
