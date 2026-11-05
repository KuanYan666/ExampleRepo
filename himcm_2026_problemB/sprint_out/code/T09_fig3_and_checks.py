"""T09 step 6: Fig 3 (occupancy multiplies service but barely moves the ranking;
it DOES decide the control strategy) + TOPSIS structural checks."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
import T09_common as T
import T09_topsis as TP

res = pd.read_csv(T.D / "T09_service_results.csv", dtype={"stop": str})
occ = T.occupancy_table()
COL = {"fan": "#2a78d6", "evap": "#eb6834", "evap_big": "#1baf7a"}
NAME = {"fan": "A fan (0.25 kW)", "evap": "B evap (1.2 kW)", "evap_big": "C large evap (2.5 kW)"}
INK2, GRID = "#52514e", "#e4e3df"
stops = ["102445", "102949", "551928", "303317"]
short = {"102445": "Bx41\n170/day", "102949": "Bx15\n406/day", "551928": "Q67\n316/day",
         "303317": "B41\n2213/day"}

fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.4), gridspec_kw=dict(width_ratios=[1, 1, 1.05]))
# (a) total people-weighted service, Phoenix vs Houston
for ax, city in zip(axes[:2], ["Phoenix", "Houston"]):
    sub = res[(res.city == city) & (res.policy == "smart_occ")]
    for i, d in enumerate(["fan", "evap", "evap_big"]):
        v = [sub[(sub.stop == s) & (sub.device == d)].S_pdh.iloc[0] / 1000 for s in stops]
        ax.bar(np.arange(4) + (i - 1) * .27, v, .25, color=COL[d], label=NAME[d])
    for j, s in enumerate(stops):
        e = {d: sub[(sub.stop == s) & (sub.device == d)].eta.iloc[0] for d in COL}
        ax.text(j, ax.get_ylim()[1] * 0 + max(sub[sub.stop == s].S_pdh) / 1000 * 1.04,
                f"η: {e['fan']:.1f} / {e['evap']:.1f} / {e['evap_big']:.1f}", ha="center",
                fontsize=7.2, color=INK2)
    ax.set_xticks(range(4)); ax.set_xticklabels([short[s] for s in stops], fontsize=8.5)
    ax.set_title(f"{city}: felt cooling delivered per season", loc="left", fontsize=10)
    ax.grid(axis="y", color=GRID, lw=.6)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
axes[0].set_ylabel("Thousand person·°C·h  (Σ N·ΔSET·Δt)")
axes[0].legend(frameon=False, fontsize=8, loc="upper left")
axes[0].set_ylim(0, 7.2); axes[1].set_ylim(0, 4.4)
# (b) presence sensor saving vs occupancy
L = np.linspace(0.01, 6, 200)
ax = axes[2]
ax.plot(L, 100 * np.exp(-L), color=INK2, lw=1.5, ls="--", label="theory, constant L: saving = e^(−L)")
for city, mk in [("Phoenix", "o"), ("Houston", "s")]:
    p = res[(res.city == city) & (res.device == "evap_big")].pivot_table(index="stop", columns="policy", values="kWh")
    for s in stops:
        Lm = occ[(occ.stop_id == s) & occ.hour.between(9, 20)].L.mean()
        sav = 100 * (1 - p.loc[s, "smart_occ"] / p.loc[s, "smart"])
        ax.plot(Lm, sav, mk, ms=8, color="#6250d6" if city == "Phoenix" else "#eda100",
                mec="white", mew=1.5, label=city if s == stops[0] else None)
        if city == "Phoenix":
            ax.annotate(short[s].split("\n")[0], (Lm, sav), (6, 4), textcoords="offset points", fontsize=8)
ax.set_xlabel("Mean number waiting 9:00–21:00, L (persons)")
ax.set_ylabel("Energy saved by a presence sensor (%)")
ax.set_title("Occupancy decides the control, not the device", loc="left", fontsize=10)
ax.set_ylim(0, 100); ax.set_xlim(0, 6.2); ax.grid(color=GRID, lw=.6)
ax.legend(frameon=False, fontsize=8)
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
fig.tight_layout(); fig.savefig(T.S / "figs" / "T09_fig3_people_weighted_service.png", dpi=170)

# ---------------- structural checks on TOPSIS
print("Correlation of the two benefit criteria across 5 cities x 3 devices (Bx15 stop):")
sub = res[(res.stop == "102949") & (res.policy == "smart_occ")]
print("  corr(felt cooling, heat-safety) =", round(np.corrcoef(sub.S_pdh, sub.risk)[0, 1], 2))
print("  corr(energy, cost)              =",
      round(np.corrcoef(sub.kWh, [TP.matrix(c, "102949")[["fan", "evap", "evap_big"].index(d), 4]
                                  for c, d in zip(sub.city, sub.device)])[0, 1], 2))
for city in ["Phoenix", "Houston", "Singapore"]:
    X = TP.matrix(city, "102949")
    keep = [0, 2, 3, 4]
    w = TP.W_AHP[keep] / TP.W_AHP[keep].sum()
    c = TP.topsis(X[:, keep], w, TP.BENEFIT[keep])
    print(f"  {city}: TOPSIS WITHOUT heat-safety (AHP weights renormalised): " +
          " ".join(f"{v:.2f}" for v in c) + f" -> {TP.NAME[TP.DEVS[c.argmax()]]}")
    # weight on heat-safety at which the winner switches (others scaled proportionally)
    for ws in np.linspace(0, .9, 91):
        w = TP.W_AHP.copy(); rest = np.delete(np.arange(5), 1)
        w[rest] = TP.W_AHP[rest] / TP.W_AHP[rest].sum() * (1 - ws); w[1] = ws
        if TP.DEVS[TP.topsis(X, w).argmax()] != "fan":
            print(f"     heat-safety weight needed for the fan to lose first place: {ws:.2f}")
            break
    # occupancy scale invariance check
    X5 = TP.matrix(city, "303317")
    print(f"     closeness at Bx15 vs B41 (5.4x riders): {TP.topsis(X, TP.W_AHP).round(3)} vs "
          f"{TP.topsis(X5, TP.W_AHP).round(3)}")
