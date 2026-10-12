
import matplotlib.pyplot as plt


def plot_optical_circuit(components):
    """
    Draw an optical circuit and return its figure
    for display in Streamlit.
    """

    fig, ax = plt.subplots(figsize=(12, 3))

    ax.set_xlim(-0.5, len(components) + 1.5)
    ax.set_ylim(-1, 1)

    # Optical path
    ax.plot(
        [0, len(components) + 1],
        [0, 0],
        linewidth=2
    )

    # Draw components
    for i, component in enumerate(components, start=1):
        ax.scatter(
            i,
            0,
            s=1200,
            zorder=3
        )

        label_y = 0.45 if i % 2 == 1 else -0.45

        ax.text(
            i,
            label_y,
            component,
            ha="center",
            va="center",
            fontsize=8,
            wrap=True
        )

    # Input and output labels
    ax.text(
        0,
        0,
        "Input",
        ha="right",
        va="center"
    )

    ax.text(
        len(components) + 1,
        0,
        "Output",
        ha="left",
        va="center"
    )

    ax.set_title("QUANTA-SIM Optical Circuit")
    ax.axis("off")

    plt.tight_layout()

    return fig
