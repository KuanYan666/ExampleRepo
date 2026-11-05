"""The spine of the paper: what you are cooling changes, so the measure must change."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
SURF, BASE = "#fcfcfb", "#c3c2b7"
plt.rcParams.update({"font.family": "sans-serif", "figure.facecolor": SURF,
                     "savefig.facecolor": SURF, "text.color": INK})

fig, axes = plt.subplots(1, 3, figsize=(14.5, 6.4))
fig.subplots_adjust(left=0.03, right=0.97, top=0.76, bottom=0.14, wspace=0.14)

panels = [
    (BLUE, "TASK 1", "The freezer", "Food",
     "ACTUAL\ntemperature",
     ["Food does not sweat.", "Food does not feel wind.",
      "A chicken at −18 °C is at", "−18 °C, full stop."],
     "You need:\na thermometer",
     "A fan makes food\ncool down FASTER\n— but not colder."),
    (ORANGE, "TASK 2a", "The bus stop", "One person",
     "FELT\ntemperature",
     ["People sweat.", "Wind and sun change how", "hot they feel — even when",
      "the thermometer doesn't move."],
     "You need:\ntemperature + humidity\n+ wind + sun",
     "A fan makes a person\nFEEL cooler\n— without cooling the air."),
    (AQUA, "TASK 2b", "The train station", "A crowd",
     "FELT temperature\n+ the crowd's own heat",
     ["Same as the bus stop, but", "200 people give off 20 kW.",
      "They are being cooled AND", "they are heating the room."],
     "You need:\nall of the above\n+ a headcount",
     "The people become\npart of the problem,\nnot just the point of it."),
]

for ax, (col, tag, title, who, cares, bullets, need, punch) in zip(axes, panels):
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    ax.text(5, 10.7, tag, ha="center", fontsize=11, color=col, fontweight="bold")
    ax.text(5, 9.9, title, ha="center", fontsize=16, color=INK, fontweight="bold")

    ax.add_patch(FancyBboxPatch((0.6, 6.0), 8.8, 2.6, boxstyle="round,pad=0.14",
                                fc="#f4f7fb", ec=col, lw=2.2))
    ax.text(5, 8.05, f"What you are cooling:  {who}", ha="center", fontsize=10.5,
            color=INK2)
    ax.text(5, 6.9, cares, ha="center", va="center", fontsize=13.5, color=col,
            fontweight="bold", linespacing=1.35)

    for i, b in enumerate(bullets):
        ax.text(0.7, 5.2 - i * 0.62, b, fontsize=10.2, color=INK2)

    ax.add_patch(FancyBboxPatch((0.6, 1.45), 8.8, 1.25, boxstyle="round,pad=0.12",
                                fc=SURF, ec=BASE, lw=1.4))
    ax.text(5, 2.07, need, ha="center", va="center", fontsize=10.5, color=INK,
            linespacing=1.4)

    ax.text(5, 0.95, punch, ha="center", va="top", fontsize=10, color=col,
            style="italic", linespacing=1.35)

for i in (0, 1):
    fig.add_artist(FancyArrowPatch((0.345 + i * 0.3133, 0.50), (0.372 + i * 0.3133, 0.50),
                                   transform=fig.transFigure, arrowstyle="-|>",
                                   mutation_scale=30, lw=3.5, color=MUTED))

fig.suptitle("What are we actually cooling? That is what changes — and so the measure must change",
             fontsize=15.5, fontweight="bold", y=0.945)
fig.text(0.5, 0.035,
         "This is the spine of the whole paper. Task 1 is easy because food has no feelings. "
         "The moment the target is a person, a thermometer is no longer enough.",
         ha="center", fontsize=10.5, color=INK2)
fig.savefig("figs/fig7_what_changes.png", dpi=170)
print("ok")
