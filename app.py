"""QUANTA-SIM: integrated photonic quantum simulator Streamlit application."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from optical_builder.utils.builder_tab import render_integrated_builder_tab
from photon_noise_engine import PhotonNoiseEngine

st.set_page_config(page_title="QUANTA-SIM", page_icon="⚛️", layout="wide")
st.title("⚛️ QUANTA-SIM")
st.caption("Photonic quantum circuits · Interference · Noise · Digital quantum validation")

builder_tab, experiments_tab, qiskit_tab, about_tab = st.tabs(
    ["Circuit Builder", "Experiments & Noise", "Qiskit Comparison", "About & Validation"]
)

with builder_tab:
    render_integrated_builder_tab()

with experiments_tab:
    st.header("Interferometry & Photon Experiments")
    st.write("Explore a Mach–Zehnder interferometer (MZI) and Hong–Ou–Mandel (HOM) two-photon interference.")
    col1, col2 = st.columns(2)
    with col1:
        reflectivity = st.slider("Nominal beam-splitter reflectivity", 0.0, 1.0, 0.5, 0.01, key="exp_reflectivity")
        shots = st.select_slider("Measurement shots", [128, 512, 1024, 4096, 8192], value=1024, key="exp_shots")
    with col2:
        noisy = st.toggle("Enable optical imperfections", value=False, key="exp_noisy")
        phase_sigma = st.slider("Phase drift σ (rad)", 0.0, 1.0, 0.10, 0.01, key="exp_phase_sigma") if noisy else 0.0
        reflectivity_sigma = st.slider("Reflectivity error σ", 0.0, 0.2, 0.02, 0.005, key="exp_ref_sigma") if noisy else 0.0

    engine = PhotonNoiseEngine(seed=42)
    phases = np.linspace(0.0, 2 * np.pi, 100)
    sweep = engine.mzi_sweep(
        phases, reflectivity=reflectivity, phase_drift_std=phase_sigma,
        reflectivity_std=reflectivity_sigma, noisy=noisy, shots=shots,
    )
    st.subheader("Mach–Zehnder interference sweep")
    plot_data = {"Ideal P(mode 0)": sweep["p0_ideal"], "Ideal P(mode 1)": sweep["p1_ideal"]}
    if noisy:
        plot_data.update({"Noisy P(mode 0)": sweep["p0_noisy"], "Noisy P(mode 1)": sweep["p1_noisy"]})
    st.line_chart(pd.DataFrame(plot_data, index=np.round(phases, 4)))
    denom = max(1e-12, float(np.max(sweep["p0_noisy"]) + np.min(sweep["p0_noisy"])))
    visibility = float((np.max(sweep["p0_noisy"]) - np.min(sweep["p0_noisy"])) / denom)
    st.metric("P(mode 0) visibility", f"{visibility:.4f}")
    st.caption("The plotted values are theoretical probabilities. Finite-shot samples are shown for the HOM experiment below.")

    st.subheader("Hong–Ou–Mandel (HOM) interference")
    hom = engine.simulate_hom(reflectivity=reflectivity, noisy=noisy,
                              reflectivity_std=reflectivity_sigma, shots=shots)
    h1, h2 = st.columns(2)
    h1.dataframe(pd.DataFrame({"Output Fock state": list(hom["probabilities"].keys()),
                               "Probability": list(hom["probabilities"].values())}), hide_index=True, use_container_width=True)
    h2.write("Sampled counts")
    h2.json(hom["sampled_counts"])
    st.caption("For indistinguishable photons at an ideal 50:50 beam splitter, the |1,1⟩ coincidence probability should be approximately zero.")

with qiskit_tab:
    st.header("Optical model vs Qiskit Aer")
    st.write("Compare the optical Photon & Noise Engine against the shot-based digital quantum circuit using the same MZI phase and beam-splitter convention.")
    phase = st.slider("MZI internal phase φ (rad)", 0.0, float(2 * np.pi), float(np.pi / 3), 0.01, key="qiskit_phase")
    q_reflectivity = st.slider("Beam-splitter reflectivity", 0.0, 1.0, 0.5, 0.01, key="qiskit_reflectivity")
    q_shots = st.select_slider("Qiskit measurement shots", [512, 1024, 2048, 4096, 8192], value=2048, key="qiskit_shots")
    if st.button("Run Qiskit benchmark", type="primary", key="run_qiskit_benchmark"):
        try:
            from photon_qiskit_bridge import benchmark_mzi_with_qiskit
            with st.spinner("Running optical and Qiskit simulations..."):
                result = benchmark_mzi_with_qiskit(
                    phase=phase, reflectivity=q_reflectivity, shots=q_shots,
                    noisy_optical=False, seed=42,
                )
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Variation Distance", f"{result['tvd']:.5f}")
            m2.metric("Classical Fidelity", f"{result['classical_fidelity']:.5f}")
            m3.metric("Hellinger Distance", f"{result['hellinger_distance']:.5f}")
            comparison = pd.DataFrame({
                "Optical theory": result["optical_probabilities"],
                "Qiskit sampled": result["qiskit_probabilities"],
            }).fillna(0.0)
            comparison.index = [f"Mode {i}" for i in comparison.index]
            st.subheader("Probability comparison")
            st.bar_chart(comparison)
            st.subheader("Qiskit circuit")
            from qiskitintegration import plot_circuit, plot_gate_breakdown
            st.pyplot(plot_circuit(result["circuit"]))
            st.subheader("Circuit resource breakdown")
            st.pyplot(plot_gate_breakdown(result["report"]))
            with st.expander("Raw benchmark details"):
                st.json({"counts": result["counts"], "report": result["report"].to_dict()})
        except Exception as exc:
            st.error("The Qiskit benchmark could not run. Check that the project dependencies are installed and compatible.")
            st.exception(exc)
    else:
        st.info("Choose the phase and shot count, then click **Run Qiskit benchmark**. Qiskit imports are lazy so the other tabs can still be used if Qiskit is not installed yet.")

with about_tab:
    st.header("Project architecture")
    st.markdown("""
    **Member 1 — Core Physics & Mathematics:** `core_engine.py` provides state vectors, unitary transformations, and Born-rule probabilities.

    **Member 2 — Optical Components & Builder:** `optical_builder/` provides the interactive component builder and circuit schematic. The separate original Member 2 source archive was not included among the uploaded files; this integrated builder was supplied within Member 4's archive.

    **Member 3 — Interferometry & Experiments:** `physics_experiments.py` orchestrates MZI and HOM experiments.

    **Member 4 — Photon & Noise Engine:** `photon_noise_engine.py` handles photon evolution, Fock-state interference, optical imperfections, and finite-shot sampling.

    **Member 5 — Qiskit Integration:** `qiskitintegration/` builds digital circuits, runs Qiskit Aer, and calculates benchmark metrics.

    **Member 6 — UI, Visualization & Integration:** this Streamlit app connects the modules and presents results.
    """)
    st.subheader("Numerical validation")
    if st.button("Run integration smoke tests"):
        try:
            import subprocess, sys
            proc = subprocess.run([sys.executable, "test_integration.py"], capture_output=True, text=True, timeout=120)
            if proc.returncode == 0:
                st.success("Integration smoke tests passed.")
            else:
                st.error("Integration smoke tests reported an error.")
            st.code(proc.stdout + ("\n" + proc.stderr if proc.stderr else ""))
        except Exception as exc:
            st.exception(exc)
