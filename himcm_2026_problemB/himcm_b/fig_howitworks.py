"""How the three cooling machines actually work, mechanically."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Ellipse

BLUE, ORANGE, AQUA, RED, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#e34948", "#eda100"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
SURF, BASE = "#fcfcfb", "#c3c2b7"
plt.rcParams.update({"font.family": "sans-serif", "figure.facecolor": SURF,
                     "savefig.facecolor": SURF, "text.color": INK})

fig, axes = plt.subplots(1, 3, figsize=(15.2, 7.4))
fig.subplots_adjust(left=0.02, right=0.98, top=0.80, bottom=0.13, wspace=0.10)
for ax in axes:
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")

# ================================================== A: the fridge / freezer / AC
ax = axes[0]
ax.text(5, 10.9, "1.  FREEZER  /  AIR CONDITIONER", ha="center", fontsize=12,
        color=BLUE, fontweight="bold")
ax.text(5, 10.15, "moves heat using a boiling liquid", ha="center", fontsize=10, color=INK2)

boxes = [
    (0.4, 6.6, 4.1, 2.0, AQUA, "① BOIL  (inside)",
     "liquid boils at −25 °C\nboiling SUCKS IN heat\n→ the food gets cold"),
    (5.5, 6.6, 4.1, 2.0, RED, "② SQUEEZE",
     "a pump compresses the gas\nsqueezing makes it HOT\n(hotter than the room)"),
    (5.5, 2.5, 4.1, 2.0, ORANGE, "③ CONDENSE  (outside)",
     "now hotter than the room,\nso heat flows OUT by itself\n→ gas turns back to liquid"),
    (0.4, 2.5, 4.1, 2.0, BLUE, "④ RELEASE",
     "liquid squirts through a\nnarrow valve and expands\n→ it goes cold again"),
]
for (x, y, w, h, c, t, s) in boxes:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                                fc="#f5f8fc", ec=c, lw=2))
    ax.text(x + w / 2, y + h - 0.42, t, ha="center", fontsize=9.6, color=c,
            fontweight="bold")
    ax.text(x + w / 2, y + 0.62, s, ha="center", fontsize=8.6, color=INK2,
            linespacing=1.45)
for a, b in [((4.5, 7.6), (5.4, 7.6)), ((7.55, 6.5), (7.55, 4.6)),
             ((5.4, 3.5), (4.6, 3.5)), ((2.45, 4.6), (2.45, 6.5))]:
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=18,
                                 lw=2.4, color=MUTED))
ax.text(5.0, 5.55, "round and round, for ever", ha="center", fontsize=9,
        color=MUTED, style="italic")
ax.text(5.0, 1.55, "THE TRICK: heat won't flow from cold to hot on its own.\n"
                   "So you squeeze the gas until it's hotter than the room —\n"
                   "then the heat leaves all by itself. The squeezing is what\n"
                   "costs electricity.", ha="center", va="top", fontsize=9.2,
        color=INK, linespacing=1.5)

# ================================================== B: evaporative cooler
ax = axes[1]
ax.text(5, 10.9, "2.  EVAPORATIVE COOLER", ha="center", fontsize=12,
        color=ORANGE, fontweight="bold")
ax.text(5, 10.15, "a fan blowing through a wet sponge", ha="center", fontsize=10, color=INK2)

ax.add_patch(FancyBboxPatch((4.0, 4.4), 2.0, 4.2, boxstyle="round,pad=0.06",
                            fc="#d9eef5", ec=BLUE, lw=2))
ax.text(5.0, 8.95, "wet pad", ha="center", fontsize=9.5, color=BLUE, fontweight="bold")
for yy in (5.0, 5.8, 6.6, 7.4, 8.1):
    ax.plot([4.35, 5.65], [yy, yy], color=BLUE, lw=1.0, alpha=0.5)

ax.add_patch(FancyArrowPatch((0.4, 6.5), (3.9, 6.5), arrowstyle="-|>",
                             mutation_scale=22, lw=4.5, color=RED))
ax.text(2.1, 7.5, "HOT  DRY  air", ha="center", fontsize=10.5, color=RED,
        fontweight="bold")
ax.text(2.1, 6.95, "43 °C,  12% wet", ha="center", fontsize=9, color=RED)

ax.add_patch(FancyArrowPatch((6.1, 6.5), (9.6, 6.5), arrowstyle="-|>",
                             mutation_scale=22, lw=4.5, color=AQUA))
ax.text(7.9, 7.5, "COOL  DAMP  air", ha="center", fontsize=10.5, color=AQUA,
        fontweight="bold")
ax.text(7.9, 6.95, "24 °C,  75% wet", ha="center", fontsize=9, color=AQUA)

ax.text(5.0, 3.85, "water evaporating\nsteals the heat", ha="center", va="top",
        fontsize=9.2, color=BLUE, style="italic")

ax.text(5.0, 2.55, "THE TRICK: turning water into vapour needs a LOT of\n"
                   "energy — 600× more than warming it by one degree.\n"
                   "That energy is stolen straight out of the air,\n"
                   "so the air comes out colder.", ha="center", va="top",
        fontsize=9.2, color=INK, linespacing=1.5)
ax.text(5.0, 0.75, "Useless in a humid place: if the air is already\nfull of water, "
                   "nothing evaporates.", ha="center", va="top", fontsize=9.2,
        color=ORANGE, fontweight="bold", linespacing=1.5)

# ================================================== C: the fan
ax = axes[2]
ax.text(5, 10.9, "3.  FAN", ha="center", fontsize=12, color=AQUA, fontweight="bold")
ax.text(5, 10.15, "changes nothing about the air — changes YOU",
        ha="center", fontsize=10, color=INK2)

ax.add_patch(Ellipse((6.6, 6.6), 3.3, 4.3, fc="#fde9e0", ec=ORANGE, lw=1.6, ls="--"))
ax.add_patch(Circle((6.6, 7.9), 0.52, fc="#ffd9c4", ec=INK2, lw=1.4))
ax.plot([6.6, 6.6], [7.3, 5.6], color=INK2, lw=2.6)
ax.plot([6.6, 5.9], [5.6, 4.7], color=INK2, lw=2.2)
ax.plot([6.6, 7.3], [5.6, 4.7], color=INK2, lw=2.2)
ax.text(8.9, 8.4, "your own warm,\ndamp 'blanket'\nof air", ha="center",
        fontsize=8.8, color=ORANGE, linespacing=1.4)
ax.text(6.6, 4.25, "skin ≈ 35 °C\ngiving off ~100 W", ha="center", va="top",
        fontsize=8.8, color=INK2, linespacing=1.4)

for yy in (6.2, 7.0, 7.8):
    ax.add_patch(FancyArrowPatch((0.5, yy), (4.5, yy), arrowstyle="-|>",
                                 mutation_scale=16, lw=2.6, color=AQUA))
ax.text(2.4, 8.7, "fan blows the\nblanket away", ha="center", fontsize=9.5,
        color=AQUA, fontweight="bold", linespacing=1.4)

ax.text(5.0, 3.3, "THE TRICK: standing still, your body wraps itself in a\n"
                  "layer of warm damp air. A fan strips that layer off and\n"
                  "replaces it with fresh air — so your sweat evaporates\n"
                  "faster, and that is what cools you.", ha="center", va="top",
        fontsize=9.2, color=INK, linespacing=1.5)
ax.text(5.0, 1.2, "THE CATCH: above about 35 °C the air is hotter than\n"
                  "your skin, so the fan blows heat INTO you. A fan oven.",
        ha="center", va="top", fontsize=9.2, color=RED, fontweight="bold",
        linespacing=1.5)

fig.suptitle("How the three machines actually work", fontsize=16, fontweight="bold", y=0.955)
fig.text(0.5, 0.035, "Only the first one truly removes heat from a place. "
         "The second swaps heat for humidity. The third moves no heat at all — it works on your skin.",
         ha="center", fontsize=10.5, color=INK2)
fig.savefig("figs/fig8_how_it_works.png", dpi=165)
print("ok")
