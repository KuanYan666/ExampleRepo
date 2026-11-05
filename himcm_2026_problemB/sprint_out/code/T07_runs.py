"""T07 - scenario runs, tables and figures for the nested store model.
Run: python3 T07_runs.py   (imports T07_store_model.py from the same folder)
Outputs: printed tables, data_T07/T07_*.csv, ../figs/T07_*.png
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import T07_store_model as M

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "figs")
os.makedirs(FIG, exist_ok=True)
CITIES = {"houston": "Houston (hot-humid)", "minneapolis": "Minneapolis (cold)"}
PRICE_E, PRICE_G = 0.13, 0.04    # $/kWh electricity, $/kWh gas  [ASSUMED: rough US commercial]
MON = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]

wx = {c: M.load_weather(c) for c in CITIES}


def elec(o):
    return o.E_LT + o.E_MT + o.E_AC + o.E_light


def summary(o):
    e, g = elec(o).sum(), o.gas.sum()
    return dict(E_LT=o.E_LT.sum() / 1e3, E_AC=o.E_AC.sum() / 1e3, gas=g / 1e3,
                elec=e / 1e3, site=(e + g) / 1e3, cost=(e * PRICE_E + g * PRICE_G) / 1e3,
                RH=o.RH_i.mean())


rows = []
monthly = {}
for c in CITIES:
    print("=" * 90); print(CITIES[c]); print("=" * 90)
    w = wx[c]
    print(f"weather 2023: T mean {w.T_o.mean():.1f} C, min {w.T_o.min():.1f}, max {w.T_o.max():.1f}; "
          f"mean outdoor W {w.W_o.mean()*1000:.1f} g/kg")
    for cfg in ["remote", "plugin", "reclaim"]:
        for label, kw in [("no door air", dict(N_peak=153, door_override=np.zeros(len(w)))),
                          ("baseline 153/h", dict(N_peak=153)),
                          ("vestibule 153/h", dict(N_peak=153, vestibule=True)),
                          ("busy 306/h", dict(N_peak=306, people_peak=306))]:
            for rh in [False, True]:
                o = M.simulate(w, config=cfg, rh_control=rh, **kw)
                s = summary(o); s.update(city=c, config=cfg, doors=label, rh_control=rh)
                rows.append(s)
                monthly[(c, cfg, label, rh)] = o.groupby(o.time.dt.month).agg(
                    E_LT=("E_LT", "sum"), E_AC=("E_AC", "sum"), gas=("gas", "sum"),
                    RH=("RH_i", "mean"), T_i=("T_i", "mean"), credit=("credit_LT", "sum"),
                    Q_LT_lat=("Q_LT_lat", "mean"), Q_LT_sens=("Q_LT_sens", "mean"))
    # freezers removed entirely: to isolate the freezers' effect on HVAC
    for cfg in ["remote"]:
        o = M.simulate(w, config=cfg, n_LT=0)
        monthly[(c, "none", "baseline 153/h", False)] = o.groupby(o.time.dt.month).agg(
            E_LT=("E_LT", "sum"), E_AC=("E_AC", "sum"), gas=("gas", "sum"),
            RH=("RH_i", "mean"), T_i=("T_i", "mean"), credit=("credit_LT", "sum"),
            Q_LT_lat=("Q_LT_lat", "mean"), Q_LT_sens=("Q_LT_sens", "mean"))
        s = summary(o); s.update(city=c, config="no freezers", doors="baseline 153/h", rh_control=False)
        rows.append(s)

R = pd.DataFrame(rows)
R.to_csv(os.path.join(M.DATA, "T07_annual_scenarios.csv"), index=False)
pd.set_option("display.width", 200)
print(R[(~R.rh_control)].round(1).to_string(index=False))
print("\nwith 55 % RH cap:")
print(R[(R.rh_control)].round(1).to_string(index=False))

# ------------------------------------------------------------------ door effect table
print("\n" + "=" * 90); print("DOOR-TRAFFIC EFFECT ON ANNUAL FREEZER (LT) ELECTRICITY, 12 cases"); print("=" * 90)
for c in CITIES:
    for cfg in ["remote", "plugin"]:
        for rh in [False, True]:
            sub = R[(R.city == c) & (R.config == cfg) & (R.rh_control == rh)].set_index("doors")
            b0 = sub.loc["no door air"]
            line = f"{c:12s} {cfg:7s} RHcap={str(rh):5s} | LT no-door {b0.E_LT:6.1f} MWh"
            for d in ["vestibule 153/h", "baseline 153/h", "busy 306/h"]:
                line += f" | {d}: {100*(sub.loc[d].E_LT/b0.E_LT-1):+5.1f}% LT, {100*(sub.loc[d].site/b0.site-1):+5.1f}% site, ${sub.loc[d].cost-b0.cost:+5.1f}k"
            print(line)

# per-month door effect (remote, no RH control)
print("\nmonthly % change in freezer electricity, baseline doors vs no door air (remote rack):")
for c in CITIES:
    a = monthly[(c, "remote", "baseline 153/h", False)]; b = monthly[(c, "remote", "no door air", False)]
    print(f"{c:12s}", " ".join(f"{x:+5.1f}" for x in 100 * (a.E_LT / b.E_LT - 1)))
    print(f"{'  store RH':12s}", " ".join(f"{x:5.1f}" for x in a.RH))
    print(f"{'  RH no door':12s}", " ".join(f"{x:5.1f}" for x in b.RH))

# split of the door effect on the LT evaporator load: temperature vs moisture
print("\nsplit of the door effect on the LT evaporator load (annual, remote):")
for c in CITIES:
    a = M.simulate(wx[c], N_peak=153); b = M.simulate(wx[c], door_override=np.zeros(len(wx[c])))
    dS = (a.Q_LT_sens - b.Q_LT_sens).sum(); dL = (a.Q_LT_lat - b.Q_LT_lat).sum()
    print(f"{c:12s}: d(sensible) {dS/1e3:+.2f} MWh/case, d(latent) {dL/1e3:+.2f} MWh/case "
          f"-> moisture share {100*dL/(dS+dL):.0f} %  (abs-sum share {100*abs(dL)/(abs(dS)+abs(dL)):.0f} %)")
    # by season
    for name, months in [("Jun-Aug", [6, 7, 8]), ("Dec-Feb", [12, 1, 2])]:
        mk = a.time.dt.month.isin(months)
        dS = (a.Q_LT_sens - b.Q_LT_sens)[mk].sum(); dL = (a.Q_LT_lat - b.Q_LT_lat)[mk].sum()
        print(f"      {name}: d(sens) {dS:+8.0f} kWh, d(lat) {dL:+8.0f} kWh per case")

# marginal energy per door opening
print("\nmarginal energy per door opening (finite difference 153 -> 168 openings/h peak):")
for c in CITIES:
    a = M.simulate(wx[c], N_peak=153); b = M.simulate(wx[c], N_peak=168.3)
    dn = (b.N - a.N).sum()
    for nm, col in [("freezers", "E_LT"), ("AC", "E_AC"), ("gas heat", "gas"), ("whole store", "E_total_site")]:
        print(f"  {c:12s} {nm:12s}: {1000*(b[col].sum()-a[col].sum())/dn:+7.2f} Wh per opening")
    print(f"  {c:12s} openings per year at baseline: {a.N.sum():,.0f}")

# ------------------------------------------------------------------ case-credit sign analysis
print("\n" + "=" * 90); print("WHAT THE FREEZERS DO TO STORE HVAC (12 LT cases present minus absent)"); print("=" * 90)
sign = {}
for c in CITIES:
    none = monthly[(c, "none", "baseline 153/h", False)]
    for cfg in ["remote", "plugin", "reclaim"]:
        m = monthly[(c, cfg, "baseline 153/h", False)]
        dAC = m.E_AC - none.E_AC; dG = m.gas - none.gas
        sign[(c, cfg)] = (dAC, dG, m.E_LT)
        dcost = dAC * PRICE_E + dG * PRICE_G
        print(f"{c:12s} {cfg:8s}: annual dAC {dAC.sum()/1e3:+6.1f} MWh_e, dHeat {dG.sum()/1e3:+6.1f} MWh_gas, "
              f"LT {m.E_LT.sum()/1e3:5.1f} MWh_e -> HVAC/LT cost ratio {dcost.sum()/(m.E_LT.sum()*PRICE_E):+.2f}")
        print("     monthly dHVAC cost $:", " ".join(f"{x:+5.0f}" for x in dcost))

# ------------------------------------------------------------------ sweep of door openings
sweep_N = np.array([0, 25, 50, 100, 153, 200, 250, 300, 400])
sweep = []
for c in CITIES:
    for rh in [False, True]:
        for N in sweep_N:
            o = M.simulate(wx[c], N_peak=N if N > 0 else 153,
                           door_override=None if N > 0 else np.zeros(len(wx[c])), rh_control=rh,
                           people_peak=153)
            nn, _ = M.door_schedule(o.time.dt.hour.values, N)
            s = summary(o); s.update(city=c, N_peak=N, rh_control=rh, mean_open=nn.mean())
            sweep.append(s)
SW = pd.DataFrame(sweep)
SW.to_csv(os.path.join(M.DATA, "T07_door_sweep.csv"), index=False)
print("\nsweep (remote):"); print(SW.round(2).to_string(index=False))

# ------------------------------------------------------------------ FIGURE 1: monthly
fig, ax = plt.subplots(2, 2, figsize=(12, 8.2), sharex=True)
x = np.arange(1, 13)
for j, c in enumerate(CITIES):
    a = ax[0, j]
    for lab, col, ls in [("no door air", "#4C72B0", "--"), ("baseline 153/h", "#222222", "-"),
                         ("busy 306/h", "#C44E52", "-")]:
        m = monthly[(c, "remote", lab, False)]
        a.plot(x, m.E_LT / 1e3, ls, color=col, marker="o", ms=4,
               label={"no door air": "doors sealed (no outdoor air via door)",
                      "baseline 153/h": "baseline traffic (peak 153 openings/h)",
                      "busy 306/h": "double traffic (peak 306/h)"}[lab])
    a2 = a.twinx()
    a2.bar(x, monthly[(c, "remote", "baseline 153/h", False)].RH, color="#55A868", alpha=0.18, width=0.7)
    a2.set_ylim(0, 100); a2.set_ylabel("store RH, baseline (%)  [green bars]", color="#2d6b3c", fontsize=9)
    a.set_zorder(a2.get_zorder() + 1); a.patch.set_visible(False)
    a.set_title(f"{CITIES[c]}: freezer electricity per month", fontsize=11)
    a.set_ylabel("freezer lineup electricity (MWh/month)")
    a.set_ylim(8, 20)
    a.grid(alpha=0.3)
    if j == 0:
        a.legend(fontsize=8, loc="upper left")
    b = ax[1, j]
    w = 0.27
    for k, (cfg, col, nm) in enumerate([("remote", "#4C72B0", "remote rooftop condenser"),
                                       ("reclaim", "#8172B2", "remote + heat reclaim"),
                                       ("plugin", "#DD8452", "plug-in (condenser in store)")]):
        dAC, dG, _ = sign[(c, cfg)]
        b.bar(x + (k - 1) * w, (dAC * PRICE_E + dG * PRICE_G) / 1e3, width=w, color=col, label=nm)
    b.axhline(0, color="k", lw=0.8)
    b.set_title(f"{CITIES[c]}: freezers' effect on store HVAC bill", fontsize=11)
    b.set_ylabel("extra HVAC cost caused by freezers\n(k$/month; <0 = freezers save HVAC)")
    b.set_xticks(x); b.set_xticklabels(MON)
    b.set_xlabel("month of 2023")
    b.grid(alpha=0.3, axis="y")
    if j == 1:
        h, l = b.get_legend_handles_labels()
        fig.legend(h, l, fontsize=9, loc="lower center", ncol=3, frameon=False)
fig.suptitle("Nested store model: outdoor weather -> store air -> freezer cases (12 open vertical freezers, hourly 2023 weather)",
             fontsize=11)
fig.tight_layout(rect=(0, 0.035, 1, 0.96))
fig.savefig(os.path.join(FIG, "T07_monthly_freezer_hvac.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ------------------------------------------------------------------ FIGURE 2: door sweep
fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
for c, col in zip(CITIES, ["#C44E52", "#4C72B0"]):
    for rh, ls in [(False, "-"), (True, "--")]:
        s = SW[(SW.city == c) & (SW.rh_control == rh)].sort_values("N_peak")
        base = s[s.N_peak == 0].iloc[0]
        lab = f"{CITIES[c]}" + (", store RH held <= 55 %" if rh else ", no humidity control")
        ax[0].plot(s.N_peak, 100 * (s.E_LT / base.E_LT - 1), ls, color=col, marker="o", ms=4, label=lab)
        ax[1].plot(s.N_peak, 100 * (s.site / base.site - 1), ls, color=col, marker="o", ms=4, label=lab)
ax[0].set_title("Freezer electricity vs front-door air\n(shopper numbers held at baseline)", fontsize=11)
ax[0].set_ylabel("change in annual freezer electricity (%)\nvs doors sealed")
ax[1].set_title("Whole-store energy (electricity + gas) vs front-door air\n(shopper numbers held at baseline)", fontsize=11)
ax[1].set_ylabel("change in annual site energy (%)\nvs doors sealed")
for a in ax:
    a.axvline(153, color="grey", lw=0.8, ls=":")
    a.text(156, a.get_ylim()[0] + 0.05 * (a.get_ylim()[1] - a.get_ylim()[0]), "PNNL retail\npeak 153/h",
           fontsize=8, color="grey")
    a.axhline(0, color="k", lw=0.6)
    a.set_xlabel("peak-hour door openings per hour (busiest hour of the day)")
    a.grid(alpha=0.3)
ax[0].legend(fontsize=8, loc="upper left")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "T07_freezer_vs_door_openings.png"), dpi=150)
plt.close(fig)

# ------------------------------------------------------------------ FIGURE 3: hourly store RH vs outdoor
fig, ax = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
for a, c in zip(ax, CITIES):
    o = M.simulate(wx[c], N_peak=153)
    ok = o.N > 20
    sc = a.scatter(o.W_o[ok] * 1000, o.Q_LT_case[ok], c=o.time.dt.month[ok], cmap="twilight", s=3, alpha=0.6)
    a.set_title(f"{CITIES[c]}: open hours", fontsize=11)
    a.set_xlabel("outdoor humidity ratio (g water / kg dry air)")
    a.grid(alpha=0.3)
ax[0].set_ylabel("load on ONE freezer case (kW)")
cb = fig.colorbar(sc, ax=ax, fraction=0.03); cb.set_label("month")
fig.savefig(os.path.join(FIG, "T07_case_load_vs_outdoor_humidity.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("figures written")
