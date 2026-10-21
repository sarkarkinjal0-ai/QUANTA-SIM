"""Interactive animation gallery for QUANTA-SIM.

Adds visual, educational views for beam splitters, phase shifters, MZI,
Hong-Ou-Mandel interference, and selected Qiskit gate circuits.
The optical paths and moving markers are explanatory visualizations, not
literal trajectories of individual quantum particles.
"""
from __future__ import annotations

import math
from html import escape

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


def _mount_svg(body: str, height: int = 350) -> None:
    """Render self-contained animated SVG/CSS inside a Streamlit iframe."""
    page = f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
:root {{ color-scheme: dark; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: transparent; color: #e8eefc;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; }}
svg {{ width: 100%; height: auto; display: block; max-height: {height}px; }}
.wire {{ fill: none; stroke: #7890ad; stroke-width: 3; stroke-linecap: round; }}
.wire-dim {{ fill: none; stroke: #526780; stroke-width: 2; stroke-dasharray: 7 7; }}
.optical {{ fill: #18283c; stroke: #8eb9ec; stroke-width: 2.5; rx: 7; }}
.gate {{ fill: #183b58; stroke: #75d7e8; stroke-width: 2.2; rx: 7; }}
.label {{ fill: #e8eefc; font-size: 17px; font-weight: 600; }}
.small {{ fill: #a8b9d1; font-size: 13px; }}
.detector {{ fill: #102c32; stroke: #54d6b0; stroke-width: 2.5; }}
.photon {{ fill: #ffe08a; stroke: #fff7d6; stroke-width: 1.5; filter: drop-shadow(0 0 7px #ffca63); }}
.photon-cyan {{ fill: #63e2f5; stroke: #effdff; stroke-width: 1.5; filter: drop-shadow(0 0 7px #63e2f5); }}
.pulse {{ fill: none; stroke: #ffe08a; stroke-width: 2; opacity: .75; stroke-dasharray: 9 9; animation: dash 1.3s linear infinite; }}
@keyframes dash {{ to {{ stroke-dashoffset: -36; }} }}
@keyframes glow {{ 0%,100% {{ opacity: .5; }} 50% {{ opacity: 1; }} }}
.glow {{ animation: glow 1.5s ease-in-out infinite; }}
@media (prefers-reduced-motion: reduce) {{ .pulse, .glow {{ animation: none; }} }}
</style></head><body><svg viewBox="0 0 900 320" role="img" aria-label="Animated quantum optics teaching diagram">{body}</svg></body></html>"""
    components.html(page, height=height + 12, scrolling=False)


def _probability_bar(label: str, probability: float, color: str) -> str:
    pct = max(0.0, min(1.0, float(probability))) * 100
    return f"""<div style='margin:.45rem 0'>
<div style='display:flex;justify-content:space-between;gap:.5rem;color:#dbe7f6;font-size:.92rem'><span>{escape(label)}</span><b>{pct:.1f}%</b></div>
<div style='height:10px;background:#24364b;border-radius:99px;overflow:hidden;margin-top:5px'><div style='height:10px;width:{pct:.3f}%;background:{color};border-radius:99px;transition:width .2s'></div></div></div>"""


def _beam_splitter() -> None:
    st.subheader("1 · Beam splitter")
    st.write("Change reflectivity and watch the two output channels brighten or dim.")
    r = st.slider("Reflectivity R", 0.0, 1.0, 0.5, 0.01, key="anim_bs_reflectivity")
    t = 1.0 - r
    upper_opacity = 0.2 + 0.8 * math.sqrt(t)
    lower_opacity = 0.2 + 0.8 * math.sqrt(r)
    body = f"""
<path class="wire" d="M55 160 H390"/><path class="wire" d="M410 160 L760 65" opacity="{upper_opacity:.3f}"/><path class="wire" d="M410 160 L760 255" opacity="{lower_opacity:.3f}"/>
<path class="pulse" d="M55 160 H390"/><path class="pulse" d="M410 160 L760 65" opacity="{upper_opacity:.3f}"/><path class="pulse" d="M410 160 L760 255" opacity="{lower_opacity:.3f}"/>
<rect class="optical" x="376" y="126" width="48" height="68" transform="rotate(45 400 160)"/><text class="label" x="400" y="215" text-anchor="middle">BS</text>
<circle class="photon" r="8"><animateMotion dur="2.2s" repeatCount="indefinite" path="M55 160 H390"/></circle>
<circle class="photon-cyan" r="7" opacity="{upper_opacity:.3f}"><animateMotion dur="2.2s" repeatCount="indefinite" path="M410 160 L760 65"/></circle>
<circle class="photon" r="7" opacity="{lower_opacity:.3f}"><animateMotion dur="2.2s" begin="-.7s" repeatCount="indefinite" path="M410 160 L760 255"/></circle>
<circle class="detector" cx="790" cy="57" r="22" opacity="{upper_opacity:.3f}"/><circle class="detector" cx="790" cy="263" r="22" opacity="{lower_opacity:.3f}"/>
<text class="label" x="790" y="25" text-anchor="middle">T = {t:.2f}</text><text class="label" x="790" y="303" text-anchor="middle">R = {r:.2f}</text>
<text class="small" x="55" y="133">Input</text><text class="small" x="650" y="30">Transmitted</text><text class="small" x="650" y="292">Reflected</text>
"""
    _mount_svg(body)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(_probability_bar("Transmitted channel (T)", t, "#63e2f5"), unsafe_allow_html=True)
    with c2:
        st.markdown(_probability_bar("Reflected channel (R)", r, "#ffe08a"), unsafe_allow_html=True)
    st.caption("The brightness indicates relative channel weight. The animation is a teaching schematic, not a claim that one photon splits into two detected photons.")


def _phase_shifter() -> None:
    st.subheader("2 · Phase shifter")
    st.write("A phase shifter changes the phase of an optical mode without, in the ideal model, changing its intensity by itself.")
    phi = st.slider("Phase shift φ (radians)", 0.0, 2 * math.pi, math.pi / 2, 0.01, key="anim_phase_only")

    def wave_path(x0: float, x1: float, phase: float) -> str:
        pts = []
        for x in np.linspace(x0, x1, 130):
            y = 150 + 22 * math.sin((x - x0) * 2 * math.pi / 120 + phase)
            pts.append((x, y))
        return "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)

    incoming = wave_path(60, 365, 0.0)
    outgoing = wave_path(530, 835, phi)
    body = f"""
<path class="wire" d="M55 150 H845" opacity=".3"/><path d="{incoming}" fill="none" stroke="#63e2f5" stroke-width="4" stroke-linecap="round"/>
<rect class="optical" x="390" y="104" width="100" height="92"/><text class="label" x="440" y="142" text-anchor="middle">PHASE</text><text class="label" x="440" y="166" text-anchor="middle">SHIFT</text>
<path class="pulse" d="M55 150 H390"/><path class="pulse" d="M490 150 H845"/><path d="{outgoing}" fill="none" stroke="#b69cff" stroke-width="4" stroke-linecap="round"/>
<circle class="photon" r="7"><animateMotion dur="3s" repeatCount="indefinite" path="M55 150 H390"/></circle><circle class="photon-cyan" r="7"><animateMotion dur="3s" begin="-1.1s" repeatCount="indefinite" path="M490 150 H845"/></circle>
<text class="small" x="65" y="90">Reference phase: 0</text><text class="label" x="680" y="90" text-anchor="middle">φ = {phi:.2f} rad</text><text class="small" x="65" y="238">Input field</text><text class="small" x="680" y="238" text-anchor="middle">Phase-shifted field</text>
"""
    _mount_svg(body)
    st.metric("Phase offset", f"{phi:.3f} rad", f"{math.degrees(phi):.1f}°")
    st.caption("The wavy lines represent optical-field phase. Their vertical shape is schematic, not the physical path of a photon.")


def _mzi() -> None:
    st.subheader("3 · Mach–Zehnder interferometer (MZI)")
    st.write("Adjust the relative phase and beam-splitter reflectivity to see how recombination changes the output probabilities.")
    c1, c2 = st.columns(2)
    with c1:
        r = st.slider("Beam-splitter reflectivity R", 0.0, 1.0, 0.5, 0.01, key="anim_mzi_r")
    with c2:
        phi = st.slider("Relative phase φ (radians)", 0.0, 2 * math.pi, 0.0, 0.01, key="anim_mzi_phi")

    # Interference contrast for a symmetric two-BS MZI convention matching
    # P(output 0)=cos²(phi/2) for the balanced R=0.5 case.
    p0 = 1.0 - 4.0 * r * (1.0 - r) * (math.sin(phi / 2.0) ** 2)
    p0 = min(1.0, max(0.0, p0))
    p1 = 1.0 - p0
    hi = 0.25 + 0.75 * math.sqrt(p0)
    lo = 0.25 + 0.75 * math.sqrt(p1)
    body = f"""
<path class="wire" d="M45 165 H230 L330 75 H540 L645 165 H790"/><path class="wire" d="M230 165 L330 255 H540 L645 165 H790"/>
<path class="pulse" d="M45 165 H230 L330 75 H540 L645 165"/><path class="pulse" d="M230 165 L330 255 H540 L645 165"/>
<rect class="optical" x="209" y="143" width="42" height="44" transform="rotate(45 230 165)"/><text class="small" x="230" y="203" text-anchor="middle">BS1</text>
<rect class="optical" x="624" y="143" width="42" height="44" transform="rotate(45 645 165)"/><text class="small" x="645" y="203" text-anchor="middle">BS2</text>
<path class="wire" d="M410 75 V55 H478 V75"/><rect class="gate" x="402" y="49" width="84" height="48"/><text class="label" x="444" y="70" text-anchor="middle">φ</text><text class="small" x="444" y="87" text-anchor="middle">phase</text>
<path class="wire" d="M365 255 H510" stroke-dasharray="7 7"/><text class="small" x="436" y="285" text-anchor="middle">reference arm</text>
<circle class="photon" r="7"><animateMotion dur="3.0s" repeatCount="indefinite" path="M45 165 H230 L330 75 H540 L645 165"/></circle>
<circle class="photon-cyan" r="7"><animateMotion dur="3.0s" begin="-1.0s" repeatCount="indefinite" path="M45 165 H230 L330 255 H540 L645 165"/></circle>
<path class="wire" d="M645 165 L760 103" opacity="{hi:.3f}"/><path class="wire" d="M645 165 L760 227" opacity="{lo:.3f}"/>
<circle class="detector" cx="790" cy="88" r="23" opacity="{hi:.3f}"/><circle class="detector" cx="790" cy="242" r="23" opacity="{lo:.3f}"/>
<text class="label" x="790" y="51" text-anchor="middle">D0</text><text class="label" x="790" y="282" text-anchor="middle">D1</text>
<text class="small" x="48" y="142">Input</text><text class="small" x="438" y="24" text-anchor="middle">Adjustable phase</text>
"""
    _mount_svg(body, height=360)
    m0, m1 = st.columns(2)
    with m0:
        st.metric("Detector D0 probability", f"{p0:.4f}")
        st.markdown(_probability_bar("D0", p0, "#63e2f5"), unsafe_allow_html=True)
    with m1:
        st.metric("Detector D1 probability", f"{p1:.4f}")
        st.markdown(_probability_bar("D1", p1, "#b69cff"), unsafe_allow_html=True)
    st.caption("For a balanced MZI (R = 0.5), the displayed convention gives P(D0)=cos²(φ/2) and P(D1)=sin²(φ/2). The animated paths illustrate the two arms; detection probabilities come from the stated idealized model.")


def _hom() -> None:
    st.subheader("4 · Hong–Ou–Mandel (HOM) two-photon interference")
    st.write("Explore how indistinguishable photons tend to leave a balanced beam splitter together, reducing coincidences at separate outputs.")
    c1, c2 = st.columns(2)
    with c1:
        distinguishability = st.slider("Photon distinguishability", 0.0, 1.0, 0.0, 0.01, key="anim_hom_dist")
        st.caption("0 = indistinguishable · 1 = fully distinguishable")
    with c2:
        shots = st.select_slider("Sampled trials", options=[128, 512, 1024, 4096, 8192], value=1024, key="anim_hom_shots")
    overlap = 1.0 - distinguishability
    probabilities = np.array([(1.0 + overlap) / 4.0, (1.0 - overlap) / 2.0, (1.0 + overlap) / 4.0])
    probabilities = probabilities / probabilities.sum()
    counts = np.random.default_rng(42).multinomial(int(shots), probabilities)
    labels = ["|2,0⟩", "|1,1⟩", "|0,2⟩"]
    body = f"""
<path class="wire" d="M45 92 H380 L420 160 L380 228 H45"/><path class="wire" d="M420 160 L770 92"/><path class="wire" d="M420 160 L770 228"/>
<path class="pulse" d="M45 92 H380"/><path class="pulse" d="M45 228 H380"/><path class="pulse" d="M420 160 L770 92" opacity="{probabilities[0]+probabilities[1]/2:.3f}"/><path class="pulse" d="M420 160 L770 228" opacity="{probabilities[2]+probabilities[1]/2:.3f}"/>
<rect class="optical" x="390" y="130" width="60" height="60" transform="rotate(45 420 160)"/><text class="label" x="420" y="202" text-anchor="middle">BS</text>
<circle class="photon" r="8"><animateMotion dur="2.1s" repeatCount="indefinite" path="M45 92 H380 L420 160"/></circle><circle class="photon-cyan" r="8"><animateMotion dur="2.1s" begin="-1.05s" repeatCount="indefinite" path="M45 228 H380 L420 160"/></circle>
<circle class="detector" cx="790" cy="86" r="23"/><circle class="detector" cx="790" cy="234" r="23"/><text class="label" x="790" y="48" text-anchor="middle">Output A</text><text class="label" x="790" y="276" text-anchor="middle">Output B</text>
<text class="small" x="45" y="66">Photon 1</text><text class="small" x="45" y="258">Photon 2</text><text class="small" x="515" y="140">Overlap = {overlap:.2f}</text><text class="small" x="515" y="163">Coincidence P = {probabilities[1]:.2f}</text>
"""
    _mount_svg(body)
    a, b, c = st.columns(3)
    for col, label, prob, count in zip((a, b, c), labels, probabilities, counts):
        col.metric(label, f"{prob:.3f}", f"{int(count)} counts")
    frame = pd.DataFrame({"Theory": probabilities, "Sampled frequency": counts / int(shots)}, index=labels)
    st.bar_chart(frame)
    st.caption("For the ideal balanced splitter used here, P(|1,1⟩)=(1−overlap)/2. These outcomes are sampled with a fixed seed for reproducibility; real experimental counts fluctuate.")


def _qiskit() -> None:
    st.subheader("5 · Animated Qiskit digital circuits")
    st.write("Watch a moving marker traverse a gate sequence and inspect the actual Qiskit circuit text and statevector probabilities when Qiskit is installed.")
    template = st.selectbox(
        "Circuit template",
        ["MZI analogue: H → P(φ) → H", "Bell pair: H → CX"],
        key="anim_qiskit_template",
    )
    phase = 0.0
    if template.startswith("MZI"):
        phase = st.slider("Phase gate angle φ (radians)", 0.0, 2 * math.pi, math.pi / 2, 0.01, key="anim_qiskit_phase")
        probs = {"0": math.cos(phase / 2) ** 2, "1": math.sin(phase / 2) ** 2}
        body = f"""
<path class="wire" d="M55 160 H845"/><text class="label" x="55" y="130">q0</text>
<rect class="gate" x="205" y="126" width="72" height="68"/><text class="label" x="241" y="166" text-anchor="middle">H</text>
<rect class="gate" x="380" y="126" width="96" height="68"/><text class="label" x="428" y="155" text-anchor="middle">P(φ)</text><text class="small" x="428" y="177" text-anchor="middle">{phase:.2f}</text>
<rect class="gate" x="580" y="126" width="72" height="68"/><text class="label" x="616" y="166" text-anchor="middle">H</text>
<rect class="optical" x="745" y="126" width="70" height="68"/><text class="label" x="780" y="166" text-anchor="middle">M</text>
<circle class="photon" r="8"><animateMotion dur="3.3s" repeatCount="indefinite" path="M55 160 H845"/></circle><path class="pulse" d="M55 160 H845"/>
<text class="small" x="240" y="220" text-anchor="middle">superposition</text><text class="small" x="428" y="220" text-anchor="middle">phase</text><text class="small" x="616" y="220" text-anchor="middle">recombine</text><text class="small" x="780" y="220" text-anchor="middle">measure</text>
"""
    else:
        probs = {"00": 0.5, "01": 0.0, "10": 0.0, "11": 0.5}
        body = """
<path class="wire" d="M55 118 H845"/><path class="wire" d="M55 228 H845"/><text class="label" x="55" y="90">q0</text><text class="label" x="55" y="200">q1</text>
<rect class="gate" x="210" y="84" width="72" height="68"/><text class="label" x="246" y="124" text-anchor="middle">H</text>
<path class="wire" d="M430 118 V228"/><circle cx="430" cy="118" r="8" fill="#75d7e8"/><circle cx="430" cy="228" r="22" fill="#183b58" stroke="#75d7e8" stroke-width="2.5"/><text class="label" x="430" y="234" text-anchor="middle">X</text>
<rect class="optical" x="700" y="84" width="70" height="68"/><text class="label" x="735" y="124" text-anchor="middle">M</text><rect class="optical" x="700" y="194" width="70" height="68"/><text class="label" x="735" y="234" text-anchor="middle">M</text>
<circle class="photon" r="8"><animateMotion dur="3.3s" repeatCount="indefinite" path="M55 118 H845"/></circle><circle class="photon-cyan" r="7"><animateMotion dur="3.3s" begin="-1.1s" repeatCount="indefinite" path="M55 228 H845"/></circle><path class="pulse" d="M55 118 H845"/><path class="pulse" d="M55 228 H845"/>
<text class="small" x="246" y="176" text-anchor="middle">Hadamard</text><text class="small" x="430" y="282" text-anchor="middle">controlled-X</text><text class="small" x="735" y="176" text-anchor="middle">measure</text>
"""
    _mount_svg(body, height=350)

    st.markdown("**Expected measurement probabilities**")
    st.dataframe(pd.DataFrame({"Bitstring": list(probs.keys()), "Probability": list(probs.values())}), hide_index=True, use_container_width=True)
    try:
        from qiskit import QuantumCircuit  # type: ignore
        from qiskit.quantum_info import Statevector  # type: ignore

        if template.startswith("MZI"):
            circuit = QuantumCircuit(1, 1)
            circuit.h(0)
            circuit.p(float(phase), 0)
            circuit.h(0)
            circuit.measure(0, 0)
        else:
            circuit = QuantumCircuit(2, 2)
            circuit.h(0)
            circuit.cx(0, 1)
            circuit.measure([0, 1], [0, 1])
        state_circuit = circuit.remove_final_measurements(inplace=False)
        state = Statevector.from_instruction(state_circuit)
        actual = state.probabilities_dict()
        st.markdown("**Actual Qiskit circuit**")
        st.code(str(circuit.draw(output="text")), language="text")
        st.markdown("**Statevector-derived probabilities (before sampling)**")
        st.dataframe(
            pd.DataFrame({"Bitstring": list(actual.keys()), "Probability": [float(v) for v in actual.values()]}),
            hide_index=True,
            use_container_width=True,
        )
        st.caption("The MZI analogue is a qubit gate sequence H–P(φ)–H with the same balanced-interference probability formula. It is a digital analogy, not a claim that optical components are literally identical to qubit gates.")
    except Exception as exc:
        st.info("The animated circuit schematic is available, but Qiskit's circuit/statevector view could not be loaded in this environment. Confirm that `qiskit` is installed. The visual remains an educational schematic.")
        with st.expander("Optional diagnostic"):
            st.code(f"{type(exc).__name__}: {exc}")


def render_animations_lab() -> None:
    """Entry point added as a separate tab in app.py."""
    st.header("Interactive Animations Lab")
    st.markdown(
        "Explore the optical elements, interference experiments, and digital circuit analogy. "
        "Choose one view at a time so hidden animations do not keep running."
    )
    choice = st.selectbox(
        "Choose an animation",
        [
            "Beam splitter",
            "Phase shifter",
            "Mach–Zehnder interferometer (MZI)",
            "Hong–Ou–Mandel (HOM)",
            "Qiskit digital circuit",
        ],
        key="quantum_animations_choice",
    )
    st.divider()
    if choice == "Beam splitter":
        _beam_splitter()
    elif choice == "Phase shifter":
        _phase_shifter()
    elif choice == "Mach–Zehnder interferometer (MZI)":
        _mzi()
    elif choice == "Hong–Ou–Mandel (HOM)":
        _hom()
    else:
        _qiskit()
