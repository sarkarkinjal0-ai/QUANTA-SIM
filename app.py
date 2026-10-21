
"""QUANTA-SIM: integrated photonic quantum simulator Streamlit application."""
from __future__ import annotations

import subprocess
import sys

import numpy as np
import pandas as pd
import streamlit as st

from optical_builder.utils.builder_tab import render_integrated_builder_tab
from photon_noise_engine import PhotonNoiseEngine
from quantum_animations import render_animations_lab


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="QUANTA-SIM",
    page_icon="⚛️",
    layout="wide",
)

st.title("⚛️ QUANTA-SIM")
st.caption(
    "Photonic quantum circuits · Interference · Noise · "
    "Digital quantum validation"
)

st.markdown(
    """
    QUANTA-SIM is an interactive software environment for exploring
    photonic quantum circuits, optical interference, modeled noise,
    and comparisons with digital quantum simulation.
    """
)

builder_tab, experiments_tab, qiskit_tab, about_tab, tutorial_tab, animations_tab = st.tabs(
    [
        "Circuit Builder",
        "Experiments & Noise",
        "Qiskit Comparison",
        "About",
        "Tutorial",
        "Animations Lab",
    ]
)


# ============================================================
# TAB 1: CIRCUIT BUILDER
# ============================================================

with builder_tab:
    render_integrated_builder_tab()


# ============================================================
# TAB 2: EXPERIMENTS & NOISE
# ============================================================

with experiments_tab:
    st.header("Interferometry & Photon Experiments")

    st.write(
        "Explore a Mach–Zehnder interferometer (MZI) and "
        "Hong–Ou–Mandel (HOM) two-photon interference."
    )

    col1, col2 = st.columns(2)

    with col1:
        reflectivity = st.slider(
            "Nominal beam-splitter reflectivity",
            0.0,
            1.0,
            0.5,
            0.01,
            key="exp_reflectivity",
            help="Nominal reflectivity used by the optical model.",
        )

        shots = st.select_slider(
            "Measurement shots",
            [128, 512, 1024, 4096, 8192],
            value=1024,
            key="exp_shots",
            help="Number of simulated measurement trials where supported.",
        )

    with col2:
        noisy = st.toggle(
            "Enable optical imperfections",
            value=False,
            key="exp_noisy",
        )

        phase_sigma = (
            st.slider(
                "Phase drift σ (rad)",
                0.0,
                1.0,
                0.10,
                0.01,
                key="exp_phase_sigma",
            )
            if noisy
            else 0.0
        )

        reflectivity_sigma = (
            st.slider(
                "Reflectivity error σ",
                0.0,
                0.2,
                0.02,
                0.005,
                key="exp_ref_sigma",
            )
            if noisy
            else 0.0
        )

    engine = PhotonNoiseEngine(seed=42)
    phases = np.linspace(0.0, 2 * np.pi, 100)

    sweep = engine.mzi_sweep(
        phases,
        reflectivity=reflectivity,
        phase_drift_std=phase_sigma,
        reflectivity_std=reflectivity_sigma,
        noisy=noisy,
        shots=shots,
    )

    st.subheader("Mach–Zehnder interference sweep")

    plot_data = {
        "Ideal P(mode 0)": sweep["p0_ideal"],
        "Ideal P(mode 1)": sweep["p1_ideal"],
    }

    if noisy:
        plot_data.update(
            {
                "Noisy P(mode 0)": sweep["p0_noisy"],
                "Noisy P(mode 1)": sweep["p1_noisy"],
            }
        )

    st.line_chart(
        pd.DataFrame(plot_data, index=np.round(phases, 4))
    )

    denominator = max(
        1e-12,
        float(
            np.max(sweep["p0_noisy"])
            + np.min(sweep["p0_noisy"])
        ),
    )

    visibility = float(
        (
            np.max(sweep["p0_noisy"])
            - np.min(sweep["p0_noisy"])
        )
        / denominator
    )

    st.metric("P(mode 0) visibility", f"{visibility:.4f}")

    st.caption(
        "The MZI chart displays probabilities calculated by the model. "
        "The HOM section below also displays simulated sampled counts."
    )

    st.subheader("Hong–Ou–Mandel (HOM) interference")

    hom = engine.simulate_hom(
        reflectivity=reflectivity,
        noisy=noisy,
        reflectivity_std=reflectivity_sigma,
        shots=shots,
    )

    h1, h2 = st.columns(2)

    h1.dataframe(
        pd.DataFrame(
            {
                "Output Fock state": list(hom["probabilities"].keys()),
                "Probability": list(hom["probabilities"].values()),
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    h2.write("Sampled counts")
    h2.json(hom["sampled_counts"])

    st.caption(
        "For indistinguishable photons entering an ideal 50:50 beam "
        "splitter under the usual HOM conditions, the |1,1⟩ coincidence "
        "probability should be approximately zero."
    )


# ============================================================
# TAB 3: QISKIT COMPARISON
# ============================================================

with qiskit_tab:
    st.header("Optical Model vs Qiskit Aer")

    st.write(
        "Compare the optical Photon & Noise Engine against a shot-based "
        "digital quantum simulation using the project's MZI model."
    )

    phase = st.slider(
        "MZI internal phase φ (rad)",
        0.0,
        float(2 * np.pi),
        float(np.pi / 3),
        0.01,
        key="qiskit_phase",
    )

    q_reflectivity = st.slider(
        "Beam-splitter reflectivity",
        0.0,
        1.0,
        0.5,
        0.01,
        key="qiskit_reflectivity",
    )

    q_shots = st.select_slider(
        "Qiskit measurement shots",
        [512, 1024, 2048, 4096, 8192],
        value=2048,
        key="qiskit_shots",
    )

    if st.button(
        "Run Qiskit benchmark",
        type="primary",
        key="run_qiskit_benchmark",
    ):
        try:
            from photon_qiskit_bridge import benchmark_mzi_with_qiskit

            with st.spinner(
                "Running optical and Qiskit simulations..."
            ):
                result = benchmark_mzi_with_qiskit(
                    phase=phase,
                    reflectivity=q_reflectivity,
                    shots=q_shots,
                    noisy_optical=False,
                    seed=42,
                )

            metric1, metric2, metric3 = st.columns(3)

            metric1.metric(
                "Total Variation Distance",
                f"{result['tvd']:.5f}",
            )
            metric2.metric(
                "Classical Fidelity",
                f"{result['classical_fidelity']:.5f}",
            )
            metric3.metric(
                "Hellinger Distance",
                f"{result['hellinger_distance']:.5f}",
            )

            comparison = pd.DataFrame(
                {
                    "Optical theory": result["optical_probabilities"],
                    "Qiskit sampled": result["qiskit_probabilities"],
                }
            ).fillna(0.0)

            comparison.index = [
                f"Mode {i}" for i in comparison.index
            ]

            st.subheader("Probability comparison")
            st.bar_chart(comparison)

            from qiskitintegration import (
                plot_circuit,
                plot_gate_breakdown,
            )

            st.subheader("Qiskit circuit")
            st.pyplot(plot_circuit(result["circuit"]))

            st.subheader("Circuit resource breakdown")
            st.pyplot(plot_gate_breakdown(result["report"]))

            with st.expander("Raw benchmark details"):
                st.json(
                    {
                        "counts": result["counts"],
                        "report": result["report"].to_dict(),
                    }
                )

        except Exception as exc:
            st.error(
                "The Qiskit benchmark could not run. Check the installed "
                "dependencies and their compatibility."
            )
            st.exception(exc)

    else:
        st.info(
            "Choose the phase and shot count, then click "
            "**Run Qiskit benchmark**. Qiskit is imported only when "
            "the benchmark is requested."
        )


# ============================================================
# TAB 4: ABOUT
# ============================================================

with about_tab:
    st.header("ABOUT QUANTA-SIM")

    st.markdown(
        """
        ## 1. Overview

        **QUANTA-SIM** is a software environment for exploring selected
        concepts in photonic quantum information. It combines an
        interactive circuit builder, optical interference experiments,
        a photon-and-noise simulation engine, and an optional comparison
        with a digital quantum simulator.

        Photonic quantum computing uses optical modes and photon states
        to represent and process quantum information.

        QUANTA-SIM supports learning, numerical exploration, and
        computational experiments. Its outputs are generated by software
        models, not by direct measurements from physical laboratory equipment.

        ## 2. Main objectives

        - Explore optical circuit components and their arrangements.
        - Investigate phase-dependent interference.
        - Examine selected single- and two-photon effects.
        - Study modeled optical imperfections.
        - Compare selected optical-model outputs with digital simulation.
        - Support structured and reproducible computational experiments.
        - Understand how model assumptions affect numerical results.

        ## 3. How the application works

        A typical simulation follows this sequence:

        1. The user chooses circuit components or experiment parameters.
        2. The relevant module constructs or evaluates the model.
        3. Optical transformations and phase settings are applied.
        4. The simulator calculates output probabilities or other results.
        5. Where supported, finite-shot sampling generates simulated counts.
        6. Streamlit displays the resulting charts, tables, and metrics.

        The precise calculations depend on the selected module and its
        implementation.

        ## 4. Quantum-state representation

        A quantum state can be expressed as a superposition of basis states.
        """
    )

    st.latex(r"\lvert\psi\rangle = \sum_j c_j \lvert j\rangle")

    st.markdown(
        """
        Here, cⱼ is the complex probability amplitude of basis state j.
        A normalized quantum state satisfies the following condition:
        """
    )

    st.latex(r"\sum_j |c_j|^2 = 1")

    st.markdown(
        """
        In photonic systems, Fock states describe photon occupation in
        optical modes. For example, |1,1⟩ represents one photon in each
        of two modes. The state representation and supported dimensions
        depend on the relevant implementation.
        """
    )

    st.markdown("## 5. Quantum transformations")

    st.markdown(
        "An ideal quantum transformation can be represented as:"
    )
    st.latex(
        r"\lvert\psi_{\mathrm{out}}\rangle"
        r" = U\lvert\psi_{\mathrm{in}}\rangle"
    )

    st.markdown(
        """
        U denotes the transformation applied to the modeled state.
        For an ideal unitary transformation, the mathematical condition is:
        """
    )
    st.latex(r"U^\dagger U = I")

    st.markdown(
        """
        Here, U† is the conjugate transpose of U, and I is the identity
        operator. This condition describes ideal unitary evolution; it
        does not imply that all real optical devices are lossless.
        """
    )

    st.markdown("## 6. Measurement and the Born rule")

    st.markdown(
        "The probability of measuring basis state j is given by:"
    )
    st.latex(
        r"P(j) = |\langle j \mid \psi \rangle|^2 = |c_j|^2"
    )

    st.markdown(
        """
        These probabilities describe the predicted distribution of
        measurement outcomes. A finite number of simulated trials may
        produce observed frequencies that differ from the theoretical
        probabilities.
        """
    )

    st.markdown("## 7. Beam splitters and phase shifters")

    st.markdown(
        """
        A beam splitter mixes optical modes. For an ideal lossless beam
        splitter, reflectivity R and transmissivity T obey:
        """
    )
    st.latex(r"R + T = 1")

    st.markdown(
        """
        A phase shifter changes the phase of an optical amplitude.
        Relative phase can cause constructive or destructive interference.

        The component matrices and exact phase conventions used by
        QUANTA-SIM are determined by its implementation. Real devices
        may also exhibit absorption, scattering, and other losses that
        are not necessarily represented by this ideal relation.
        """
    )

    st.markdown("## 8. Mach–Zehnder interferometer (MZI)")

    st.markdown(
        """
        A Mach–Zehnder interferometer splits optical paths, introduces
        a relative phase, and recombines the paths. Its output probabilities
        depend on phase, beam-splitter settings, and the model's conventions.

        In the Experiments & Noise tab, QUANTA-SIM sweeps the phase variable
        over a range and plots the modeled probabilities for two output modes.

        Questions to explore:

        - How do output probabilities change with phase?
        - How does reflectivity affect the output curve?
        - How do modeled imperfections affect the interference pattern?
        - Are the output probabilities consistent with the model's
          expected normalization?
        """
    )

    st.markdown("## 9. Hong–Ou–Mandel (HOM) interference")

    st.markdown(
        """
        The Hong–Ou–Mandel effect is a two-photon interference phenomenon.
        For indistinguishable photons entering separate inputs of an ideal
        50:50 beam splitter under the usual conditions, the photons tend
        to exit together, suppressing coincidences with one photon in each
        output mode.

        The two-mode coincidence state is commonly written as:
        """
    )
    st.latex(r"\lvert 1,1\rangle")

    st.markdown(
        """
        The application presents modeled output-state probabilities and
        sampled counts. Actual experiments can also depend on photon
        distinguishability, losses, detector efficiency, and timing
        mismatch. Do not assume those effects are included unless the
        implementation explicitly models them.
        """
    )

    st.markdown("## 10. Noise and finite-shot sampling")

    st.markdown(
        """
        The Experiments & Noise tab provides controls for modeled phase
        drift and reflectivity variation. These settings are assumptions
        of the simulation, not automatically calibrated properties of
        real optical equipment.

        For an event with probability p measured over N independent trials,
        the expected number of occurrences is:
        """
    )
    st.latex(r"\mathbb{E}[n] = Np")

    st.markdown(
        "For independent Bernoulli trials, the standard deviation of the "
        "estimated probability is:"
    )
    st.latex(
        r"\sigma_{\hat p} = \sqrt{\frac{p(1-p)}{N}}"
    )

    st.markdown(
        """
        Increasing the shot count generally reduces statistical fluctuations.
        It does not correct an inaccurate model or account for physical
        effects that the simulator does not represent.
        """
    )

    st.markdown("## 11. Qiskit comparison")

    st.markdown(
        """
        The Qiskit Comparison tab calls the project's
        `benchmark_mzi_with_qiskit` function. It displays optical-model
        probabilities, sampled Qiskit probabilities, comparison metrics,
        and information about the constructed digital circuit.

        The reported metrics are:
        """
    )

    st.markdown("**Total Variation Distance (TVD)**")
    st.latex(
        r"D_{\mathrm{TV}}(P,Q)"
        r" = \frac{1}{2}\sum_i |P_i-Q_i|"
    )

    st.markdown(
        """
        TVD measures the difference between two probability distributions.
        It is zero when the distributions are identical.
        """
    )

    st.markdown("**Classical fidelity**")

    st.latex(
        r"F(P,Q) = \left(\sum_i \sqrt{P_i Q_i}\right)^2"
    )

    st.markdown(
        """
        This is one common definition of classical fidelity for
        probability distributions. Check the project's implementation
        to confirm the exact convention used by its reported metric.
        """
    )

    st.markdown("**Hellinger distance**")

    st.latex(
        r"H(P,Q) = \frac{1}{\sqrt{2}}"
        r"\sqrt{\sum_i(\sqrt{P_i}-\sqrt{Q_i})^2}"
    )

    st.markdown(
        """
        This is a common Hellinger-distance convention. The implementation
        should be checked before comparing values with other software.

        Meaningful comparisons require compatible assumptions, output
        mappings, phase conventions, and probability normalization.
        Agreement between two simulations does not independently prove
        that either model matches physical reality.
        """
    )

    st.markdown("## 12. Software architecture")

    st.markdown(
        """
        | File or directory | Role in the application |
        |---|---|
        | `app.py` | Streamlit interface and navigation |
        | `optical_builder/` | Interactive circuit builder and utilities |
        | `photon_noise_engine.py` | Photon/noise simulation interface used by the experiments tab |
        | `core_engine.py` | Core physics functionality identified in the project documentation |
        | `physics_experiments.py` | Experiment-related functionality identified in the project documentation |
        | `photon_qiskit_bridge.py` | Interface called by the Qiskit benchmark |
        | `qiskitintegration/` | Digital-circuit visualization and resource reporting |
        | `test_integration.py` | Integration smoke-test script |

        These descriptions summarize the roles indicated by the project
        structure and current application code. They do not guarantee
        that every possible physical process or research feature is implemented.
        """
    )

    st.markdown("## 13. Capabilities and limitations")

    st.markdown(
        """
        **Appropriate uses**

        - Learning photonic quantum concepts.
        - Exploring parameters in implemented models.
        - Comparing probability distributions.
        - Studying sensitivity to selected modeled imperfections.
        - Developing hypotheses for further analysis.

        **Important limitations**

        - QUANTA-SIM is a software simulator, not a physical quantum-photonics
          laboratory or hardware-control system.
        - A noise model may not represent all sources of experimental noise.
        - Finite-shot sampling does not guarantee agreement with experiments.
        - Results depend on implementation, assumptions, parameters, and
          numerical methods.
        - Features not implemented in a module are not simulated merely
          because they are described conceptually.
        - Qiskit results depend on compatible dependencies and conventions.
        - Claims about experimental accuracy require separate evidence.
        """
    )

    st.markdown("## 14. Recommended research workflow")

    st.markdown(
        """
        1. State a specific research question.
        2. Identify the model assumptions and parameters.
        3. Establish an ideal baseline.
        4. Change one parameter at a time.
        5. Record settings and outputs.
        6. Repeat at different shot counts or noise settings when relevant.
        7. Verify equations and conventions independently.
        8. Document limitations and alternative explanations.
        9. Compare important conclusions with analytical calculations,
           trusted references, or experimental data when available.
        """
    )

    st.divider()
    st.subheader("Numerical validation")

    st.write(
        "Run the project's integration smoke tests to check the paths "
        "covered by the test script. Passing these tests does not prove "
        "that every model is physically accurate."
    )

    if st.button(
        "Run integration smoke tests",
        key="about_run_integration_tests",
    ):
        try:
            proc = subprocess.run(
                [sys.executable, "test_integration.py"],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if proc.returncode == 0:
                st.success("Integration smoke tests passed.")
            else:
                st.error(
                    "Integration smoke tests reported an error."
                )

            st.code(
                proc.stdout
                + ("\n" + proc.stderr if proc.stderr else "")
            )

        except Exception as exc:
            st.exception(exc)

    with st.expander("How to interpret validation results"):
        st.markdown(
            """
            Passing a smoke test means the checks performed by that test
            completed successfully in the current environment. It does not
            establish correctness for every possible input, physical accuracy,
            or completeness of the modeled noise.

            For research, supplement smoke tests with unit tests, analytical
            checks, numerical convergence checks, and experimental comparisons
            where appropriate.
            """
        )


# ============================================================
# TAB 5: TUTORIAL — HOW TO USE
# ============================================================

with tutorial_tab:
    st.header("Tutorial — How to Use QUANTA-SIM")

    st.markdown(
        """
        This tutorial starts with basic navigation and progresses toward
        structured computational experiments.

        **Recommended order:** start with Circuit Builder, explore MZI
        and HOM experiments, and then try the Qiskit comparison.
        """
    )

    st.info(
        "The instructions below cover controls visible in the current app. "
        "Available circuit-builder operations depend on the builder module."
    )

    with st.expander(
        "Lesson 1 — Open the app and understand the tabs",
        expanded=True,
    ):
        st.markdown(
            """
            1. Open QUANTA-SIM in your browser or start the app locally.
            2. Choose the tab for the task you want to perform.
            3. Adjust a slider or selection control.
            4. Read the updated charts, tables, or metrics.
            5. Record the parameter settings before interpreting results.

            **Circuit Builder:** construct or inspect an optical circuit.

            **Experiments & Noise:** explore MZI interference, HOM
            probabilities, sampled counts, and modeled imperfections.

            **Qiskit Comparison:** compare an optical model with a digital
            quantum-circuit simulation.

            **ABOUT:** review the physics, equations, architecture,
            and limitations.
            """
        )

    with st.expander("Lesson 2 — First experiment: MZI interference"):
        st.markdown(
            """
            **Goal:** inspect how modeled output probabilities change
            over a phase sweep.

            1. Open **Experiments & Noise**.
            2. Set reflectivity to `0.50`.
            3. Keep optical imperfections disabled.
            4. Set measurement shots to `1024`.
            5. Inspect the MZI interference chart.
            6. Read the P(mode 0) visibility metric.
            7. Note the shape of the curves and your parameter settings.

            Questions to investigate:

            - Where does mode 0 reach its maximum and minimum?
            - How does mode 1 change relative to mode 0?
            - Does the result match an analytical calculation using
              the engine's actual phase and beam-splitter conventions?

            The chart sweeps phase internally, so this tab does not require
            a separate phase slider.
            """
        )

    with st.expander("Lesson 3 — Explore HOM interference"):
        st.markdown(
            """
            1. Open **Experiments & Noise**.
            2. Set reflectivity to `0.50`.
            3. Disable optical imperfections for the baseline.
            4. Inspect the output Fock-state probability table.
            5. Inspect the sampled counts.
            6. Locate the `|1,1⟩` coincidence state if it appears.

            Under the usual ideal HOM conditions, indistinguishable photons
            at a balanced beam splitter suppress coincidences.

            The current interface does not expose every experimental
            variable, such as detector efficiency or photon distinguishability.
            Do not assume such effects are included unless the engine
            explicitly models them.
            """
        )

    with st.expander("Lesson 4 — Investigate optical imperfections"):
        st.markdown(
            """
            **Goal:** compare the ideal baseline with modeled imperfections.

            1. Open **Experiments & Noise**.
            2. Set reflectivity to `0.50`.
            3. Enable optical imperfections.
            4. Start with phase drift σ = `0.10` rad.
            5. Start with reflectivity error σ = `0.02`.
            6. Compare ideal and noisy curves.
            7. Increase phase drift while holding reflectivity error fixed.
            8. Restore the original settings.
            9. Change reflectivity error while holding phase drift fixed.

            Suggested manual test plan:

            | Trial | Phase drift σ | Reflectivity error σ |
            |---|---:|---:|
            | Baseline | 0.00 | 0.00 |
            | A | 0.05 | 0.02 |
            | B | 0.20 | 0.02 |
            | C | 0.10 | 0.00 |
            | D | 0.10 | 0.05 |

            Change one parameter at a time so that observed differences
            are easier to interpret. Results represent the selected model,
            not necessarily a complete model of laboratory behavior.
            """
        )

    with st.expander("Lesson 5 — Understand measurement shots"):
        st.markdown(
            """
            A shot is one simulated measurement trial. For an event with
            probability p over N independent trials, the expected count is:
            """
        )
        st.latex(r"\mathbb{E}[n] = Np")

        st.markdown(
            "For independent Bernoulli trials, the standard deviation "
            "of the estimated frequency is:"
        )
        st.latex(
            r"\sigma_{\hat p} = \sqrt{\frac{p(1-p)}{N}}"
        )

        st.markdown(
            """
            In the current interface:

            - Experiments & Noise offers 128, 512, 1024, 4096, and 8192 shots.
            - HOM displays sampled counts.
            - The MZI chart displays theoretical probabilities.
            - Qiskit Comparison has its own shot-count control.

            **Exercise:** compare HOM counts at 128 and 8192 shots with
            other settings fixed. Larger shot counts generally reduce
            statistical fluctuations, but do not remove model bias.
            """
        )

    with st.expander("Lesson 6 — Run a Qiskit benchmark"):
        st.markdown(
            """
            1. Open **Qiskit Comparison**.
            2. Set phase to approximately `1.047` rad (π/3).
            3. Set reflectivity to `0.50`.
            4. Select `2048` shots.
            5. Click **Run Qiskit benchmark**.
            6. Wait for the calculation to finish.
            7. Read TVD, Classical Fidelity, and Hellinger Distance.
            8. Compare the optical-theory and Qiskit-sampled bars.
            9. Inspect the digital circuit and resource breakdown.
            10. Open Raw benchmark details to inspect counts and reports.

            If the benchmark fails, inspect the displayed error. Possible
            causes include missing dependencies, incompatible versions,
            or a problem in the bridge or simulator configuration.

            A mismatch may reflect sampling variation, different conventions,
            output mapping, or a model issue. Verify the metric definitions
            and assumptions before drawing a scientific conclusion.
            """
        )

    with st.expander("Lesson 7 — Use the Circuit Builder"):
        st.markdown(
            """
            1. Open **Circuit Builder**.
            2. Read the builder's on-screen instructions.
            3. Choose from the components and operations it provides.
            4. Follow its controls to construct or inspect a circuit.
            5. Record the component arrangement and settings.
            6. Change one component or parameter and compare the outputs.

            The precise builder controls are defined by
            `render_integrated_builder_tab()` in
            `optical_builder/utils/builder_tab.py`. This tutorial does not
            assume features that are not exposed by the installed builder.
            """
        )

    with st.expander("Lesson 8 — Reproducible research workflow"):
        st.markdown(
            """
            1. Define a specific research question.
            2. Identify the physical assumptions and relevant parameters.
            3. Establish a baseline.
            4. Change one independent variable at a time.
            5. Record the complete settings and outputs.
            6. Repeat with different shot counts or noise settings where useful.
            7. Check analytical equations, conventions, and normalization.
            8. Document which effects are and are not modeled.
            9. Compare important conclusions with trusted references
               or experimental data when available.
            10. Record software versions, dependencies, and random seeds
                where applicable.

            A fixed seed can help reproduce some stochastic results,
            but it does not replace independent statistical checks.
            """
        )

    with st.expander("Lesson 9 — Troubleshooting"):
        st.markdown(
            """
            **The app does not start**

            - Read the terminal traceback.
            - Confirm the intended Python environment is active.
            - Check that Streamlit, NumPy, and pandas are installed.
            - Check that the project modules can be imported.

            **Circuit Builder reports an error**

            - Confirm that the `optical_builder` package exists.
            - Check the path to `builder_tab.py`.
            - Inspect the traceback for missing imports.

            **Qiskit benchmark fails**

            - Check whether Qiskit and Qiskit Aer are installed at
              compatible versions.
            - Read the exception shown by the benchmark.
            - Verify that the bridge and integration modules are present.

            **Results differ from an expected formula**

            - Check phase conventions and reflectivity definitions.
            - Check input states, output-mode order, and normalization.
            - Distinguish theoretical probabilities from sampled counts.
            - Check whether the expected physical effect is actually modeled.
            - Compare with an independently derived analytical result.

            **Integration tests fail**

            - Read the output in ABOUT.
            - Inspect the failing test and traceback.
            - Resolve code or dependency issues before relying on the result.
            """
        )

    st.divider()
    st.subheader("Quick reference")

    st.markdown(
        """
        | Task | Tab |
        |---|---|
        | Construct or inspect an optical circuit | Circuit Builder |
        | Explore phase-dependent interference | Experiments & Noise |
        | Inspect HOM probabilities and sampled counts | Experiments & Noise |
        | Change modeled optical imperfections | Experiments & Noise |
        | Compare optical and digital simulation | Qiskit Comparison |
        | Read physics and limitations | ABOUT |
        | Follow guided workflows | Tutorial — How to Use |

        **Research reminder:** simulation results depend on the implemented
        model, selected parameters, and numerical methods. Validate important
        conclusions independently.
        """
    )

    st.success(
        "You are ready to explore QUANTA-SIM: establish a baseline, "
        "change one parameter at a time, and record your results."
    )


# ============================================================
# TAB 6: INTERACTIVE ANIMATIONS LAB
# ============================================================

with animations_tab:
    render_animations_lab()
