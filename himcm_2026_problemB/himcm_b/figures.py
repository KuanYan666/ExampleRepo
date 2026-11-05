"""Teaching figures for Tasks 1 and 2. Palette from the validated reference set."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle, FancyBboxPatch
import numpy as np
import core as C

BLUE, ORANGE, AQUA, YELLOW, RED = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e34948"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
SURF, GRID, BASE = "#fcfcfb", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 11,
    "axes.edgecolor": BASE, "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.facecolor": SURF,
    "figure.facecolor": SURF, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "axes.axisbelow": True, "savefig.facecolor": SURF,
})
OUT = "figs/"
import os; os.makedirs(OUT, exist_ok=True)


# ---------------------------------------------------------------- FIG 1
def fig1_where_cold_goes():
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.2))
    panels = [
        (axes[0], "Open supermarket freezer case", 0.25, "67-85%",
         "measured, 5 studies", "cold air spills\ninto the aisle"),
        (axes[1], "Open-sided bus shelter", 0.255, "74%",
         "our model, fitted to\nCOMAP's own table", "cooled air blows\nout to the street"),
    ]
    for ax, title, phi, lost, src, caption in panels:
        ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
        ax.set_title(title, fontsize=13, color=INK, pad=14, fontweight="bold")
        # the box
        ax.add_patch(FancyBboxPatch((2.4, 5.0), 5.2, 3.3, boxstyle="round,pad=0.12",
                                    fc="#eef4fd", ec=BLUE, lw=2))
        ax.text(5.0, 7.4, "cooling produced", ha="center", fontsize=10.5, color=INK2)
        ax.text(5.0, 6.0, "100%", ha="center", fontsize=24, color=BLUE, fontweight="bold")
        # useful arrow straight down, well clear of the box
        ax.add_patch(FancyArrowPatch((5.0, 4.7), (5.0, 3.2), arrowstyle="-|>",
                                     mutation_scale=22, lw=3.4, color=AQUA))
        ax.text(4.6, 3.95, f"{phi*100:.0f}%", ha="right", fontsize=17,
                color=AQUA, fontweight="bold")
        ax.text(5.0, 2.45, "reaches the thing\nyou meant to cool", ha="center",
                va="top", fontsize=10.5, color=AQUA)
        # wasted flow out of both open sides
        ax.add_patch(FancyArrowPatch((7.6, 7.3), (9.6, 7.9), arrowstyle="-|>",
                                     mutation_scale=24, lw=4.0, color=ORANGE))
        ax.add_patch(FancyArrowPatch((7.6, 6.1), (9.6, 6.0), arrowstyle="-|>",
                                     mutation_scale=24, lw=4.0, color=ORANGE))
        ax.add_patch(FancyArrowPatch((2.4, 6.6), (0.4, 7.2), arrowstyle="-|>",
                                     mutation_scale=24, lw=4.0, color=ORANGE))
        ax.text(5.0, 9.35, lost + "  lost", ha="center", fontsize=19,
                color=ORANGE, fontweight="bold")
        ax.text(8.2, 4.35, caption, ha="center", fontsize=9.2, color=MUTED, style="italic")
        ax.text(5.0, 0.6, src, ha="center", fontsize=8.5, color=MUTED)
    fig.suptitle("Where does the cooling actually go?", fontsize=15,
                 color=INK, fontweight="bold", y=0.99)
    fig.text(0.5, 0.025, "Same physics, same answer: roughly three-quarters of the cooling "
             "never reaches a person. This is why COMAP opens with a freezer.",
             ha="center", fontsize=10, color=INK2)
    fig.tight_layout(rect=[0, 0.06, 1, 0.94])
    fig.savefig(OUT + "fig1_where_cold_goes.png", dpi=170)
    plt.close(fig)


# ---------------------------------------------------------------- FIG 2
def fig2_cooling_budget():
    cities = ["Las Vegas", "Phoenix", "Seville", "Houston", "Singapore"]
    wbd = [16.7, 15.8, 9.9, 3.6, 2.6]
    eps, phi = 0.85, 0.255
    at_outlet = [w * eps for w in wbd]
    delivered = [w * eps * phi for w in wbd]

    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    y = np.arange(len(cities))[::-1]
    ax.barh(y, wbd, height=0.62, color="#dbe8fa", edgecolor=SURF, lw=2,
            label="Physical ceiling (wet-bulb depression)")
    ax.barh(y, at_outlet, height=0.62, color=BLUE, edgecolor=SURF, lw=2,
            label="At the cooler's outlet  (× pad efficiency 0.85)")
    ax.barh(y, delivered, height=0.62, color=ORANGE, edgecolor=SURF, lw=2,
            label="Actually felt by a waiting person  (× capture 0.26)")
    for yi, (w, d) in zip(y, zip(wbd, delivered)):
        ax.text(w + 0.3, yi, f"{w:.1f} °C", va="center", fontsize=10, color=INK2)
        ax.text(d + 0.3, yi - 0.30, f"{d:.1f} °C", va="center", fontsize=9.5,
                color=ORANGE, fontweight="bold")
    ax.axvline(5.0, color=RED, lw=2, ls="--", zorder=5)
    ax.text(5.25, len(cities) - 0.35, "COMAP's claimed\n\"up to 5 °C\"",
            fontsize=9.5, color=RED, va="top")
    ax.set_yticks(y); ax.set_yticklabels(cities, color=INK, fontsize=11)
    ax.set_xlabel("Air-temperature drop available (°C)", fontsize=11)
    ax.set_xlim(0, 19); ax.grid(axis="y", visible=False)
    ax.set_title("The evaporative cooling budget, and how little survives",
                 fontsize=14, color=INK, fontweight="bold", pad=14)
    ax.legend(loc="lower right", frameon=False, fontsize=9.5, labelcolor=INK2)
    fig.text(0.012, 0.03, "Mean summer 2025 conditions (Open-Meteo). In Singapore the ceiling "
             "itself is 2.6 °C — the claimed 5 °C is thermodynamically impossible there.",
             fontsize=9.5, color=INK2)
    fig.tight_layout(rect=[0, 0.07, 1, 1])
    fig.savefig(OUT + "fig2_cooling_budget.png", dpi=170)
    plt.close(fig)


# ---------------------------------------------------------------- FIG 3
def fig3_psychrometric():
    fig, ax = plt.subplots(figsize=(10.5, 6.4))
    T = np.linspace(10, 50, 300)
    for rh, lab, tx in [(100, "100% RH  (saturation)", 17.0), (80, "80%", 21.0),
                        (60, "60%", 35.5), (40, "40%", 41.0), (20, "20%", 47.0)]:
        W = np.array([C.W_from_RH(t, rh) * 1000 for t in T])
        ax.plot(T, W, color=MUTED if rh == 100 else BASE,
                lw=2.2 if rh == 100 else 1.0, zorder=2)
        wl = C.W_from_RH(tx, rh) * 1000
        ax.text(tx, wl + 0.7, lab, fontsize=8.5, color=MUTED, va="bottom",
                ha="center", rotation=0,
                bbox=dict(fc=SURF, ec="none", pad=1.0))

    for (Ti, RHi, name, col, dy) in [(43, 12, "Phoenix  43 °C / 12% RH", BLUE, -2.1),
                                     (32, 80, "Singapore  32 °C / 80% RH", ORANGE, -2.1)]:
        Wi = C.W_from_RH(Ti, RHi) * 1000
        To, RHo, Wo = C.evaporative_cooler(Ti, RHi, 0.85)
        ax.add_patch(FancyArrowPatch((Ti, Wi), (To, Wo * 1000), arrowstyle="-|>",
                                     mutation_scale=22, lw=3.2, color=col, zorder=5))
        ax.plot([Ti], [Wi], "o", ms=11, color=col, mec=SURF, mew=2, zorder=6)
        ax.plot([To], [Wo * 1000], "s", ms=10, color=col, mec=SURF, mew=2, zorder=6)
        ax.text(Ti, Wi + dy, name, fontsize=10.5, color=col, fontweight="bold",
                ha="right" if Ti > 40 else "center", zorder=7,
                bbox=dict(fc=SURF, ec="none", pad=1.5))
        mx, my = (Ti + To) / 2, (Wi + Wo * 1000) / 2
        ax.text(mx, my + 1.6, f"{Ti-To:.1f} °C cooler", fontsize=10.5, color=col,
                fontweight="bold", ha="center", zorder=7,
                bbox=dict(fc=SURF, ec="none", pad=1.5))
    ax.set_xlabel("Dry-bulb temperature  (°C)  — what a normal thermometer reads", fontsize=11)
    ax.set_ylabel("Humidity ratio  W  (g water / kg dry air)", fontsize=11)
    ax.set_xlim(10, 50); ax.set_ylim(0, 33)
    ax.set_title("An evaporative cooler pushes air LEFT (cooler) and UP (wetter),\n"
                 "and must stop at the saturation curve",
                 fontsize=13.5, color=INK, fontweight="bold", pad=12)
    fig.text(0.012, 0.028,
             "Phoenix starts far below saturation, so the arrow is long. Singapore starts almost "
             "on the curve, so there is nowhere to go.\nSame machine, same electricity: "
             "18.8 °C of cooling versus 2.6 °C.", fontsize=9.8, color=INK2)
    fig.tight_layout(rect=[0, 0.1, 1, 1])
    fig.savefig(OUT + "fig3_psychrometric.png", dpi=170)
    plt.close(fig)


# ---------------------------------------------------------------- FIG 4
def fig4_apples_oranges():
    fig, ax = plt.subplots(figsize=(10.5, 5.4))
    labels = ["A. Fan\n0.25 kW", "B. Evaporative\n1.2 kW", "C. Large evaporative\n2.5 kW"]
    claimed = [3.0, 5.0, 8.0]
    kind = ["FELT", "AIR", "AIR"]
    x = np.arange(3)
    bars = ax.bar(x, claimed, width=0.52, color=[AQUA, BLUE, BLUE],
                  edgecolor=SURF, lw=2)
    for xi, (c, k) in enumerate(zip(claimed, kind)):
        ax.text(xi, c + 0.18, f"{c:.0f} °C", ha="center", fontsize=15,
                fontweight="bold", color=INK)
        ax.text(xi, c + 0.95, f"a {k} temperature", ha="center", fontsize=10,
                color=AQUA if k == "FELT" else BLUE, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=10.5, color=INK)
    ax.set_ylabel("Claimed effect (°C)", fontsize=11)
    ax.set_ylim(0, 10.6); ax.grid(axis="x", visible=False)
    ax.set_title("The trap in COMAP's table: these three numbers are not the same quantity",
                 fontsize=13.5, color=INK, fontweight="bold", pad=14)
    ax.annotate("", xy=(0.28, 9.4), xytext=(1.72, 9.4),
                arrowprops=dict(arrowstyle="<->", color=RED, lw=2))
    ax.text(1.0, 9.65, "you cannot compare these until you convert one into the other",
            ha="center", fontsize=10.5, color=RED, fontweight="bold")
    fig.text(0.012, 0.03,
             "A fan changes no air property at all — it changes how your skin loses heat. "
             "The coolers change the air itself.\nConverting between them is the single "
             "highest-value move available in Task 2a.", fontsize=9.8, color=INK2)
    fig.tight_layout(rect=[0, 0.09, 1, 1])
    fig.savefig(OUT + "fig4_apples_oranges.png", dpi=170)
    plt.close(fig)


# ---------------------------------------------------------------- FIG 5
def fig5_task2b():
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.4))
    specs = [
        (axes[0], "2a  Open bus shelter", 0.26, 3, 0.3,
         ["3 sides open", "wind blows through", "3 people = 300 W", "people are NEGLIGIBLE"],
         AQUA),
        (axes[1], "2b  Semi-open rail platform", 0.55, 200, 20.0,
         ["walls + roof", "air exchange at the ends", "200 people = 20 kW",
          "people DOMINATE the heat load"], ORANGE),
    ]
    for ax, title, phi, n, kw, bullets, col in specs:
        ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
        ax.set_title(title, fontsize=13, color=INK, fontweight="bold", pad=12)
        ax.add_patch(FancyBboxPatch((1.2, 4.4), 7.6, 3.6, boxstyle="round,pad=0.1",
                                    fc="#f4f8fd", ec=col, lw=2.2))
        ax.text(5.0, 7.2, f"capture fraction  φ = {phi:.2f}", ha="center",
                fontsize=12, color=col, fontweight="bold")
        ax.text(5.0, 6.3, f"{n} people waiting", ha="center", fontsize=11, color=INK2)
        ax.text(5.0, 5.3, f"body heat:  {kw:.1f} kW", ha="center", fontsize=13,
                color=INK, fontweight="bold")
        ax.text(5.0, 4.75, "(compare: biggest cooler = 2.5 kW)", ha="center",
                fontsize=9, color=MUTED, style="italic")
        for i, b in enumerate(bullets):
            weight = "bold" if i == len(bullets) - 1 else "normal"
            c = col if i == len(bullets) - 1 else INK2
            ax.text(1.4, 3.5 - i * 0.72, "•  " + b, fontsize=10.5, color=c, fontweight=weight)
    fig.suptitle("Task 2b: what actually changes — and why it needs a NEW model, not a tweak",
                 fontsize=14, color=INK, fontweight="bold", y=0.99)
    fig.text(0.5, 0.025, "At the bus stop people RECEIVE cooling. On the platform they receive it "
             "AND generate the dominant heat load.\nThat makes efficiency non-linear in crowd size — "
             "a structural change, which is exactly what COMAP asks you to justify.",
             ha="center", fontsize=10, color=INK2)
    fig.tight_layout(rect=[0, 0.08, 1, 0.93])
    fig.savefig(OUT + "fig5_task2b.png", dpi=170)
    plt.close(fig)


for f in (fig1_where_cold_goes, fig2_cooling_budget, fig3_psychrometric,
          fig4_apples_oranges, fig5_task2b):
    f(); print("wrote", f.__name__)
