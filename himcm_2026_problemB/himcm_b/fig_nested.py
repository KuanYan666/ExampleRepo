"""Nested boundaries + the sign of waste."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

BLUE, ORANGE, AQUA, RED, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#e34948", "#eda100"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
SURF, BASE, GRID = "#fcfcfb", "#c3c2b7", "#e1e0d9"
plt.rcParams.update({"font.family": "sans-serif", "figure.facecolor": SURF,
                     "savefig.facecolor": SURF, "text.color": INK,
                     "axes.facecolor": SURF, "axes.edgecolor": BASE,
                     "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.grid": True, "grid.color": GRID, "axes.axisbelow": True})

fig = plt.figure(figsize=(15.0, 7.0))
gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0], wspace=0.16,
                      left=0.03, right=0.975, top=0.80, bottom=0.14)

# ---------------------------------------------------------------- (a) nested
ax = fig.add_subplot(gs[0]); ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
ax.text(0, 10.75, "(a)  Three boxes inside each other — and every wall leaks",
        fontsize=12.8, color=INK, fontweight="bold", va="bottom")

ax.add_patch(FancyBboxPatch((0.25, 0.9), 9.5, 8.2, boxstyle="round,pad=0.1",
                            fc="#fdf2ec", ec=ORANGE, lw=2.0, ls="--"))
ax.text(0.65, 8.62, "OUTDOORS   32 °C, humid", fontsize=10.5, color=ORANGE,
        fontweight="bold")

ax.add_patch(FancyBboxPatch((1.3, 1.9), 7.4, 6.0, boxstyle="round,pad=0.1",
                            fc="#eef4fd", ec=BLUE, lw=2.2))
ax.text(1.7, 7.42, "THE SHOP   24 °C", fontsize=10.5, color=BLUE, fontweight="bold")

ax.add_patch(FancyBboxPatch((2.5, 3.0), 5.0, 3.2, boxstyle="round,pad=0.1",
                            fc="#e3f6ef", ec=AQUA, lw=2.2))
ax.text(5.0, 5.72, "THE FREEZER CASE", ha="center", fontsize=10.5, color=AQUA,
        fontweight="bold")
ax.text(5.0, 4.75, "−18 °C", ha="center", fontsize=19, color=AQUA, fontweight="bold")
ax.text(5.0, 3.85, "open front", ha="center", fontsize=8.8, color=MUTED, style="italic")

# the shop's front door
ax.add_patch(FancyBboxPatch((1.15, 3.6), 0.32, 1.5, boxstyle="square,pad=0.02",
                            fc=YELLOW, ec="#9a6a00", lw=1.6))
ax.text(0.45, 3.0, "front\ndoor", fontsize=9, color="#9a6a00", fontweight="bold",
        ha="center", linespacing=1.3)
ax.add_patch(FancyArrowPatch((0.9, 4.35), (2.4, 4.35), arrowstyle="-|>",
                             mutation_scale=18, lw=3.0, color=ORANGE))

ax.text(5.0, 2.45, "humid outdoor air  →  humid shop air  →  more frost on the coil",
        ha="center", fontsize=9.5, color=INK2)

ax.text(5.0, 1.45, "The freezer NEVER touches the outside air.\n"
                   "Yet opening the shop door changes its bill by up to +27%.",
        ha="center", va="center", fontsize=10.5, color=RED, fontweight="bold",
        linespacing=1.45)

ax.text(9.35, 6.9, "+8%", fontsize=11, color=ORANGE, fontweight="bold", ha="right")
ax.text(9.35, 6.35, "+17%", fontsize=11, color=ORANGE, fontweight="bold", ha="right")
ax.text(9.35, 5.8, "+27%", fontsize=12, color=RED, fontweight="bold", ha="right")
ax.text(9.35, 7.45, "freezer load as the\nshop gets muggier:", fontsize=8.6,
        color=MUTED, ha="right", linespacing=1.3)

# ---------------------------------------------------------------- (b) sign of waste
ax2 = fig.add_subplot(gs[1])
ax2.set_title("(b)  Is the escaping cold actually waste?", fontsize=12.8,
              color=INK, fontweight="bold", pad=14, loc="left")
cats = ["Freezer\nin SUMMER", "Freezer\nin WINTER", "Bus shelter\n(any season)"]
vals = [-1.0, +1.0, -1.0]
cols = [RED, AQUA, RED]
notes = ["shop AC must\nremove it\n→ real waste",
         "it offsets the\nshop's heating\n→ RECOVERED",
         "it goes to the\nsky, for ever\n→ gone"]
x = np.arange(3)
ax2.bar(x, vals, width=0.55, color=cols, edgecolor=SURF, lw=2)
for xi, (v, n) in enumerate(zip(vals, notes)):
    ax2.text(xi, v + (0.14 if v > 0 else -0.14), n, ha="center",
             va="bottom" if v > 0 else "top", fontsize=9.2, color=INK2,
             linespacing=1.4)
ax2.axhline(0, color=BASE, lw=1.6)
ax2.set_xticks(x); ax2.set_xticklabels(cats, fontsize=9.6, color=INK2)
ax2.set_yticks([-1, 0, 1])
ax2.set_yticklabels(["waste", "neutral", "useful"], fontsize=10, color=INK2)
ax2.set_ylim(-1.95, 1.95); ax2.grid(axis="x", visible=False)
ax2.text(0.5, -0.22, "The same escaping cold has a different SIGN\n"
                     "depending on season and on where you draw the box.",
         transform=ax2.transAxes, ha="center", va="top", fontsize=9.8,
         color=INK, fontweight="bold", linespacing=1.45)

fig.suptitle("The supermarket door question — and why it breaks the obvious answer",
             fontsize=15.5, fontweight="bold", y=0.945)
fig.text(0.5, 0.035,
         "Nobody models the shop's front door as part of the freezer's efficiency. "
         "It is, and it is worth 27%. That is the kind of boundary question\n"
         "that decides whether the bus-shelter model is right too — because cold spilling onto a crowded pavement may not be waste at all.",
         ha="center", fontsize=10, color=INK2)
fig.savefig("figs/fig9_nested.png", dpi=165)
print("ok")
