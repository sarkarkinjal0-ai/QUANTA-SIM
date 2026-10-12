"""Matplotlib plots for QUANTA-SIM. Each function returns a Figure,
so in Streamlit use: st.pyplot(fig)."""
import numpy as np
import matplotlib.pyplot as plt


def plot_phase_sweep(phi, p0, p1=None, title="MZI phase sweep"):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(phi, p0, label="Detector 0")
    ax.plot(phi, 1 - np.asarray(p0) if p1 is None else p1, label="Detector 1")
    ax.set_xlabel(r"Phase delay $\phi$ (rad)")
    ax.set_ylabel("Detection probability")
    ax.set_ylim(-0.02, 1.02)
    ax.set_title(title)
    ax.legend()
    ax.grid(alpha=0.3)
    return fig


def plot_noise_comparison(phi, ideal, noisy, v_ideal=None, v_noisy=None):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(phi, ideal, label="Ideal" + (f" (V={v_ideal:.2f})" if v_ideal is not None else ""))
    ax.plot(phi, noisy, "--", label="Noisy" + (f" (V={v_noisy:.2f})" if v_noisy is not None else ""))
    ax.set_xlabel(r"Phase $\phi$ (rad)")
    ax.set_ylabel("P(detector 0)")
    ax.set_title("Noise degrades fringe visibility")
    ax.legend()
    ax.grid(alpha=0.3)
    return fig


def plot_hom_dip(delays, visibility=1.0, width=1.0):
    """Coincidence probability vs relative delay (Gaussian dip)."""
    delays = np.asarray(delays)
    p = 0.5 * (1 - visibility * np.exp(-(delays / width) ** 2))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(delays, p)
    ax.axhline(0.5, color="gray", ls=":", label="Classical (distinguishable)")
    ax.set_xlabel("Relative delay")
    ax.set_ylabel(r"Coincidence probability $P(|1,1\rangle)$")
    ax.set_ylim(0, 0.6)
    ax.set_title("Hong-Ou-Mandel dip")
    ax.legend()
    ax.grid(alpha=0.3)
    return fig


def plot_hom_histogram(quantum=None, classical=None):
    """Bar chart over outcomes |2,0>, |1,1>, |0,2>."""
    labels = [r"$|2,0\rangle$", r"$|1,1\rangle$", r"$|0,2\rangle$"]
    classical = classical or [0.25, 0.5, 0.25]
    quantum = quantum or [0.5, 0.0, 0.5]
    x = np.arange(3)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(x - 0.2, classical, 0.4, label="Classical particles")
    ax.bar(x + 0.2, quantum, 0.4, label="Indistinguishable photons")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Probability")
    ax.set_title("Classical vs quantum bunching")
    ax.legend()
    return fig


def plot_benchmark(phi, exact, sampled, shots=None):
    """Exact continuous curve vs Qiskit shot-sampled points."""
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(phi, exact, label="Exact (continuous)")
    ax.scatter(phi, sampled, s=14, color="tab:red",
               label="Qiskit-Aer" + (f" ({shots} shots)" if shots else ""))
    ax.set_xlabel(r"Phase $\phi$ (rad)")
    ax.set_ylabel("P(detector 0)")
    ax.set_title("Exact vs shot-sampled probabilities")
    ax.legend()
    ax.grid(alpha=0.3)
    return fig
