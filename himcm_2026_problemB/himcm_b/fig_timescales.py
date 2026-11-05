"""Timescale map: which parts of the problem deserve a differential equation."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BLUE, ORANGE, AQUA, RED, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#e34948", "#eda100"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
SURF, BASE, GRID = "#fcfcfb", "#c3c2b7", "#e1e0d9"
plt.rcParams.update({"font.family": "sans-serif", "figure.facecolor": SURF,
                     "savefig.facecolor": SURF, "text.color": INK,
                     "axes.facecolor": SURF, "axes.edgecolor": BASE,
                     "xtick.color": MUTED, "ytick.color": MUTED})

fig, ax = plt.subplots(figsize=(14.0, 6.6))
fig.subplots_adjust(left=0.165, right=0.975, top=0.78, bottom=0.21)

items = [
    ("One door opening",      8.0,      ORANGE, "average it into a rate\n(don't simulate each one)", "R"),
    ("Air inside the case",   54.0,     BLUE,   "settles instantly\n→ plain algebra", "R"),
    ("Shop air",              1800.0,   AQUA,   "borderline → ODE only if\nyou want within-day detail", "L"),
    ("The FOOD itself",       4000.0,   RED,    "ODE — and this IS\nthe service you sell", "R"),
    ("Frost on the coil",     21600.0,  "#6250d6", "ODE — this is what makes\nefficiency a sawtooth", "L"),
]

y = np.arange(len(items))[::-1]
for yi, (name, tau, col, advice, side) in zip(y, items):
    ax.plot([1, tau], [yi, yi], color=col, lw=3.0, alpha=0.30, solid_capstyle="round")
    ax.plot([tau], [yi], "o", ms=16, color=col, mec=SURF, mew=2.5, zorder=5)
    lab = f"{tau:.0f} s" if tau < 90 else (f"{tau/60:.0f} min" if tau < 5400 else f"{tau/3600:.0f} h")
    xp, ha = (tau * 1.4, "left") if side == "R" else (tau * 0.72, "right")
    ax.text(xp, yi + 0.17, lab, fontsize=10.5, color=col, fontweight="bold", ha=ha)
    ax.text(xp, yi - 0.26, advice, fontsize=8.8, color=INK2, va="top", ha=ha,
            linespacing=1.35)

ax.axvspan(2400, 5400, color=YELLOW, alpha=0.16, zorder=0)
ax.axvline(3600, color="#9a6a00", lw=2.2, ls="--", zorder=1)
ax.text(3600, len(items) - 0.26, "  1 HOUR\n  your weather data\n  arrives this often",
        fontsize=10, color="#9a6a00", fontweight="bold", va="top", linespacing=1.4)

ax.set_yticks(y)
ax.set_yticklabels([i[0] for i in items], fontsize=11.5, color=INK)
ax.set_xscale("log")
ax.set_xlim(3, 400000)
ax.set_ylim(-0.75, len(items) - 0.35)
ax.set_xlabel("How long this part of the system takes to respond   (log scale)",
              fontsize=11.5)
ax.set_xticks([10, 60, 600, 3600, 86400])
ax.set_xticklabels(["10 s", "1 min", "10 min", "1 hour", "1 day"], fontsize=10.5)
ax.grid(axis="x", color=GRID, lw=0.9)
ax.set_axisbelow(True)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)

ax.text(0.5, -0.20,
        "RULE:   much faster than your data  →  it has already settled, use algebra"
        "        ·        similar to your data  →  it needs a differential equation\n"
        "much faster but repeating over and over  →  replace it with an average rate",
        transform=ax.transAxes, ha="center", va="top", fontsize=10.0, color=INK,
        fontweight="bold", linespacing=1.6)

fig.suptitle("Does this need a differential equation?  Measure the time constants and find out",
             fontsize=15.5, fontweight="bold", y=0.945)
fig.text(0.5, 0.885,
         "Only two states here are slow enough to deserve one — the food and the frost. "
         "Everything else is algebra or an average.",
         ha="center", fontsize=11, color=INK2)
fig.savefig("figs/fig10_timescales.png", dpi=165)
print("ok")
