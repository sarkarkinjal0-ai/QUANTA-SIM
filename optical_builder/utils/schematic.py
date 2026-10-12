"""Schematic drawing of an OpticalCircuit: one horizontal line per mode,
components placed left to right in the order they act."""
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def draw_circuit(circ):
    n = circ.n_modes
    k = max(len(circ.components), 1)
    fig, ax = plt.subplots(figsize=(max(6.0, 1.2 * k + 2.5), 0.9 * n + 1.2))

    def y(mode):  # mode 0 at the top
        return n - 1 - mode

    x_end = k + 1
    for m in range(n):
        ax.plot([0.3, x_end], [y(m), y(m)], color="gray", lw=1.5, zorder=1)
        ax.text(0.1, y(m), f"Mode {m}", ha="right", va="center", fontsize=9)

    for idx, comp in enumerate(circ.components, 1):
        if comp.kind == "BS":
            a, b = comp.modes
            ax.plot([idx, idx], [y(a), y(b)], color="tab:blue", lw=2, zorder=2)
            for m in (a, b):
                ax.plot(idx, y(m), "o", color="tab:blue", ms=9, zorder=3)
            ax.text(idx + 0.12, (y(a) + y(b)) / 2, f"BS\n\u03b8={comp.param:.2f}",
                    fontsize=8, va="center", color="tab:blue")
        else:
            m = comp.modes[0]
            ax.add_patch(Rectangle((idx - 0.28, y(m) - 0.22), 0.56, 0.44,
                                   facecolor="white", edgecolor="tab:orange",
                                   lw=2, zorder=3))
            ax.text(idx, y(m), "PS", ha="center", va="center", fontsize=8, zorder=4)
            ax.text(idx, y(m) + 0.38, f"\u03c6={comp.param:.2f}", ha="center",
                    fontsize=8, color="tab:orange")

    ax.set_xlim(-0.8, x_end + 0.4)
    ax.set_ylim(-0.7, n - 0.3)
    ax.axis("off")
    fig.tight_layout()
    return fig
