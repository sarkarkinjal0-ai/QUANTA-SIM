import numpy as np
import matplotlib.pyplot as plt


def plot_mzi_interference(phases, output_0, output_1):
    """
    Plot MZI output probabilities against phase.
    """

    plt.figure(figsize=(9, 5))

    plt.plot(phases, output_0, label="Output Mode 0")
    plt.plot(phases, output_1, label="Output Mode 1")

    plt.xlabel("Phase (radians)")
    plt.ylabel("Probability")
    plt.title("Mach-Zehnder Interference")

    plt.ylim(0, 1.05)
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.show()
def plot_hom_dip(distinguishabilities, coincidences):
    """
    Plot HOM coincidence probability
    against photon distinguishability.
    """

    plt.figure(figsize=(9, 5))

    plt.plot(
        distinguishabilities,
        coincidences,
        marker="o",
        label="HOM Coincidence Probability"
    )

    plt.xlabel("Photon Distinguishability")
    plt.ylabel("Coincidence Probability")
    plt.title("Hong-Ou-Mandel Interference")

    plt.ylim(0, 0.55)
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.show()
def plot_mzi_comparison(
    phases,
    optical_0,
    qiskit_0
):
    """
    Compare optical and Qiskit MZI
    output-0 probabilities.
    """

    plt.figure(figsize=(9, 5))

    plt.plot(
        phases,
        optical_0,
        label="QUANTA-SIM Optical"
    )

    plt.plot(
        phases,
        qiskit_0,
        "--",
        label="Qiskit"
    )

    plt.xlabel("Phase (radians)")
    plt.ylabel("Probability")
    plt.title("QUANTA-SIM vs Qiskit MZI")

    plt.ylim(0, 1.05)
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.show()

def plot_unitary_magnitude(unitary):
    """
    Visualize the magnitude of a unitary matrix
    and return the figure for Streamlit.
    """

    fig, ax = plt.subplots(figsize=(6, 5))

    image = ax.imshow(
        np.abs(unitary),
        interpolation="nearest"
    )

    fig.colorbar(image, ax=ax, label="Magnitude")

    ax.set_xlabel("Input Mode")
    ax.set_ylabel("Output Mode")
    ax.set_title("Unitary Matrix Magnitude")

    fig.tight_layout()

    return fig

def plot_probability_histogram(probabilities, labels=None):
    """
    Plot measurement probabilities as a bar chart.
    """

    plt.figure(figsize=(8, 5))

    if labels is None:
        labels = [
            f"Mode {i}"
            for i in range(len(probabilities))
        ]

    plt.bar(labels, probabilities)

    plt.xlabel("Output State")
    plt.ylabel("Probability")
    plt.title("Quantum Measurement Probabilities")

    plt.ylim(0, 1.05)
    plt.grid(axis="y")

    plt.tight_layout()
    plt.show()