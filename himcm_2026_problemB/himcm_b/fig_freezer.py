"""One figure for Task 1: energy conservation in an open freezer case, and why
the textbook model misses the point."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np

BLUE, ORANGE, AQUA, YELLOW, RED = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e34948"
GOLD = "#9a6a00"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
SURF, GRID, BASE = "#fcfcfb", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 11,
    "axes.edgecolor": BASE, "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.facecolor": SURF,
    "figure.facecolor": SURF, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "axes.axisbelow": True, "savefig.facecolor": SURF,
})

fig = plt.figure(figsize=(14.0, 6.8))
gs = fig.add_gridspec(1, 2, width_ratios=[1.1, 1.0], wspace=0.20,
                      left=0.045, right=0.985, top=0.80, bottom=0.17)

# ---------------------------------------------------------------- (a) energy balance
ax = fig.add_subplot(gs[0]); ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")

ax.text(0, 10.6, "(a)  Energy is conserved — a freezer MOVES heat, it never destroys it",
        fontsize=12.5, color=INK, fontweight="bold", va="bottom")

ax.text(5.0, 9.1, "2.50  +  1.47  =  3.97 kW", ha="center", fontsize=17,
        color=INK, fontweight="bold")
ax.text(5.0, 8.4, "heat removed   +   work done   =   heat rejected", ha="center",
        fontsize=9.5, color=INK2)

ax.add_patch(FancyBboxPatch((3.6, 4.1), 2.9, 2.9, boxstyle="round,pad=0.12",
                            fc="#eef4fd", ec=BLUE, lw=2.2))
ax.text(5.05, 6.25, "FREEZER CASE", ha="center", fontsize=10.5, color=BLUE,
        fontweight="bold")
ax.text(5.05, 5.25, "−18 °C", ha="center", fontsize=21, color=BLUE, fontweight="bold")
ax.text(5.05, 4.5, "steady state", ha="center", fontsize=8.5, color=MUTED, style="italic")

# heat in (horizontal)
ax.add_patch(FancyArrowPatch((0.5, 5.55), (3.5, 5.55), arrowstyle="-|>",
                             mutation_scale=24, lw=5.0, color=ORANGE))
ax.text(1.95, 6.0, "2.50 kW", ha="center", fontsize=13.5, color=ORANGE, fontweight="bold")
ax.text(1.95, 4.85, "leaks in from\nthe aisle", ha="center", va="top",
        fontsize=9.5, color=ORANGE)

# heat out (horizontal, thicker)
ax.add_patch(FancyArrowPatch((6.6, 5.55), (9.6, 5.55), arrowstyle="-|>",
                             mutation_scale=26, lw=6.4, color=RED))
ax.text(8.1, 6.0, "3.97 kW", ha="center", fontsize=14.5, color=RED, fontweight="bold")
ax.text(8.1, 4.85, "dumped at the\ncondenser", ha="center", va="top",
        fontsize=9.5, color=RED)

# electricity in (vertical)
ax.add_patch(FancyArrowPatch((5.05, 2.35), (5.05, 3.95), arrowstyle="-|>",
                             mutation_scale=22, lw=4.2, color=YELLOW))
ax.text(5.55, 3.05, "1.47 kW", fontsize=13, color=GOLD, fontweight="bold", va="center")
ax.text(5.05, 1.95, "electricity in   (COP 1.7)", ha="center", va="top",
        fontsize=9.5, color=GOLD)

ax.text(5.0, 0.75, "Put that condenser inside the shop and the store's air conditioning\n"
                   "must remove 3.97 kW — a further 1.32 kW of electricity.",
        ha="center", va="top", fontsize=9.3, color=INK2, style="italic")

# ---------------------------------------------------------------- (b) load breakdown
ax2 = fig.add_subplot(gs[1])
labels = ["Infiltration\nSENSIBLE", "Infiltration\nLATENT", "Conduction",
          "Radiation", "Lights, fans,\ndefrost"]
sub = ["chilling the air", "drying it + frost", "through walls", "into the opening", ""]
vals = [1.15, 0.73, 0.15, 0.15, 0.33]
cols = [ORANGE, ORANGE, BLUE, BLUE, BLUE]
alphas = [1.0, 0.60, 1.0, 1.0, 1.0]
x = np.arange(len(vals))
for xi, (v, c, a) in enumerate(zip(vals, cols, alphas)):
    ax2.bar(xi, v, width=0.66, color=c, alpha=a, edgecolor=SURF, lw=2)
    ax2.text(xi, v + 0.035, f"{v:.2f} kW", ha="center", fontsize=10.5,
             color=INK, fontweight="bold")
    ax2.text(xi, v + 0.145, f"{100*v/2.5:.0f}%", ha="center", fontsize=9, color=MUTED)
labels = ["Infiltration\nSENSIBLE\n(chilling the air)", "Infiltration\nLATENT\n(drying + frost)",
          "Conduction\n(through walls)", "Radiation\n(into the opening)", "Lights, fans,\ndefrost"]
ax2.set_xticks(x); ax2.set_xticklabels(labels, fontsize=8.6, color=INK2)
ax2.tick_params(axis="x", pad=6)
ax2.set_ylabel("Share of the 2.50 kW cooling load  (kW)", fontsize=10.5)
ax2.set_ylim(0, 1.62); ax2.grid(axis="x", visible=False)
ax2.set_title("(b)  Where that 2.50 kW comes from", fontsize=12.5, color=INK,
              fontweight="bold", pad=26, loc="left")
ax2.annotate("", xy=(-0.36, 1.45), xytext=(1.36, 1.45),
             arrowprops=dict(arrowstyle="<->", color=ORANGE, lw=2))
ax2.text(0.5, 1.50, "THE OPEN DOOR  =  75%", ha="center", fontsize=11.5,
         color=ORANGE, fontweight="bold")

fig.text(0.045, 0.055,
         "A textbook model asks \"how efficient is the machine?\" — COP 1.7 against a Carnot ceiling of 4.8. "
         "But three-quarters of the load should never have existed.\n"
         "Improving the machine is capped by the second law. Removing the load is not capped at all. "
         "That gap is the whole of Task 1.",
         fontsize=10, color=INK2)
fig.savefig("figs/fig6_freezer.png", dpi=170)
print("wrote figs/fig6_freezer.png")
