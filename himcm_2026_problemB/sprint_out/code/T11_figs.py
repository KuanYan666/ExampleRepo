"""T11 figures, read from T11_out/*.csv (run T11_run.py and T11_seasonal.py first)."""
import pathlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent
OUT = HERE / "T11_out"
FIG = HERE.parent / "figs"
FIG.mkdir(exist_ok=True)

BLUE, ORANGE, AQUA, YELLOW, MAGENTA, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
                     "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2,
                     "figure.facecolor": "white", "axes.facecolor": "white", "legend.frameon": False})


def save(fig, name):
    fig.savefig(FIG / name, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("saved", FIG / name)


# ------------------------------------------------------------- F1 heat budget
bud = pd.read_csv(OUT / "budget.csv")
fig, axs = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
for ax, city in zip(axs, ("Phoenix", "Houston")):
    b = bud[bud.city == city]
    ax.plot(b.N, b.people_lat, color=BLUE, marker="o", ms=4, label="Crowd: moisture (latent) heat")
    ax.plot(b.N, b.people_sens, color=ORANGE, marker="o", ms=4, label="Crowd: sensible heat (two-node body model)")
    ax.plot(b.N, b.ashrae_sens, color=ORANGE, ls="--", lw=1.5, label="Crowd sensible if 75 W/person (ASHRAE, 24 °C room)")
    ax.plot(b.N, b.roof, color=AQUA, marker="s", ms=4, label="Sun through the roof")
    ax.plot(b.N, b.cool_cap, color=VIOLET, lw=2, label="Large cooler: sensible cooling delivered")
    ax.axhline(2.5, color=INK2, ls=":", lw=1.5, label="Large cooler: electricity drawn (2.5 kW)")
    ax.axhline(0, color=INK2, lw=0.8)
    T0 = b.Tz.iloc[0]
    ax.set_title(f"{city}: median summer afternoon, outdoor {b.Tz_none.iloc[0]-0:.0f} °C zone (no device)",
                 fontsize=10, color=INK, loc="left")
    ax.set_title(f"{city} (typical summer afternoon)", fontsize=11, color=INK, loc="left")
    ax.set_xlabel("People waiting, N")
axs[0].set_ylabel("Heat flow into (+) or out of (−) the waiting area, kW")
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.13), fontsize=9)
fig.suptitle("Who heats the waiting area? In hot air the crowd adds MOISTURE, not temperature",
             x=0.01, ha="left", fontsize=12, color=INK)
save(fig, "T11_heat_budget.png")

# ------------------------------------------------------------- F2 limiting cases
lim = pd.read_csv(OUT / "limits.csv")
fig, ax = plt.subplots(figsize=(7.5, 4.4))
a = lim[lim.dev == "big_nm"]
ax.semilogx(a.A_open, a.Tz, color=BLUE, label="No people, no sun, adiabatic roof, motor heat off")
a = lim[lim.dev == "evap_big"]
ax.semilogx(a.A_open, a.Tz, color=BLUE, ls="--", lw=1.5, label="Same, motor heat on (+0.8 °C at the sealed end)")
a = lim[lim.dev == "evap_big_N200_sun"]
ax.semilogx(a.A_open, a.Tz, color=ORANGE, label="200 people + sun on the roof (realistic)")
ax.axhline(40.9, color=INK2, ls=":", lw=1.2)
ax.text(1.2e-3, 41.3, "Outdoor air 40.9 °C", color=INK2, fontsize=9)
ax.axhline(23.27, color=INK2, ls=":", lw=1.2)
ax.text(1.2e-3, 21.6, "Cooler supply air 23.3 °C", color=INK2, fontsize=9)
ax.axvline(40, color=INK2, lw=0.8)
ax.text(46, 30.5, "our station\n(40 m² opening)", color=INK2, fontsize=9)
ax.set_xlabel("Area of openings, m² (log scale)")
ax.set_ylabel("Waiting-area air temperature, °C")
ax.set_ylim(20, 44)
ax.legend(loc="center left", bbox_to_anchor=(0.0, 0.66), fontsize=8.5)
ax.set_title("Limiting cases: sealed → supply air; wide open → outdoor air (Phoenix, large cooler)",
             loc="left", fontsize=10.5, color=INK)
save(fig, "T11_limits.png")

# ------------------------------------------------------------- F3 efficiency vs crowd
eff = pd.read_csv(OUT / "efficiency.csv")
series = [("fan", "O", BLUE, "-", "Fan (0.25 kW)"),
          ("evap", "O", ORANGE, "-", "Cooler B, outdoor intake (1.2 kW)"),
          ("evap_big", "O", AQUA, "-", "Cooler C, outdoor intake (2.5 kW)"),
          ("evap_big", "R", YELLOW, "-", "Cooler C, recirculating zone air")]
fig, axs = plt.subplots(2, 2, figsize=(11, 8), sharex=True)
for j, city in enumerate(("Phoenix", "Houston")):
    for dev, mode, col, ls, lab in series:
        e = eff[(eff.city == city) & (eff.dev == dev) & (eff["mode"] == mode)]
        axs[0, j].plot(e.N, e.dSET, color=col, ls=ls, marker="o", ms=3.5, label=lab)
        axs[1, j].plot(e.N, e.eta_deg, color=col, ls=ls, marker="o", ms=3.5, label=lab)
    e = eff[(eff.city == city) & (eff.dev == "evap_big") & (eff["mode"] == "O")]
    axs[1, j].plot(e.N, e.eta_deg_old, color=AQUA, ls="--", lw=1.5,
                   label="Cooler C, OLD bus-stop logic (crowd changes nothing)")
    axs[0, j].plot(e.N, e.dSET.iloc[0] * np.ones(len(e)), color=AQUA, ls="--", lw=1.5,
                   label="Cooler C, OLD bus-stop logic (crowd changes nothing)")
    for ax in axs[:, j]:
        ax.axvspan(400, 600, color=GRID, alpha=0.6, lw=0)
        ax.axhline(0, color=INK2, lw=0.8)
    axs[0, j].text(410, 1.12 if j == 0 else 2.0, "packed:\n< 0.3 m² each", fontsize=8.5, color=INK2, va="top")
    axs[0, j].set_title(f"{city}: felt cooling per person", loc="left", fontsize=11, color=INK)
    axs[1, j].set_title(f"{city}: efficiency = people × felt cooling ÷ power", loc="left", fontsize=11, color=INK)
    axs[1, j].set_xlabel("People waiting, N (120 m² area)")
axs[0, 0].set_ylabel("Felt cooling ΔSET per person, °C")
axs[1, 0].set_ylabel("Efficiency, person·°C·h per kWh")
axs[0, 1].set_ylim(-0.8, 2.2)
axs[0, 0].set_ylim(-0.8, 3.2)
# mark felt-overwhelm point Houston cooler C
axs[0, 1].annotate("recirculating cooler: people\nfeel HOTTER than with no device", xy=(75, -0.52), xytext=(130, -0.72), fontsize=8.5,
                   color=INK2, arrowprops=dict(arrowstyle="->", color=INK2, lw=0.8))
h, l = axs[1, 0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.06), fontsize=9)
fig.suptitle("Crowd size changes the answer: efficiency keeps rising per kWh, but the benefit per person can collapse",
             x=0.01, ha="left", fontsize=12, color=INK)
fig.tight_layout(rect=(0, 0.02, 1, 0.97))
save(fig, "T11_efficiency_vs_crowd.png")

# ------------------------------------------------------------- F4 surge
tr = pd.read_csv(OUT / "surge_trace.csv")
H = 8 * 60
tr = tr[tr.t >= tr.t.max() - 3 * H].copy()
tr["tm"] = (tr.t - tr.t.min()) / 60
fig, axs = plt.subplots(2, 1, figsize=(8.5, 5.6), sharex=True, gridspec_kw=dict(height_ratios=[1, 1.3]))
axs[0].plot(tr.tm, tr.N, color=INK2, lw=1.5)
axs[0].set_ylabel("People waiting")
axs[0].set_title("Houston, cooler C, 200 people on average, a train every 8 min", loc="left", fontsize=11, color=INK)
axs[0].text(0.3, 360, "crowd builds up …", fontsize=9, color=INK2)
axs[0].text(7.8, 120, "train leaves →", fontsize=9, color=INK2, ha="right")
axs[1].plot(tr.tm, tr.T_qs, color=ORANGE, ls="--", lw=1.6, label="Instant (steady-state) answer for the crowd at that moment")
axs[1].plot(tr.tm, tr["T"], color=BLUE, label="Time-dependent ODE (air takes ~1.5 min to respond)")
axs[1].set_ylabel("Waiting-area air temperature, °C")
axs[1].set_xlabel("Time, minutes")
axs[1].legend(loc="upper left", fontsize=8.5)
axs[1].set_ylim(30.4, 31.7)
save(fig, "T11_surge.png")

# ------------------------------------------------------------- F5 tornado
sens = pd.read_csv(OUT / "sensitivity.csv")
fig, axs = plt.subplots(1, 2, figsize=(11, 4.6))
for ax, city in zip(axs, ("Phoenix", "Houston")):
    s = sens[sens.city == city].copy()
    s["span"] = (s.y_hi - s.y_lo).abs()
    s = s.sort_values("span")
    y0 = s.y0.iloc[0]
    yy = np.arange(len(s))
    for i, r in enumerate(s.itertuples()):
        ax.barh(i, r.y_lo - y0, left=y0, color=BLUE, height=0.6)
        ax.barh(i, r.y_hi - y0, left=y0, color=ORANGE, height=0.6)
    ax.set_yticks(yy)
    ax.set_yticklabels([f"{p}  [{lo:g} | {hi:g}]" for p, lo, hi in zip(s.param, s.lo, s.hi)], fontsize=8.5)
    ax.axvline(y0, color=INK, lw=1)
    ax.set_xlabel("Felt cooling per person at N = 200, ΔSET °C")
    ax.set_title(f"{city} (base {y0:.2f} °C)", loc="left", fontsize=11, color=INK)
    ax.grid(axis="y", visible=False)
from matplotlib.patches import Patch
fig.legend([Patch(color=BLUE), Patch(color=ORANGE)], ["low value of the input", "high value of the input"],
           loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.06))
fig.suptitle("What the station result depends on (cooler C, outdoor intake, one input changed at a time)",
             x=0.01, ha="left", fontsize=12, color=INK)
fig.tight_layout(rect=(0, 0.02, 1, 0.95))
save(fig, "T11_tornado.png")

# ------------------------------------------------------------- F6 seasonal overwhelm
sea = pd.read_csv(OUT / "seasonal.csv")
fig, ax = plt.subplots(figsize=(7.5, 4.2))
for city, col in (("Houston", BLUE), ("Phoenix", ORANGE)):
    x = np.sort(sea[sea.city == city].N_ow.clip(upper=3000).values)
    ax.step(x, np.arange(1, len(x) + 1) / len(x), color=col, where="post", label=city)
ax.axvline(400, color=INK2, ls=":", lw=1.2)
ax.text(420, 0.38, "packed area\n(0.3 m² each)", fontsize=8.5, color=INK2)
ax.set_xlabel("Crowd that overwhelms cooler C, people (capped at 3000)")
ax.set_ylabel("Share of summer afternoon hours")
ax.set_title("Over a whole summer: how many people does it take to cancel cooler C?", loc="left",
             fontsize=10.5, color=INK)
ax.text(1750, 0.62, "Phoenix", color=ORANGE, fontsize=10)
ax.text(620, 0.55, "Houston", color=BLUE, fontsize=10)
save(fig, "T11_overwhelm_season.png")
