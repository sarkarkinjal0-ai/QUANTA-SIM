"""Integrated Streamlit Optical Builder tab."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from optical_builder.core.builder import OpticalCircuit, mzi_circuit, pattern_label
from optical_builder.utils.schematic import draw_circuit

def _get_circuit(n_modes):
    circ=st.session_state.get("optical_circuit")
    if circ is None or circ.n_modes != n_modes:
        circ=OpticalCircuit(n_modes); st.session_state["optical_circuit"]=circ
    return circ

def _bars(probs, labels, title):
    fig,ax=plt.subplots(figsize=(6,3.5))
    ax.bar(labels, probs); ax.set_ylim(0,1.05); ax.set_ylabel("Probability"); ax.set_title(title)
    for i,p in enumerate(probs): ax.text(i,p+0.02,f"{p:.3f}",ha="center")
    fig.tight_layout(); return fig

def render_integrated_builder_tab():
    st.header("Optical Circuit Builder → Photon & Noise Engine")
    st.caption("Build the circuit here; the shared Photon & Noise Engine executes the physics.")
    n=st.selectbox("Number of optical modes",[2,3,4],index=0,key="ob_n")
    circ=_get_circuit(n); modes=list(range(n))
    kind=st.radio("Component",["Beam splitter","Phase shifter"],horizontal=True,key="ob_kind")
    if kind=="Beam splitter":
        a=st.selectbox("Mode A",modes,index=0,key="ob_a")
        b=st.selectbox("Mode B",modes,index=min(1,n-1),key="ob_b")
        theta=st.slider("Splitting angle θ",0.0,float(np.pi/2),float(np.pi/4),0.01,key="ob_theta")
        if st.button("Add beam splitter",key="ob_add_bs"):
            if a==b: st.error("Choose two different modes.")
            else: circ.add_beam_splitter(a,b,theta)
    else:
        m=st.selectbox("Mode",modes,key="ob_ps_m")
        phi=st.slider("Phase φ (rad)",0.0,float(2*np.pi),float(np.pi/2),0.01,key="ob_phi")
        if st.button("Add phase shifter",key="ob_add_ps"): circ.add_phase_shifter(m,phi)
    c1,c2,c3=st.columns(3)
    if c1.button("Undo last",key="ob_undo"): circ.remove_last()
    if c2.button("Clear all",key="ob_clear"): circ.clear()
    if c3.button("Load MZI preset",key="ob_mzi",disabled=n!=2):
        st.session_state["optical_circuit"]=circ=mzi_circuit(np.pi/2)
    if not circ.components:
        st.info("Add components to begin."); return
    st.subheader("Circuit")
    for i,c in enumerate(circ.components,1): st.write(f"{i}. {c.label()}")
    st.pyplot(draw_circuit(circ))
    U=circ.total_unitary()
    st.subheader("Total unitary")
    st.success(f"Unitarity verified: {circ.is_unitary()}")
    c1,c2=st.columns(2)
    c1.dataframe(pd.DataFrame(np.round(U,4)).astype(str))
    fig,ax=plt.subplots(figsize=(4,3.2)); im=ax.imshow(np.abs(U)**2,vmin=0,vmax=1)
    ax.set_title("|Uᵢⱼ|²"); ax.set_xlabel("Input mode"); ax.set_ylabel("Output mode"); fig.colorbar(im,ax=ax); fig.tight_layout(); c2.pyplot(fig)

    st.subheader("Photon & Noise Engine")
    in_mode=st.selectbox("Single-photon input mode",modes,key="ob_in")
    noisy=st.toggle("Inject physical imperfections",key="ob_noise")
    pstd=st.slider("Phase drift σ (rad)",0.0,1.0,0.05,0.01,key="ob_pstd") if noisy else 0.0
    rstd=st.slider("Beam-splitter reflectivity σ",0.0,0.2,0.02,0.005,key="ob_rstd") if noisy else 0.0
    shots=st.select_slider("Measurement shots",[128,512,1024,4096,8192],value=1024,key="ob_shots")
    result=circ.simulate_single_photon(input_mode=in_mode,phase_noise_std=pstd,
                                       reflectivity_noise_std=rstd,noisy=noisy,seed=42,shots=shots)
    st.pyplot(_bars(result["probabilities"],[f"Mode {i}" for i in modes],"Photon output probabilities"))
    st.write("Finite-shot counts:",result["sampled_counts"])

    st.subheader("Two-photon / Fock-state output")
    if n>=2:
        a,b=st.columns(2)
        ia=a.selectbox("Photon 1 input",modes,index=0,key="ob_ta")
        ib=b.selectbox("Photon 2 input",modes,index=min(1,n-1),key="ob_tb")
        tp=circ.simulate_two_photon(ia,ib,shots=shots,seed=42)
        labels=[pattern_label(k) for k in tp["probabilities"]]
        st.pyplot(_bars(list(tp["probabilities"].values()),labels,"Two-photon output configurations"))
        st.write("Fock-state shot counts:",tp["sampled_counts"])
