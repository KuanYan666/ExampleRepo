"""T05 - local elasticities, tornado, Sobol (SALib) and robustness of the ranking."""
import sys, os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from SALib.sample import sobol as sobol_sample
from SALib.analyze import sobol as sobol_analyze

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import T05_model as M

FIG = os.path.join(HERE, "..", "figs")
OUT = {}
P = M.PARAMS
names = list(P)
base = M.BASE
TEMP_DRIVER = {  # temperatures on an interval scale: use the driving temperature DIFFERENCE
    "T_store": base["T_store"] - base["T_DA"],
    "T_DA": base["T_store"] - base["T_DA"],
    "T_cond": base["T_cond"] - (base["T_DA"] - base["dT_coil"]),
}
OUTPUTS = {"y_day": "Electricity per day (case boundary)",
           "y_kg": "Electricity per kg product per day",
           "E_store": "Electricity per day incl. store HVAC"}


def run(pdict, key, **kw):
    return M.case_model(pdict, **kw)[key]


# ------------------------------------------------------------------ 1. local elasticities
def elasticities(key, h=0.01, **kw):
    y0 = run(base, key, **kw)
    res = {}
    for k in names:
        p0 = base[k]
        step = h * (abs(p0) if p0 != 0 else (P[k][2] - P[k][1]))
        up, dn = dict(base), dict(base)
        up[k], dn[k] = p0 + step, p0 - step
        dydp = (run(up, key, **kw) - run(dn, key, **kw)) / (2 * step)
        if k in TEMP_DRIVER:
            E = dydp * TEMP_DRIVER[k] / y0
        elif p0 == 0:
            E = np.nan               # elasticity undefined at p=0 (kappa)
        else:
            E = dydp * p0 / y0
        res[k] = dict(E=float(E), pct_per_unit=float(100 * dydp / y0))
    return y0, res


print("=" * 78)
for key in OUTPUTS:
    y0, el = elasticities(key)
    OUT[f"elast_{key}"] = el
    print(f"{OUTPUTS[key]}  baseline = {y0:.4g}")
    for k, d in sorted(el.items(), key=lambda kv: -abs(np.nan_to_num(kv[1]['E']))):
        print(f"   {k:<10} E = {d['E']:+.3f}   ({d['pct_per_unit']:+.3f} % per {P[k][4]})")
# Hand check of one elasticity: E(r_inf) should equal the infiltration share of E_th times E_comp/E_case
r = M.case_model(base)
share_inf = (r["parts_th"]["Infiltration - sensible"] + r["parts_th"]["Infiltration - latent (frost)"]) / r["E_th"]
print(f"hand check E(r_inf) ~ share_inf*E_comp/E_case = {share_inf*r['E_comp']/r['E_case']:.3f} (+ small defrost coupling)")

# ------------------------------------------------------------------ 2. tornado (one at a time, full range)
y0 = run(base, "y_day")
torn = []
for k in names:
    lo, hi = dict(base), dict(base)
    lo[k], hi[k] = P[k][1], P[k][2]
    torn.append((k, run(lo, "y_day") - y0, run(hi, "y_day") - y0))
torn.sort(key=lambda t: abs(t[2] - t[1]))
OUT["tornado"] = torn
print("\nTornado swings (kWh/day) low->high:")
for k, a, b in torn[::-1]:
    print(f"   {k:<10} low {a:+6.2f}  high {b:+6.2f}  swing {abs(b-a):5.2f}")

LABEL = {
    "T_store": "Store air temperature (21-26 °C)", "RH_store": "Store humidity (35-60 % RH)",
    "r_inf": "Air-curtain infiltration (x0.7-1.5)", "T_DA": "Case air temperature (-25 to -18 °C)",
    "dT_coil": "Coil temperature gap (3-8 K)", "T_cond": "Condensing temperature (25-45 °C)",
    "eta_II": "Machine quality, 2nd-law eff. (0.35-0.55)", "UA": "Insulation UA (4-10 W/K)",
    "epsF": "Radiation factor (0.3-0.8)", "P_light": "Lamp power (39-181 W)",
    "h_light": "Lamp hours (12-24 h/day)", "f_light": "Lamp heat into case (50-100 %)",
    "P_fan": "Evaporator fan power (40-150 W)", "P_ambfan": "Curtain fan power (5-20 W)",
    "P_ash": "Anti-sweat heater power (250-450 W)", "duty_ash": "Anti-sweat duty (30-100 %)",
    "f_ash": "Anti-sweat heat into case (20-70 %)", "P_def": "Defrost heater power (1.4-3.4 kW)",
    "n_def": "Defrosts per day (1-4)", "t_def": "Defrost length (15-30 min)",
    "f_def": "Defrost heat re-removed (30-80 %)", "m_restock": "Restocking (30-300 kg/day)",
    "dT_arr": "Product arrives warmer by (2-15 K)", "kappa": "Store HVAC weight (-0.33 to +0.33)",
    "rho_load": "Product per m³ of shelf (150-400 kg)",
}

fig, ax = plt.subplots(figsize=(10, 8.5))
show = [t for t in torn if abs(t[2] - t[1]) > 1e-9]
for i, (k, a, b) in enumerate(show):
    ax.barh(i, a, color="#3b6fb6", height=0.7)
    ax.barh(i, b, color="#d0703c", height=0.7)
ax.set_yticks(range(len(show)))
ax.set_yticklabels([LABEL[t[0]] for t in show], fontsize=9)
ax.axvline(0, color="k", lw=0.8)
ax.set_xlabel(f"Change in electricity use (kWh/day) from baseline {y0:.1f} kWh/day")
ax.set_title("Tornado: one parameter at a time moved across its full plausible range\n"
             "2.5 m open vertical freezer case, case boundary (no store HVAC)", fontsize=11)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color="#3b6fb6", label="parameter at LOW end"),
                   Patch(color="#d0703c", label="parameter at HIGH end")], loc="lower right")
ax.grid(axis="x", alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "T05_tornado.png"), dpi=150)
plt.close(fig)

# ------------------------------------------------------------------ 3. Sobol
GROUP = {k: P[k][3] for k in names}


CLIP = {"duty_ash": (0.05, 1.0), "f_light": (0.05, 1.0), "f_ash": (0.0, 1.0), "f_def": (0.0, 1.0),
        "RH_store": (5, 95), "T_DA": (-35, -15), "P_light": (0.005, 1), "n_def": (0.5, 6), "t_def": (5, 30)}


def make_problem(scale=1.0, groups=False, sym20=False):
    bounds = []
    for k in names:
        b, lo, hi = P[k][0], P[k][1], P[k][2]
        if sym20:   # pure-structure test: every parameter +-20 % of baseline (temps: +-2 K)
            if k in ("T_store", "T_DA", "T_cond"):
                lo, hi = b - 2, b + 2
            elif b == 0:
                lo, hi = -0.066, 0.066          # +-20 % of the 0.33 range half-width
            else:
                lo, hi = 0.8 * b, 1.2 * b
        elif scale != 1.0:
            c = 0.5 * (lo + hi)
            lo, hi = c - scale * (c - lo), c + scale * (hi - c)
        if k in CLIP:
            lo, hi = max(lo, CLIP[k][0]), min(hi, CLIP[k][1])
        bounds.append([lo, hi])
    pr = {"num_vars": len(names), "names": names, "bounds": bounds}
    if groups:
        pr["groups"] = [GROUP[k] for k in names]
    return pr


def evaluate(X, key, **kw):
    return run({k: X[:, i] for i, k in enumerate(names)}, key, **kw)


def sobol(problem, key, N=2**14, seed=1, **kw):
    X = sobol_sample.sample(problem, N, calc_second_order=False, seed=seed)
    Y = evaluate(X, key, **kw)
    S = sobol_analyze.analyze(problem, Y, calc_second_order=False, seed=seed)
    return S, Y


results = {}
for key in OUTPUTS:
    Sp, Y = sobol(make_problem(), key)
    Sg, _ = sobol(make_problem(groups=True), key)
    gnames = list(dict.fromkeys(GROUP[k] for k in names))
    results[key] = dict(
        param={k: (float(Sp["S1"][i]), float(Sp["ST"][i]), float(Sp["ST_conf"][i])) for i, k in enumerate(names)},
        group={g: (float(Sg["S1"][i]), float(Sg["ST"][i]), float(Sg["ST_conf"][i])) for i, g in enumerate(gnames)},
        mean=float(Y.mean()), p5=float(np.percentile(Y, 5)), p95=float(np.percentile(Y, 95)),
        sumS1=float(np.sum(Sp["S1"])))
    print(f"\nSOBOL {OUTPUTS[key]}: mean {Y.mean():.4g}, 5-95% [{np.percentile(Y,5):.4g}, {np.percentile(Y,95):.4g}],"
          f" sum S1 = {np.sum(Sp['S1']):.3f}")
    for g, (s1, st, c) in sorted(results[key]["group"].items(), key=lambda kv: -kv[1][1]):
        print(f"   GROUP {g:<28} S1 {s1:6.3f}  ST {st:6.3f} +-{c:.3f}")
    for k, (s1, st, c) in sorted(results[key]["param"].items(), key=lambda kv: -kv[1][1])[:14]:
        print(f"   {k:<10} S1 {s1:6.3f}  ST {st:6.3f} +-{c:.3f}")
OUT["sobol"] = results

# ------------------------------------------------------------------ 4. robustness of the group ranking
robust = {}
cases = {"base ranges": dict(), "ranges halved": dict(scale=0.5), "ranges x1.5": dict(scale=1.5),
         "all +-20 % (structure only)": dict(sym20=True)}
for lab, kw in cases.items():
    pr = make_problem(groups=True, **kw)
    S, _ = sobol(pr, "y_day", N=2**13)
    gnames = list(dict.fromkeys(GROUP[k] for k in names))
    robust[lab] = {g: float(S["ST"][i]) for i, g in enumerate(gnames)}
S, _ = sobol(make_problem(groups=True), "y_day", N=2**13, frost_coupling=False)
robust["no frost->defrost coupling"] = {g: float(S["ST"][i]) for i, g in enumerate(gnames)}
OUT["robust"] = robust
print("\nRobustness of group total indices (y_day):")
print(" " * 30 + "".join(f"{l[:14]:>16}" for l in robust))
for g in gnames:
    print(f"   {g:<27}" + "".join(f"{robust[l][g]:16.3f}" for l in robust))

# ------------------------------------------------------------------ 5. figures
def sobol_fig():
    fig, axes = plt.subplots(1, 2, figsize=(14, 7.2))
    R = results["y_day"]
    items = sorted(R["param"].items(), key=lambda kv: kv[1][1])
    items = [it for it in items if it[1][1] > 0.002][-14:]
    yy = np.arange(len(items))
    ax = axes[0]
    ax.barh(yy + 0.2, [v[1] for _, v in items], 0.4, color="#d0703c", label="Total index S_T (alone + with others)",
            xerr=[v[2] for _, v in items], capsize=2)
    ax.barh(yy - 0.2, [v[0] for _, v in items], 0.4, color="#3b6fb6", label="First-order index S_1 (alone)")
    ax.set_yticks(yy)
    ax.set_yticklabels([LABEL[k] for k, _ in items], fontsize=8.5)
    ax.axvline(0.05, color="k", ls="--", lw=1)
    ax.text(0.052, 0.3, "inclusion\nthreshold 0.05", fontsize=8, va="bottom")
    ax.set_xlabel("Share of the variance of electricity/day")
    ax.set_title("(a) Individual parameters (top 14)", fontsize=11)
    ax.legend(loc="lower right", fontsize=8.5)
    ax.grid(axis="x", alpha=0.3)

    ax = axes[1]
    gitems = sorted([kv for kv in R["group"].items()
                     if kv[0] not in ("Store HVAC interaction", "Product stocked (service)")], key=lambda kv: kv[1][1])
    yy = np.arange(len(gitems))
    ax.barh(yy, [v[1] for _, v in gitems], 0.55, color="#d0703c", label="S_T, base ranges")
    marks = {"ranges halved": "o", "ranges x1.5": "s", "all +-20 % (structure only)": "^",
             "no frost->defrost coupling": "x"}
    for lab, mk in marks.items():
        ax.scatter([robust[lab][g] for g, _ in gitems], yy, marker=mk, color="k", s=28, zorder=3, label=lab,
                   facecolors="none" if mk in "os^" else "k")
    ax.set_yticks(yy)
    ax.set_yticklabels([g for g, _ in gitems], fontsize=9)
    ax.axvline(0.05, color="k", ls="--", lw=1)
    ax.set_xlabel("Total Sobol index of the whole aspect (group)")
    ax.set_title("(b) Aspects (grouped) + robustness checks", fontsize=11)
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(axis="x", alpha=0.3)
    fig.suptitle("Global sensitivity (Sobol, N = 16384 base samples) of a 2.5 m open freezer case's electricity use",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "T05_sobol.png"), dpi=150)
    plt.close(fig)


sobol_fig()

# elasticity bar chart
fig, ax = plt.subplots(figsize=(10, 8))
el = OUT["elast_y_day"]
elk = OUT["elast_y_kg"]
items = sorted([k for k in names if not np.isnan(el[k]["E"])],
               key=lambda k: max(abs(el[k]["E"]), abs(elk[k]["E"])))
yy = np.arange(len(items))
ax.barh(yy + 0.2, [el[k]["E"] for k in items], 0.4, color="#3b6fb6", label="(a) kWh per day")
ax.barh(yy - 0.2, [elk[k]["E"] for k in items], 0.4, color="#7aa974", label="(b) kWh per kg of product per day")
ax.set_yticks(yy)
ax.set_yticklabels([LABEL[k].split(" (")[0] + ("  [vs ΔT]" if k in TEMP_DRIVER else "") for k in items], fontsize=9)
ax.axvline(0, color="k", lw=0.8)
for x in (-0.1, 0.1):
    ax.axvline(x, color="grey", ls=":", lw=1)
ax.set_xlabel("Elasticity E = (dy/dp)(p/y): % change in y for a 1 % change in p")
ax.set_title("Local elasticities at the baseline (temperatures: per 1 % of the driving temperature difference)",
             fontsize=10.5)
ax.legend(loc="lower right")
ax.grid(axis="x", alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "T05_elasticity.png"), dpi=150)
plt.close(fig)

# load breakdown figure
r = M.case_model(base)
fig, axes = plt.subplots(1, 2, figsize=(13, 6))
ax = axes[0]
parts = r["parts_th"]
cols = ["#2a5c9a", "#6fa0d8", "#9b9b9b", "#e0b040", "#f2dd80", "#7aa974", "#d0703c", "#a0522d", "#bbbbbb"]
left = 0
for (k, v), c in zip(parts.items(), cols):
    w = 100 * v / r["E_th"]
    ax.barh(0, w, left=left, color=c, label=f"{k}: {v/24:.2f} kW ({w:.0f}%)")
    left += w
lit = [("Faramarzi 2000, MT meat", 81), ("Faramarzi 2000, MT dairy", 78), ("Faramarzi 1999 multideck", 73)]
for i, (lab, s) in enumerate(lit):
    ax.barh(-1 - i * 0.6, s, height=0.4, color="#2a5c9a", alpha=0.6)
    ax.text(2, -1 - i * 0.6, f"{lab}: infiltration {s}%", va="center", fontsize=8.5, color="white",
            weight="bold")
inf = 100 * (parts["Infiltration - sensible"] + parts["Infiltration - latent (frost)"]) / r["E_th"]
ax.text(inf / 2, 0.48, f"this model: infiltration {inf:.0f}%", ha="center", fontsize=9, weight="bold")
ax.set_yticks([])
ax.set_xlim(0, 100)
ax.set_ylim(-2.6, 0.75)
ax.set_xlabel("% of heat the refrigeration machine must remove")
ax.set_title(f"(a) Heat into the case: {r['Q_avg']:.2f} kW average\n(F6 data-sheet rating: 3.57 kW)", fontsize=11)
ax.legend(fontsize=7.8, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
ax = axes[1]
ek = [("Compressor", r["E_comp"]), ("Anti-sweat\nheaters", r["E_ash"]), ("Defrost\nheaters", r["E_def"]),
      ("Fans", r["E_fan"]), ("Lights", r["E_light"])]
ax.bar([e[0] for e in ek], [e[1] for e in ek], color=["#2a5c9a", "#d0703c", "#a0522d", "#7aa974", "#e0b040"])
for i, (k, v) in enumerate(ek):
    ax.text(i, v + 0.8, f"{v:.1f}\n({100*v/r['E_case']:.0f}%)", ha="center", fontsize=9)
ax.set_ylabel("kWh per day")
ax.set_ylim(0, 58)
ax.set_title(f"(b) Electricity: {r['E_case']:.1f} kWh/day (DOE 2017 limit for this size: 74.3)", fontsize=11)
ax.tick_params(axis="x", labelsize=9)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "T05_load_breakdown.png"), dpi=150)
plt.close(fig)

# comparison of the three outputs: the boundary and the denominator change the answer
fig, ax = plt.subplots(figsize=(11, 6.5))
gn = sorted(results["y_day"]["group"], key=lambda g: -max(results[k]["group"][g][1] for k in OUTPUTS))
x = np.arange(len(gn))
colors = {"y_day": "#3b6fb6", "y_kg": "#7aa974", "E_store": "#d0703c"}
labs = {"y_day": "(a) kWh/day, case boundary", "y_kg": "(b) kWh per kg product per day",
        "E_store": "(c) kWh/day incl. store HVAC (kappa)"}
for j, key in enumerate(OUTPUTS):
    ax.bar(x + (j - 1) * 0.27, [results[key]["group"][g][1] for g in gn], 0.27, color=colors[key], label=labs[key])
ax.axhline(0.05, color="k", ls="--", lw=1)
ax.text(len(gn) - 0.5, 0.06, "threshold 0.05", ha="right", fontsize=9)
ax.set_xticks(x)
ax.set_xticklabels([g.replace(" (", "\n(").replace(" interaction", "\ninteraction") for g in gn],
                   rotation=40, ha="right", fontsize=9)
ax.set_ylabel("Total Sobol index S_T of the aspect")
ax.set_title("Which aspects matter depends on WHAT you divide by and WHERE you draw the boundary", fontsize=11)
ax.legend()
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "T05_outputs_compare.png"), dpi=150)
plt.close(fig)

# threshold sensitivity of the rule
for thr in (0.01, 0.03, 0.05, 0.10):
    keep = [g for g, v in results["y_day"]["group"].items() if v[1] >= thr]
    print(f"threshold {thr}: {keep}")

with open(os.path.join(HERE, "T05_results.json"), "w") as f:
    json.dump(OUT, f, indent=1, default=float)
print("saved figures + T05_results.json")
