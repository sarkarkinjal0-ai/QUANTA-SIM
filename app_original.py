import sys
import os
import csv
import io

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

from optics.beam_splitter import beam_splitter
from core.state import basis_state
from core.unitary import apply_unitary
from core.probability import calculate_probabilities
from experiments.mzi import simulate_mzi, phase_sweep
from experiments.hom import hom_interference, hom_dip
from experiments.noise import simulate_noisy_mzi, add_beam_splitter_error
from quantum.comparison import compare_mzi
from visualization.circuit_plot import plot_optical_circuit
from visualization.plots import plot_unitary_magnitude


st.set_page_config(
    page_title="QUANTA-SIM",
    page_icon="⚛️",
    layout="wide"
)

SECTIONS = [
    "All Simulations",
    "Project Overview",
    "Beam Splitter",
    "Mach-Zehnder Interferometer",
    "Hong-Ou-Mandel Interference",
    "Noise & Imperfections",
    "Qiskit Comparison",
    "Optical Circuit Diagram",
    "Unitary Matrix Visualization",
    "Validation & Reports",
]

with st.sidebar:
    st.title("⚛️ QUANTA-SIM")
    st.caption("Photonic Quantum Simulator")
    st.divider()
    st.markdown("**Project Modules**")
    st.markdown(
        "- Beam Splitter\n"
        "- Mach–Zehnder Interferometer\n"
        "- Hong–Ou–Mandel Interference\n"
        "- Noise & Imperfections\n"
        "- Optical vs Qiskit Comparison"
    )
    st.divider()
    st.markdown("### Navigate to")
    section = st.radio(
        "Choose a section",
        SECTIONS,
        label_visibility="collapsed",
        key="navigation_section"
    )
    st.caption("Choose a section to focus the dashboard.")
    st.divider()
    st.title("Simulation Controls")
    transmission = st.slider(
        "Beam Splitter Transmission",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        key="sidebar_transmission"
    )


def show_section(name):
    """Show a section when it is selected, or show everything in All Simulations."""
    return section == "All Simulations" or section == name


st.title("QUANTA-SIM")
st.subheader("Quantum Circuit & Photonic Simulation Framework")
st.write(
    "Simulate optical quantum systems using unitary matrices, "
    "state vectors, and probability distributions."
)

if show_section("Project Overview"):
    st.markdown('<div id="project-overview"></div>', unsafe_allow_html=True)
    st.header("Project Overview")
    st.info(
        "QUANTA-SIM is an educational framework that connects photonic "
        "quantum experiments with mathematical simulation and digital quantum circuits."
    )

    overview_cols = st.columns(4)
    with overview_cols[0]:
        st.metric("Optical Experiments", "3")
        st.caption("Beam Splitter, MZI, HOM")
    with overview_cols[1]:
        st.metric("Noise Models", "2")
        st.caption("Phase and transmission errors")
    with overview_cols[2]:
        st.metric("Qiskit Validation", "Active")
        st.caption("Compare output probabilities")
    with overview_cols[3]:
        st.metric("Validation", "Active")
        st.caption("Probability conservation")

    st.subheader("Framework Capabilities")
    status_col1, status_col2, status_col3 = st.columns(3)
    with status_col1:
        st.success("Optical Simulation")
        st.caption("Beam splitters, phase shifts, and interference")
    with status_col2:
        st.success("Mathematical Validation")
        st.caption("Unitary matrices and probability conservation")
    with status_col3:
        st.success("Quantum Comparison")
        st.caption("Optical MZI results compared with Qiskit")

    with st.expander("📘 How to Use QUANTA-SIM"):
        st.markdown("""
        **1. Beam Splitter:** Adjust transmission and observe output probabilities.

        **2. Mach–Zehnder Interferometer:** Change phase and observe interference.

        **3. Hong–Ou–Mandel Interference:** Adjust photon distinguishability.

        **4. Noise & Imperfections:** Explore phase noise and transmission errors.

        **5. Optical vs Qiskit:** Compare optical and digital-circuit probabilities.

        **6. Validation & Reports:** Check probability conservation and download a CSV report.
        """)

if show_section("Beam Splitter"):
    st.divider()
    st.markdown('<div id="beam-splitter"></div>', unsafe_allow_html=True)
    st.caption("Experiment 1 of 3 — Single-photon beam splitter")
    st.header("Beam Splitter Simulation")

    matrix = beam_splitter(transmission)
    input_state = basis_state(0, 2)
    output_state = apply_unitary(input_state, matrix)
    probabilities = calculate_probabilities(output_state)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Beam Splitter Unitary")
        st.latex(r"""
        U =
        \begin{bmatrix}
        \sqrt{T} & \sqrt{1-T}\\
        \sqrt{1-T} & -\sqrt{T}
        \end{bmatrix}
        """)
        st.write("Transmission:", transmission)
        st.write("Matrix:")
        st.code(str(matrix))

    with col2:
        st.subheader("Output State")
        st.write("Input state:")
        st.code(str(input_state))
        st.write("Output state:")
        st.code(str(output_state))
        st.write("Probabilities:")
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(["Mode 0", "Mode 1"], probabilities)
        ax.set_ylabel("Probability")
        ax.set_ylim(0, 1.05)
        ax.set_title("Beam Splitter Output Probabilities")
        ax.grid(axis="y")
        st.pyplot(fig)
        plt.close(fig)

    st.subheader("Measurement Probabilities")
    prob_col1, prob_col2 = st.columns(2)
    with prob_col1:
        st.metric("Mode 0", f"{probabilities[0]:.3f}")
    with prob_col2:
        st.metric("Mode 1", f"{probabilities[1]:.3f}")

if show_section("Mach-Zehnder Interferometer"):
    st.divider()
    st.markdown('<div id="mzi"></div>', unsafe_allow_html=True)
    st.header("Mach-Zehnder Interferometer")
    st.write("Control the phase shift and observe quantum interference.")

    mzi_phase = st.slider(
        "Phase Shift (radians)", 0.0, float(2 * np.pi),
        0.0, 0.1, key="mzi_phase"
    )
    mzi_state, mzi_probabilities = simulate_mzi(mzi_phase)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("MZI Output State")
        st.code(str(mzi_state))
    with col2:
        st.subheader("MZI Probabilities")
        st.metric("Output Mode 0", f"{mzi_probabilities[0]:.3f}")
        st.metric("Output Mode 1", f"{mzi_probabilities[1]:.3f}")

    st.subheader("Interference Pattern")
    phases, output_0, output_1 = phase_sweep(points=100)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(phases, output_0, label="Output Mode 0")
    ax.plot(phases, output_1, label="Output Mode 1")
    ax.set_xlabel("Phase (radians)")
    ax.set_ylabel("Probability")
    ax.set_title("Mach-Zehnder Interference")
    ax.set_ylim(0, 1.05)
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)
    plt.close(fig)

if show_section("Hong-Ou-Mandel Interference"):
    st.divider()
    st.markdown('<div id="hom"></div>', unsafe_allow_html=True)
    st.header("Hong–Ou–Mandel (HOM) Interference")
    st.write(
        "Explore how photon distinguishability affects the output of "
        "two photons entering a 50:50 beam splitter."
    )
    st.caption(
        "Simplified model: 0 means indistinguishable photons; "
        "1 means fully distinguishable photons."
    )

    distinguishability = st.slider(
        "Distinguishability", 0.0, 1.0, 0.0, 0.05,
        key="hom_distinguishability"
    )
    hom_probabilities = hom_interference(distinguishability)

    st.subheader("Output probabilities")
    fig, ax = plt.subplots()
    ax.bar(["|2,0>", "|1,1>", "|0,2>"], hom_probabilities)
    ax.set_xlabel("Output photon distribution")
    ax.set_ylabel("Probability")
    ax.set_ylim(0, 0.55)
    ax.set_title("HOM Output Probabilities")
    st.pyplot(fig)
    plt.close(fig)

    st.metric("Coincidence probability P(|1,1>)", f"{hom_probabilities[1]:.3f}")
    st.write(f"Total probability: {np.sum(hom_probabilities):.3f}")

    st.subheader("HOM Interference Dip")
    dist_values, coincidence_values = hom_dip(points=100)
    fig, ax = plt.subplots()
    ax.plot(dist_values, coincidence_values)
    ax.scatter(
        [distinguishability], [hom_probabilities[1]],
        label="Selected setting"
    )
    ax.set_xlabel("Distinguishability")
    ax.set_ylabel("Coincidence probability")
    ax.set_title("Coincidence Probability vs Distinguishability")
    ax.set_ylim(-0.02, 0.55)
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)
    plt.close(fig)

if show_section("Noise & Imperfections"):
    st.divider()
    st.markdown('<div id="noise"></div>', unsafe_allow_html=True)
    st.header("Noise & Imperfections")
    st.subheader("Phase Noise Simulator")
    st.write(
        "Explore how random phase variations affect the output of a "
        "Mach–Zehnder interferometer."
    )

    base_phase = st.slider(
        "Base phase (radians)", 0.0, 6.28, 0.0, 0.1,
        key="noise_base_phase"
    )
    noise_strength = st.slider(
        "Phase noise strength", 0.0, 0.5, 0.1, 0.05,
        key="noise_strength"
    )

    if st.button("Run Noisy MZI Simulation", key="run_noisy_mzi"):
        noisy_phase, noisy_state, noisy_probabilities = simulate_noisy_mzi(
            phase=base_phase,
            noise_strength=noise_strength
        )
        st.write(f"Actual phase after noise: {noisy_phase:.4f} radians")
        st.write("Output state:")
        st.code(str(noisy_state))
        fig, ax = plt.subplots()
        ax.bar(["Output 0", "Output 1"], noisy_probabilities)
        ax.set_ylabel("Probability")
        ax.set_ylim(0, 1.05)
        ax.set_title("MZI Output with Phase Noise")
        st.pyplot(fig)
        plt.close(fig)

    st.divider()
    st.subheader("Beam-Splitter Imperfection Simulator")
    st.write(
        "Explore how manufacturing or calibration errors change a beam "
        "splitter's transmission."
    )
    ideal_transmission = st.slider(
        "Ideal transmission", 0.0, 1.0, 0.5, 0.05,
        key="ideal_transmission"
    )
    error_strength = st.slider(
        "Maximum transmission error", 0.0, 0.2, 0.05, 0.01,
        key="error_strength"
    )

    if st.button("Apply Beam-Splitter Error", key="apply_bs_error"):
        actual_transmission = add_beam_splitter_error(
            ideal_transmission, error_strength
        )
        actual_bs = beam_splitter(actual_transmission)
        input_state = basis_state(0, 2)
        output_state = apply_unitary(input_state, actual_bs)
        output_probabilities = calculate_probabilities(output_state)
        st.write(f"Ideal transmission: {ideal_transmission:.3f}")
        st.write(f"Actual transmission: {actual_transmission:.3f}")
        fig, ax = plt.subplots()
        ax.bar(["Output 0", "Output 1"], output_probabilities)
        ax.set_ylabel("Probability")
        ax.set_ylim(0, 1.05)
        ax.set_title("Output with Beam-Splitter Error")
        st.pyplot(fig)
        plt.close(fig)

if show_section("Qiskit Comparison"):
    st.divider()
    st.markdown('<div id="qiskit"></div>', unsafe_allow_html=True)
    st.header("Optical MZI vs Qiskit")
    st.write(
        "Compare output probabilities from the QUANTA-SIM optical model "
        "with an equivalent Qiskit quantum circuit."
    )

    comparison_phase = st.slider(
        "Comparison phase (radians)", 0.0, 6.28, 0.0, 0.1,
        key="comparison_phase"
    )
    optical_probs, qiskit_probs, matches = compare_mzi(comparison_phase)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Optical Model")
        st.write(f"Output 0: {optical_probs[0]:.4f}")
        st.write(f"Output 1: {optical_probs[1]:.4f}")
    with col2:
        st.subheader("Qiskit Model")
        st.write(f"Output 0: {qiskit_probs[0]:.4f}")
        st.write(f"Output 1: {qiskit_probs[1]:.4f}")

    fig, ax = plt.subplots()
    positions = np.arange(2)
    width = 0.35
    ax.bar(positions - width / 2, optical_probs, width, label="Optical")
    ax.bar(positions + width / 2, qiskit_probs, width, label="Qiskit")
    ax.set_xticks(positions)
    ax.set_xticklabels(["Output 0", "Output 1"])
    ax.set_ylabel("Probability")
    ax.set_ylim(0, 1.05)
    ax.set_title("Optical and Qiskit Probability Comparison")
    ax.legend()
    st.pyplot(fig)
    plt.close(fig)

    if matches:
        st.success("The optical and Qiskit probabilities match.")
    else:
        st.warning("The probabilities differ at this phase.")

if show_section("Optical Circuit Diagram"):
    st.divider()
    st.header("Optical Circuit Diagram")
    st.write(
        "Visual representation of the components in the "
        "Mach–Zehnder interferometer."
    )
    fig = plot_optical_circuit([
        "Input",
        "50:50 Beam Splitter",
        "Phase Shifter",
        "50:50 Beam Splitter",
        "Output"
    ])
    if fig is None:
        st.warning("The circuit plotting function did not return a figure.")
    else:
        st.pyplot(fig)
        plt.close(fig)

if show_section("Unitary Matrix Visualization"):
    st.divider()
    st.header("Unitary Matrix Visualization")
    st.write(
        "Visualize the magnitude of the complex matrix elements of a beam splitter."
    )
    transmission_for_matrix = st.slider(
        "Transmission for matrix visualization", 0.0, 1.0, 0.5, 0.05,
        key="matrix_transmission"
    )
    unitary_matrix = beam_splitter(transmission_for_matrix)
    st.subheader("Beam-Splitter Unitary Matrix")
    st.write(unitary_matrix)
    fig = plot_unitary_magnitude(unitary_matrix)
    st.pyplot(fig)
    plt.close(fig)

if show_section("Validation & Reports"):
    st.divider()
    st.markdown('<div id="validation"></div>', unsafe_allow_html=True)
    st.header("Validation & Reports")
    st.subheader("Probability Conservation Check")
    st.write(
        "Check whether the output probabilities sum to 1, as expected "
        "for a normalized quantum state."
    )

    check_phase = st.slider(
        "Phase for probability check (radians)", 0.0, 6.28, 1.57, 0.1,
        key="probability_check_phase"
    )
    _, check_probabilities = simulate_mzi(check_phase)
    total_probability = np.sum(check_probabilities)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total probability", f"{total_probability:.6f}")
    with col2:
        st.metric("Probability error", f"{abs(1.0 - total_probability):.2e}")

    if np.isclose(total_probability, 1.0):
        st.success("Probability is conserved: the total is approximately 1.")
    else:
        st.warning("The total probability differs from 1.")

    st.divider()
    st.subheader("Download Simulation Report")
    st.write(
        "Generate a CSV report containing the selected MZI settings "
        "and the results of a fresh simulation."
    )
    report_phase = st.slider(
        "Report phase (radians)", 0.0, 6.28, 1.57, 0.1,
        key="report_phase"
    )
    report_state, report_probabilities = simulate_mzi(report_phase)
    report_buffer = io.StringIO()
    report_writer = csv.writer(report_buffer)
    report_writer.writerow(["QUANTA-SIM Simulation Report"])
    report_writer.writerow(["Parameter", "Value"])
    report_writer.writerow(["Experiment", "Mach-Zehnder Interferometer"])
    report_writer.writerow(["Phase (radians)", report_phase])
    report_writer.writerow(["Output 0 probability", report_probabilities[0]])
    report_writer.writerow(["Output 1 probability", report_probabilities[1]])
    report_writer.writerow(["Total probability", np.sum(report_probabilities)])

    st.download_button(
        label="Download CSV Report",
        data=report_buffer.getvalue(),
        file_name="quanta_sim_report.csv",
        mime="text/csv"
    )

if section == "All Simulations":
    st.divider()
    st.caption(
        "All Simulations mode displays every experiment. Select an individual "
        "section in the sidebar to focus on that simulation."
    )
