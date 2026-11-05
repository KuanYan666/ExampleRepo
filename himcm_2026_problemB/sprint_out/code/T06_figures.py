"""T06 figures: limiting-case scorecard, air-curtain fan sweep, bus-shelter carry-over."""
import os, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import T06_metrics as TM
import T06_bus_carryover as TB

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "figs")
os.makedirs(FIG, exist_ok=True)

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
STATUS = {"PASS": "#0ca30c", "FAIL": "#d03b3b", "BLIND": "#9a9890", "CONFOUNDED": "#fab219", "NEUTRAL": "#2a78d6"}
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})

# ------------------------------------------------------------------ Figure 1: scorecard
M, P = TM.table()
base = M.iloc[0]
HIGHER_BETTER = {"2a COP machine", "2b Heat removed per kWh (system COP)", "3 2nd-law eff. (system COP / Carnot)",
                 "5 Service kg.h per kWh", "6 Capture phi = 1 - Q_inf/Q_tot", "7 Benchmark E_doors/E",
                 "9 Net benefit $/day (vs. losing the stock)"}
ROWS = ["1 Energy/day (kWh/d)", "2a COP machine", "2b Heat removed per kWh (system COP)",
        "3 2nd-law eff. (system COP / Carnot)", "4 kWh/d per m2 TDA", "5 Service kg.h per kWh",
        "6 Capture phi = 1 - Q_inf/Q_tot", "7 Benchmark E_doors/E", "9 Net benefit $/day (vs. losing the stock)",
        "10a CO2e kg/day"]
ROWLAB = ["(1) Energy per day", "(2a) Machine COP", "(2b) Heat removed per kWh", "(3) 2nd-law efficiency",
          "(4) kWh/day per m² display", "(5) kg·h in safe band per kWh", "(6) Capture fraction φ",
          "(7) Benchmark E_doors / E", "(9) Net benefit $/day", "(10) CO2e per day",
          "RECOMMENDED: (5) + full-cycle rule\n+ standard store conditions"]
# what common sense says the score should do, relative to baseline
EXPECT = {"Switched off": "worse", "Empty case": "worse", "Doors fitted": "better", "Night cover 12 h": "better",
          "Winter store (21 C/30 %, Tcond 25 C)": "same", "Very humid store (24 C/75 %)": "same",
          "Air-curtain fan +50 % flow": "worse", "Extra 0.3 kW lights inside": "worse",
          "Aisle draft: infiltration x1.3": "worse", "Draft x1.3, oversized coil": "worse"}
COLLAB = ["Switched\noff", "Empty\ncase", "Doors\nfitted", "Night\ncover 12 h", "Winter\nstore", "Very humid\nstore",
          "Curtain fan\n+50 %", "+0.3 kW\nlights", "Aisle draft\n×1.3", "Draft ×1.3\nbig coil"]


def verdict(metric, scen):
    b, v = base[metric], M.loc[scen, metric]
    exp = EXPECT[scen]
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "FAIL", "undefined"
    if math.isinf(v):
        return "FAIL", "infinite"
    if b == 0:
        ch = 0.0 if v == 0 else math.copysign(1, v)
    else:
        ch = (v - b) / abs(b)
    better = ch > 0 if metric in HIGHER_BETTER else ch < 0
    txt = f"{ch:+.0%}" if abs(ch) < 10 else f"{v:,.0f} vs {b:,.1f}"
    if exp == "same":
        return ("CONFOUNDED" if abs(ch) > 0.05 else "NEUTRAL"), txt
    if abs(ch) < 0.01:
        return "BLIND", txt
    ok = better if exp == "better" else (not better)
    return ("PASS" if ok else "FAIL"), txt


fig, ax = plt.subplots(figsize=(12.5, 6.4))
scen = list(EXPECT)
for i, met in enumerate(ROWS + ["REC"]):
    for j, sc in enumerate(scen):
        if met == "REC":
            if sc == "Switched off":
                s, t = "PASS", "0 (stock lost)"
            elif EXPECT[sc] == "same":
                s, t = "NEUTRAL", "rated at std.\nconditions: 0%"
            else:
                s, t = verdict("5 Service kg.h per kWh", sc)
        else:
            s, t = verdict(met, sc)
        ax.add_patch(plt.Rectangle((j + 0.03, i + 0.05), 0.94, 0.9, color=STATUS[s], alpha=0.28, lw=0))
        ax.text(j + 0.5, i + 0.5, f"{s}\n{t}", ha="center", va="center", fontsize=7.2, color=INK)
ax.set_xlim(0, len(scen)); ax.set_ylim(len(ROWS) + 1, 0)
ax.set_xticks(np.arange(len(scen)) + 0.5); ax.set_xticklabels(COLLAB, fontsize=8)
ax.xaxis.tick_top()
ax.set_yticks(np.arange(len(ROWS) + 1) + 0.5); ax.set_yticklabels(ROWLAB, fontsize=8.5)
for sp in ax.spines.values(): sp.set_visible(False)
ax.tick_params(length=0)
ax.axhline(len(ROWS) + 0.02, color=INK, lw=1.2)
expect_txt = "  ".join([f"{c.split(chr(10))[0]}: {EXPECT[s]}" for c, s in zip(COLLAB, scen)])
ax.set_title("Limiting-case scorecard for 10 candidate freezer-efficiency measures\n"
             "(cell = change vs. baseline 2.5 m open freezer case; verdict = does the score move the way common sense requires?)",
             fontsize=10.5, color=INK, pad=42, loc="left")
leg = [Patch(color=STATUS[k], alpha=0.5, label=l) for k, l in
       [("PASS", "PASS: moves the right way"), ("FAIL", "FAIL: wrong way, undefined or infinite"),
        ("BLIND", "BLIND: changes < 1 %"), ("CONFOUNDED", "CONFOUNDED: credits/blames the case for the weather (>5 %)"),
        ("NEUTRAL", "NEUTRAL: unchanged, as it should be")]]
fig.legend(handles=leg, loc="lower center", ncol=3, frameon=False, fontsize=8, bbox_to_anchor=(0.55, -0.01))
fig.text(0.01, 0.085, "Expected direction:  worse = off, empty, curtain fan +50 %, extra lights, aisle draft;  better = doors, night cover;  "
         "same = winter / humid store (the case itself did not change).", fontsize=7.5, color=INK2)
plt.tight_layout(rect=(0, 0.11, 1, 1))
fig.savefig(os.path.join(FIG, "T06_scorecard.png"), dpi=170)
plt.close(fig)

# ------------------------------------------------------------------ Figure 2: air-curtain fan sweep
fm = np.linspace(0.5, 1.8, 53)
res = [TM.run("x", fan_mult=f) for f in fm]
E = np.array([r["E"] for r in res])
cop_sys = np.array([r["Q_tot"] * 24 / r["E"] for r in res])
cop_m = np.array([r["COP"] for r in res])
etaS = np.array([r["S"] / r["E"] for r in res])
phi = np.array([1 - r["Q_inf"] / r["Q_tot"] for r in res])
i0 = np.argmin(abs(fm - 1.0))
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
a1.plot(fm, E, color=S1, lw=2)
a1.axvline(1.0, color=GRID, lw=1, zorder=0)
a1.set_xlabel("Air-curtain fan flow (× baseline)"); a1.set_ylabel("Electricity (kWh per day)")
a1.set_title("(a) Energy: U-shaped, minimum at the curtain optimum", loc="left", fontsize=9.5)
a1.grid(axis="y", color=GRID, lw=0.6)
a1.annotate("curtain too weak:\nwarm air breaks through", xy=(0.55, E[2]), xytext=(0.62, E.max() * 0.93),
            fontsize=8, color=INK2, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6))
a1.annotate("curtain too strong: entrains\nmore aisle air + fan power ∝ flow³", xy=(1.75, E[-2]),
            xytext=(1.02, E.max() * 0.80), fontsize=8, color=INK2,
            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6))
for y, c, lab in [(cop_m / cop_m[i0], S2, "(2a) machine COP"), (cop_sys / cop_sys[i0], S4, "(2b) heat removed per kWh"),
                  (phi / phi[i0], S3, "(6) capture fraction φ"), (etaS / etaS[i0], S1, "(5) kg·h per kWh")]:
    a2.plot(fm, y, color=c, lw=2, label=lab)
a2.axhline(1, color=GRID, lw=1, zorder=0); a2.axvline(1.0, color=GRID, lw=1, zorder=0)
a2.set_xlabel("Air-curtain fan flow (× baseline)"); a2.set_ylabel("Score (baseline = 1)")
a2.set_title("(b) Only the service measure peaks where energy is lowest", loc="left", fontsize=9.5)
a2.legend(frameon=False, fontsize=8, loc="lower center")
a2.grid(axis="y", color=GRID, lw=0.6)
fig.text(0.01, 0.01, "Infiltration-vs-flow curve is an ILLUSTRATIVE U-shape (assumed); literature confirms an optimum exists, "
         "not its exact position. Model: T06_metrics.py", fontsize=7.2, color=INK2)
plt.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(os.path.join(FIG, "T06_curtain_fan_sweep.png"), dpi=170)
plt.close(fig)

# ------------------------------------------------------------------ Figure 3: bus shelter carry-over
rows = TB.table()
fig, ax = plt.subplots(figsize=(9, 3.8))
devs = list(TB.POWER)
clim = list(TB.CLIMATES)
h = 0.36
for k, (cl, col) in enumerate(zip(clim, [S2, S1])):
    vals = [next(r["eta"] for r in rows if r["climate"] == cl and r["device"] == d) for d in devs]
    rel = [next(r["relief"] for r in rows if r["climate"] == cl and r["device"] == d) for d in devs]
    y = np.arange(len(devs)) + (k - 0.5) * h
    ax.barh(y, vals, height=h * 0.92, color=col, label=cl)
    for yy, v, rr in zip(y, vals, rel):
        ax.text(v * 1.08, yy, f"{v:.2f}  (felt relief {rr:.1f} °C)", va="center", fontsize=7.8, color=INK)
ax.set_xscale("log"); ax.set_xlim(0.1, 80)
from matplotlib.ticker import FuncFormatter
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}"))
ax.set_yticks(np.arange(len(devs))); ax.set_yticklabels(devs)
ax.invert_yaxis()
ax.set_xlabel("Person·°C·h of felt-temperature relief per kWh, per person served (log scale)")
ax.set_title("Same measure, new target: bus-shelter devices scored per person reached", loc="left", fontsize=10)
ax.legend(frameon=False, fontsize=8, loc="lower right")
ax.grid(axis="x", color=GRID, lw=0.6, which="both")
fig.text(0.01, 0.01, "Multiply by the number of people inside each device's reach. Capture fractions 0.26/0.44 and fan speed "
         "from the team's fit to COMAP's table; cooler assumed not to cool shelter surfaces.", fontsize=7, color=INK2)
plt.tight_layout(rect=(0, 0.05, 1, 1))
fig.savefig(os.path.join(FIG, "T06_bus_carryover.png"), dpi=170)
plt.close(fig)
print("figures written to", os.path.abspath(FIG))
