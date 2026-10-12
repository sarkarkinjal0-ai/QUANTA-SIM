"""
QUANTA-SIM: Quantum Circuit Framework
Module: qiskitintegration.visuals
Role: 4/5 - Qiskit Integration (Digital Quantum Side)

This module provides publication-grade, interactive visualization tools ready for
Person 5's Streamlit dashboard and standalone scientific reporting:
1. Quantum circuit rendering (Matplotlib high-DPI and ASCII formats).
2. Side-by-side probability histograms: Optical Theory vs. Qiskit Sampled Results.
3. Mach-Zehnder Interferometer (MZI) phase sweep interference curves with residual / TVD subplots.
4. Hong-Ou-Mandel (HOM) 2-photon quantum bunching and coincidence dip curves.
5. Circuit complexity and gate breakdown charts.
"""

from typing import Dict, List, Optional, Tuple, Union
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit

from .benchmarks import BenchmarkReport, QuantumBenchmarks
from .circuit_builder import MZISweepResult, HOMSweepResult


# Apply modern, elegant styling parameters for scientific quantum figures
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial", "Helvetica"],
    "axes.edgecolor": "#CCCCCC",
    "axes.linewidth": 1.2,
    "grid.color": "#E5E5E5",
    "grid.linestyle": "--",
    "grid.alpha": 0.7,
})


def plot_circuit(
    circuit: QuantumCircuit,
    output: str = "mpl",
    filename: Optional[str] = None,
    scale: float = 1.0
) -> Union[plt.Figure, str]:
    """
    Render and export visual quantum circuit diagrams.

    Parameters:
        circuit: Target Qiskit QuantumCircuit.
        output: 'mpl' for Matplotlib Figure or 'text' for formatted ASCII string.
        filename: Optional path to save the generated image (PNG/PDF).
        scale: Scaling factor for mpl rendering.

    Returns:
        matplotlib.figure.Figure (if output='mpl') or str (if output='text').
    """
    if output == "text":
        ascii_art = circuit.draw(output="text")
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(str(ascii_art))
        return str(ascii_art)

    try:
        fig = circuit.draw(output="mpl", scale=scale, style="clifford")
    except Exception:
        # Fallback to default mpl style if custom style is missing
        fig = circuit.draw(output="mpl", scale=scale)

    if isinstance(fig, plt.Figure):
        if filename:
            fig.savefig(filename, dpi=300, bbox_inches="tight")
        return fig

    if filename and hasattr(fig, "savefig"):
        getattr(fig, "savefig")(filename, dpi=300, bbox_inches="tight")

    return fig  # type: ignore[return-value]


def plot_probability_comparison(
    optical_probs: Dict[int, float],
    qiskit_probs: Dict[int, float],
    shots: Optional[int] = None,
    title: str = "Optical Theory vs. Qiskit Measurement Statistics",
    filename: Optional[str] = None
) -> plt.Figure:
    """
    Generate a side-by-side grouped bar chart comparing theoretical optical probabilities
    against Qiskit digital quantum simulation frequencies.

    Includes:
    - Error bars representing theoretical shot noise confidence intervals: sigma = sqrt(p*(1-p)/N).
    - Statistical metrics badge (TVD, Classical Fidelity).
    """
    modes = sorted(optical_probs.keys() | qiskit_probs.keys())
    x = np.arange(len(modes))
    width = 0.35

    p_opt_vals = [float(optical_probs.get(m, 0.0)) for m in modes]
    p_qis_vals = [float(qiskit_probs.get(m, 0.0)) for m in modes]

    # Calculate TVD and Fidelity for display
    tvd = QuantumBenchmarks.total_variation_distance(optical_probs, qiskit_probs)
    fidelity = QuantumBenchmarks.classical_fidelity(optical_probs, qiskit_probs)

    # Shot noise error bars
    if shots is not None and shots > 0:
        yerr = [np.sqrt(max(p * (1.0 - p), 0.0) / float(shots)) for p in p_qis_vals]
    else:
        yerr = None

    fig, ax = plt.subplots(figsize=(8.5, 5.0), dpi=150)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FAFAFC")

    # Bar colors
    color_opt = "#1A73E8"   # Google Blue / Deep Optical Blue
    color_qis = "#9C27B0"   # Quantum Purple / Violet

    bars1 = ax.bar(x - width / 2.0, p_opt_vals, width, label="Optical Theory (Continuous)",
                   color=color_opt, alpha=0.88, edgecolor="#0D47A1", linewidth=1.2, zorder=3)
    bars2 = ax.bar(x + width / 2.0, p_qis_vals, width, yerr=yerr, capsize=4,
                   label=f"Qiskit Circuit ({shots} Shots)" if shots else "Qiskit Statevector (Exact)",
                   color=color_qis, alpha=0.88, edgecolor="#4A148C", linewidth=1.2, zorder=3)

    # Label values on top of bars
    for bar in bars1:
        h = bar.get_height()
        ax.annotate(f"{h:.3f}", xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
                    fontsize=9, fontweight="bold", color="#0D47A1")

    for bar in bars2:
        h = bar.get_height()
        ax.annotate(f"{h:.3f}", xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
                    fontsize=9, fontweight="bold", color="#4A148C")

    # Metrics badge text box
    stats_text = f"Total Variation Dist (TVD): {tvd:.4f}\nClassical Fidelity: {fidelity:.4f}"
    ax.text(0.98, 0.95, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment="top", horizontalalignment="right",
            bbox=dict(boxstyle="round,pad=0.6", facecolor="#FFFFFF", edgecolor="#BDBDBD", alpha=0.95))

    ax.set_xlabel("Optical Spatial Mode / Detector Port", fontsize=11, fontweight="bold", labelpad=8)
    ax.set_ylabel("Detection Probability", fontsize=11, fontweight="bold", labelpad=8)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=14, color="#212121")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Mode {m}" for m in modes], fontsize=10, fontweight="bold")
    ax.set_ylim(0.0, max(max(p_opt_vals + p_qis_vals) * 1.25, 1.05))
    ax.grid(axis="y", zorder=0)
    ax.legend(loc="upper left", framealpha=0.95, fontsize=10)

    plt.tight_layout()

    if filename:
        fig.savefig(filename, dpi=300, bbox_inches="tight")

    return fig


def plot_mzi_interference_sweep(
    sweep_result: MZISweepResult,
    title: str = "Mach-Zehnder Interferometer: Phase Sweep Interference Fringes",
    filename: Optional[str] = None
) -> plt.Figure:
    """
    Generate an MZI interference fringe plot featuring:
    1. Upper panel: Continuous theoretical sinusoidal curves overlaid with Qiskit sampled markers.
    2. Lower panel: Residual Total Variation Distance (TVD) per phase point.
    """
    phases = sweep_result.phases
    deg = np.degrees(phases)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(9.5, 7.0), dpi=150,
        gridspec_kw={"height_ratios": [3.2, 1.2]}, sharex=True
    )
    fig.patch.set_facecolor("#FFFFFF")
    ax1.set_facecolor("#FAFAFC")
    ax2.set_facecolor("#FAFAFC")

    color_m0 = "#00897B"   # Teal (Port 0)
    color_m1 = "#E53935"   # Crimson / Coral (Port 1)

    # Upper panel: Theoretical curves (smooth lines)
    ax1.plot(deg, sweep_result.optical_theory_p0, "-", color=color_m0, linewidth=2.5,
             label=f"Optical Theory P(Mode 0) [Vis={sweep_result.visibility_theory:.2f}]", zorder=2)
    ax1.plot(deg, sweep_result.optical_theory_p1, "--", color=color_m1, linewidth=2.5,
             label=f"Optical Theory P(Mode 1)", zorder=2)

    # Qiskit simulated data points (scatter markers)
    shot_label = f"Qiskit Sampled ({sweep_result.shots} shots)" if sweep_result.shots else "Qiskit Exact"
    ax1.scatter(deg, sweep_result.qiskit_measured_p0, color=color_m0, marker="o", s=38,
                edgecolor="#004D40", linewidth=1.2, label=f"{shot_label} - Mode 0", zorder=4)
    ax1.scatter(deg, sweep_result.qiskit_measured_p1, color=color_m1, marker="s", s=38,
                edgecolor="#B71C1C", linewidth=1.2, label=f"{shot_label} - Mode 1", zorder=4)

    ax1.set_ylabel("Transmission Probability", fontsize=11, fontweight="bold")
    ax1.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax1.set_ylim(-0.05, 1.08)
    ax1.grid(True, zorder=0)
    ax1.legend(loc="upper right", framealpha=0.92, fontsize=9.5)

    # Lower panel: Residual TVD error
    ax2.plot(deg, sweep_result.tvd_per_point, "-o", color="#3949AB", markersize=3.5,
             linewidth=1.5, label="TVD per point", zorder=3)
    ax2.axhline(sweep_result.mean_tvd, color="#FF6F00", linestyle=":", linewidth=1.8,
                label=f"Mean TVD = {sweep_result.mean_tvd:.4f}", zorder=3)

    ax2.set_xlabel("Phase Shift Angle φ (degrees)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("TVD (|ΔP|/2)", fontsize=10, fontweight="bold")
    ax2.set_xlim(0, 360)
    ax2.set_xticks(np.arange(0, 361, 45))
    ax2.set_ylim(0.0, max(np.max(sweep_result.tvd_per_point) * 1.4, 0.05))
    ax2.grid(True, zorder=0)
    ax2.legend(loc="upper right", framealpha=0.92, fontsize=9)

    plt.tight_layout()

    if filename:
        fig.savefig(filename, dpi=300, bbox_inches="tight")

    return fig


def plot_hom_dip(
    hom_result: HOMSweepResult,
    title: str = "Hong-Ou-Mandel (HOM) Effect: Quantum Bunching & Coincidence Dip",
    filename: Optional[str] = None
) -> plt.Figure:
    """
    Generate the Hong-Ou-Mandel 2-photon interference plot illustrating:
    1. The signature coincidence dip P(|1, 1>) dipping to 0 at 50:50 mixing (theta = pi/4).
    2. Quantum bunching into states |2, 0> and |0, 2> rising symmetrically to 50% each.
    3. Comparison against the classical distinguishable threshold (P_coinc = 0.5).
    """
    thetas_deg = np.degrees(hom_result.thetas)

    fig, ax = plt.subplots(figsize=(9.0, 5.5), dpi=150)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FAFAFC")

    c_coinc = "#D32F2F"   # Coincidence Red
    c_b00 = "#1976D2"     # Mode 0 Bunching Blue
    c_b11 = "#388E3C"     # Mode 1 Bunching Green

    # Theoretical curves
    ax.plot(thetas_deg, hom_result.theory_coincidence, "-", color=c_coinc, linewidth=2.8,
            label="Theory Coincidence P(|1,1>)", zorder=2)
    ax.plot(thetas_deg, hom_result.theory_bunched_00, "--", color=c_b00, linewidth=2.2,
            label="Theory Bunched P(|2,0>)", zorder=2)
    ax.plot(thetas_deg, hom_result.theory_bunched_11, ":", color=c_b11, linewidth=2.2,
            label="Theory Bunched P(|0,2>)", zorder=2)

    # Qiskit sampled data points
    ax.scatter(thetas_deg, hom_result.qiskit_coincidence, color=c_coinc, marker="v", s=45,
               edgecolor="#7F0000", linewidth=1.2, label=f"Qiskit Coincidence |01>", zorder=4)
    ax.scatter(thetas_deg, hom_result.qiskit_bunched_00, color=c_b00, marker="o", s=35,
               edgecolor="#0D47A1", linewidth=1.0, label="Qiskit Bunched |00>", zorder=4)
    ax.scatter(thetas_deg, hom_result.qiskit_bunched_11, color=c_b11, marker="s", s=35,
               edgecolor="#1B5E20", linewidth=1.0, label="Qiskit Bunched |11>", zorder=4)

    # Classical limit horizontal line
    ax.axhline(0.5, color="#757575", linestyle="-.", linewidth=1.5,
               label="Classical Distinguishable Threshold (50%)", zorder=1)

    # Highlight 50:50 dip point
    ax.axvline(45.0, color="#FF9800", linestyle=":", linewidth=1.8, zorder=1)
    ax.annotate("HOM Dip Minimum (θ=45° / 50:50 BS)\nP(|1,1>) → 0 (Complete Bunching)",
                xy=(45.0, 0.0), xytext=(48.0, 0.22),
                arrowprops=dict(facecolor="#D32F2F", shrink=0.08, width=1.5, headwidth=8),
                fontsize=9.5, fontweight="bold", color="#B71C1C",
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#FFEBEE", edgecolor="#EF9A9A", alpha=0.95))

    ax.set_xlabel("Beam Splitter Angle θ (degrees)", fontsize=11, fontweight="bold")
    ax.set_ylabel("State Probability", fontsize=11, fontweight="bold")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_xlim(0, 90)
    ax.set_xticks(np.arange(0, 91, 15))
    ax.set_ylim(-0.04, 1.05)
    ax.grid(True, zorder=0)
    ax.legend(loc="upper right", framealpha=0.92, fontsize=9)

    plt.tight_layout()

    if filename:
        fig.savefig(filename, dpi=300, bbox_inches="tight")

    return fig


def plot_gate_breakdown(
    report: BenchmarkReport,
    filename: Optional[str] = None
) -> plt.Figure:
    """
    Generate a visual donut chart of circuit gate distribution and circuit depth.
    """
    gate_dict = {k: v for k, v in report.gate_breakdown.items() if k not in ("barrier", "measure")}
    if not gate_dict:
        gate_dict = {"identity": 1}

    labels = list(gate_dict.keys())
    counts = list(gate_dict.values())
    cmap = plt.get_cmap("Set2")
    colors = [tuple(c) for c in cmap(np.linspace(0, 1, len(labels)))]

    fig, ax = plt.subplots(figsize=(6.5, 4.5), dpi=150)
    fig.patch.set_facecolor("#FFFFFF")

    wedges, texts, autotexts = ax.pie(
        counts, labels=labels, autopct="%1.1f%%",
        startangle=140, colors=colors,
        textprops=dict(color="#212121", fontweight="bold"),
        wedgeprops=dict(width=0.45, edgecolor="#FFFFFF", linewidth=2)
    )

    # Center circle annotation
    center_text = f"Depth: {report.circuit_depth}\nGates: {report.total_gates}\nQubits: {report.num_qubits}"
    ax.text(0, 0, center_text, ha="center", va="center", fontsize=10, fontweight="bold", color="#37474F")

    ax.set_title("Quantum Circuit Gate Composition", fontsize=12, fontweight="bold", pad=14)
    plt.tight_layout()

    if filename:
        fig.savefig(filename, dpi=300, bbox_inches="tight")

    return fig
