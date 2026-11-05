"""T08 analysis: spec sheets, phi vs wind, breakthrough, design options, city hours, figures.
Run:  python3 T08_analysis.py   (from this folder). Prints every number quoted in the memo."""
import sys, os, math
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(SCR, "himcm_b"))
import T08_jetmodel as J
import core as C
import scenario as SC

FIG = os.path.join(HERE, "..", "figs")
CFM = 0.000471947                     # m3/s per cfm (exact definition 1 ft3/min)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
COL = {"teamB": "#4C72B0", "teamC": "#DD8452", "CS300": "#55A868", "CS500": "#C44E52",
       "box": "#7f7f7f"}

# ------------------------------------------------------------------ 0. design hour
cal = SC.calibrate()
dT0 = cal["outlet_drop_design"]                       # 18.75 degC at 43 C / 12 % RH, eps 0.85
print(f"Design hour outlet drop dT0 = {dT0:.2f} C; box calibration phi = "
      f"{cal['phi_small']:.3f}/{cal['phi_large']:.3f}, A_fit = {cal['A_open_fit']:.2f} m2")
PHI_USELESS = 1.0 / dT0                               # phi giving 1 degC zone-average drop
print(f"phi for a 1 degC shelter-average drop at design hour = {PHI_USELESS:.3f}")

# ------------------------------------------------------------------ 1. spec sheets
specs = pd.DataFrame([
    # name, cfm, electrical kW (nameplate or listed), fan dia m, source tag
    ("Hessaire MC37M", 3100, 0.250, np.nan, "retailer listing (alphachooser)"),
    ("Portacool Cyclone 120", 2000, 120 * 2.5 / 1000, np.nan, "Portacool page via search; 2.5 A x 120 V"),
    ("Big Ass Fans Cool-Space 300", 2800, 120 * 4.1 / 1000, 0.457, "BAF cut sheet: 4.1 A @120 V, 0.37 kW motor"),
    ("Portacool Jetstream 270", 22500, 120 * 15.2 / 1000, 1.219, "Portacool legacy page: 15.2 A, 48 in blade"),
    ("Big Ass Fans Cool-Space 500", 24000, 120 * 16.5 / 1000, 1.270, "BAF cut sheet: 16.5 A @120 V, 1.1 kW motor"),
    ("Portacool Hurricane 370", 28500, 120 * 15.2 / 1000, 1.219, "Portacool page: 15.2 A, 48 in blade"),
], columns=["model", "cfm", "kW", "fan_d_m", "source"])
specs["Q_m3s"] = specs.cfm * CFM
specs["m3s_per_kW"] = specs.Q_m3s / specs.kW
specs["U0_fan_disc"] = specs.Q_m3s / (np.pi * specs.fan_d_m ** 2 / 4)
pd.set_option("display.width", 200)
print(specs[["model", "cfm", "Q_m3s", "kW", "m3s_per_kW", "fan_d_m", "U0_fan_disc"]].round(3))
print("team scenario.py devices: B 1.10 m3/s / 1.2 kW = %.2f m3/s per kW; C 2.50/2.5 = %.2f"
      % (1.10 / 1.2, 2.5 / 2.5))
print("market range m3/s per kW: %.1f - %.1f" % (specs.m3s_per_kW.min(), specs.m3s_per_kW.max()))
print("=> at market specific airflow a 1.2 kW cooler moves %.1f-%.1f m3/s, a 2.5 kW one %.1f-%.1f"
      % (1.2 * specs.m3s_per_kW.min(), 1.2 * specs.m3s_per_kW.max(),
         2.5 * specs.m3s_per_kW.min(), 2.5 * specs.m3s_per_kW.max()))

# water use from physics vs spec
rho = 1.12; cp = 1.006; hfg = 2420.0   # kg/m3 at ~43 C, kJ/kgK, kJ/kg at ~20 C
def water_Lph(Q, dT):
    return rho * Q * cp * dT / hfg * 3600.0
print("Hessaire 2.58 gal/h (retailer) at 1.463 m3/s implies a drop of %.1f C"
      % (2.58 * 3.785 / 3600 * hfg / (rho * 1.463 * cp)))
for nm, Q in [("team B", 1.10), ("team C", 2.5), ("CS300", 1.321), ("CS500", 11.33)]:
    print(f"water use at design hour {nm}: {water_Lph(Q, dT0):.0f} L/h")

# ------------------------------------------------------------------ 2. devices for jet model
U0_ASSUMED = 8.0      # m/s outlet speed for team devices; spec fleet 7.8-11.5 m/s (fan disc)
DEV = {
    "teamB": dict(label="Team device B: 1.10 m³/s, d=0.42 m", Q=1.10, d=math.sqrt(4 * 1.10 / (math.pi * U0_ASSUMED))),
    "teamC": dict(label="Team device C: 2.50 m³/s, d=0.63 m", Q=2.50, d=math.sqrt(4 * 2.50 / (math.pi * U0_ASSUMED))),
    "CS300": dict(label="Cool-Space 300: 1.32 m³/s, d=0.46 m", Q=2800 * CFM, d=0.457),
    "CS500": dict(label="Cool-Space 500: 11.3 m³/s, d=1.27 m", Q=24000 * CFM, d=1.270),
}
for k, v in DEV.items():
    v["U0"] = v["Q"] / (math.pi * v["d"] ** 2 / 4)
    print(f"{k}: Q={v['Q']:.2f} d={v['d']:.3f} U0={v['U0']:.2f}")

K_SHELTER = 0.4   # in-shelter wind at 1 m / 10-m wind (scenario.py uses 0.4)  [ASSUMED]

# ------------------------------------------------------------------ 3. phi vs wind
Ua = np.r_[0, np.linspace(0.25, 5, 20)]
res = {}
for k, v in DEV.items():
    res[k] = dict(
        cross_out=np.array([J.phi_device(v["Q"], v["d"], u, 270, "end-fire", dT0) for u in Ua]),
        tail=np.array([J.phi_device(v["Q"], v["d"], u, 0, "end-fire", dT0) for u in Ua]),
        cross_in=np.array([J.phi_device(v["Q"], v["d"], u, 90, "end-fire", dT0) for u in Ua]),
        back=np.array([J.phi_device(v["Q"], v["d"], u, 90, "back-fire", dT0) for u in Ua]),
    )
    r = res[k]
    print(f"\n{k}: phi calm end-fire {r['cross_out'][0]:.3f}, back-fire {r['back'][0]:.3f}")
    for case in ["cross_out", "tail", "cross_in", "back"]:
        print("  %-9s" % case, " ".join("%.3f" % x for x in r[case][[0, 2, 4, 6, 8, 12, 16, 20]]),
              "  at Ua =", " ".join("%.2f" % x for x in Ua[[0, 2, 4, 6, 8, 12, 16, 20]]))


def crossing(x, y, level):
    """first x where y falls below level (linear interpolation)."""
    for i in range(1, len(x)):
        if y[i - 1] >= level > y[i]:
            return x[i - 1] + (level - y[i - 1]) * (x[i] - x[i - 1]) / (y[i] - y[i - 1])
    return np.nan if y[0] < level else np.inf


print("\nBreakthrough (end-fire, cross-wind blowing the jet out of the open front):")
BT = {}
for k, v in DEV.items():
    y = res[k]["cross_out"]
    u_half = crossing(Ua, y, 0.5 * y[0])
    u_use = crossing(Ua, y, PHI_USELESS)
    r_pb = J.breakthrough_r(L_p=5.0, X_e=1.5, d=v["d"])
    u_pb = v["U0"] / r_pb
    BT[k] = (u_half, u_use, u_pb)
    print(f"  {k}: phi halves at Ua={u_half:.2f} m/s (U10={u_half / K_SHELTER:.1f}); "
          f"phi<{PHI_USELESS:.3f} (<1 C) at Ua={u_use:.2f} (U10={u_use / K_SHELTER:.1f}); "
          f"Pratte-Baines centreline leaves front before far end: r<{r_pb:.2f} -> Ua={u_pb:.2f} "
          f"(U10={u_pb / K_SHELTER:.1f})")
# PB to mid-shelter (people at 2.5 m)
for k, v in DEV.items():
    r_mid = J.breakthrough_r(L_p=2.5, X_e=1.5, d=v["d"])
    print(f"  {k}: centreline blown out before reaching mid-shelter (2.5 m) when Ua > {v['U0'] / r_mid:.2f}")
Pi = (5.0 / 1.5) ** (0.28 / 0.72) / 2.05 ** (1 / 0.72)
print(f"Breakthrough group Pi = U0 d/(Ua L_p) = {Pi:.3f} for end-fire; 'bus-stop deflection modulus'"
      f" (pi/4) Pi^2 = {math.pi / 4 * Pi ** 2:.3f}")

# box model for comparison (uses the 10-m wind)
box = {k: np.array([J.box_phi(DEV[k]["Q"], u / K_SHELTER) for u in Ua]) for k in ["teamB", "teamC"]}

# ------------------------------------------------------------------ 4. phi vs outlet diameter (calm)
dd = np.linspace(0.2, 2.0, 19)
phi_d_end = np.array([J.phi_device(8.0 * math.pi * d * d / 4, d, 0, 0, "end-fire", dT0) for d in dd])
phi_d_back = np.array([J.phi_device(8.0 * math.pi * d * d / 4, d, 0, 0, "back-fire", dT0) for d in dd])
d_for = {lvl: float(np.interp(lvl, phi_d_end, dd)) for lvl in (cal["phi_small"], cal["phi_large"])}
print("\nCalm phi vs outlet diameter (end-fire):", " ".join(f"{d:.1f}:{p:.3f}" for d, p in zip(dd[::2], phi_d_end[::2])))
print("outlet diameter that reproduces the calibrated phi in calm air (end-fire):",
      {round(k, 3): round(v, 2) for k, v in d_for.items()})
print("free-jet closed form V/Vzone for d=0.42, L=5: %.3f; d=1.27: %.3f"
      % (J.free_jet_volume(0.42, 5) / J.zone_volume(), J.free_jet_volume(1.27, 5) / J.zone_volume()))
# U0 independence
print("calm phi for d=0.42 with Q=0.5/1.1/2.2/4.4 m3/s:",
      [round(J.phi_device(Q, 0.42, 0, 0, "end-fire", dT0), 3) for Q in (0.5, 1.1, 2.2, 4.4)])

# ------------------------------------------------------------------ 5. design options
phx = pd.read_csv(os.path.join(SCR, "himcm_b", "data", "Phoenix.csv"), parse_dates=["time"])
hot = phx[(phx.time.dt.hour.between(10, 19)) & (phx.temperature_2m >= 35)]
u_med, u_p90 = hot.wind_speed_10m.median(), hot.wind_speed_10m.quantile(0.9)
print(f"\nPhoenix hot daytime hours (T>=35 C, 10-19 h, Jun 1-Sep 15 2025): n={len(hot)}, "
      f"U10 median {u_med:.2f}, p90 {u_p90:.2f} m/s")
Ua_med, Ua_p90 = K_SHELTER * u_med, K_SHELTER * u_p90
PANEL_K = 0.5      # wind reduction by an upwind end panel [ASSUMED, indicative only]


def multi_jet(Q, d, u, theta, n=4):
    """n equal outlets of the same total area, spread across the shelter depth (end-fire)."""
    tot = 0.0
    for i in range(n):
        y0 = 3.0 * (i + 0.5) / n
        J.LAYOUTS["tmp"] = dict(x0=(0.0, y0, 1.0), jet=(1, 0, 0))
        p = J.phi_device(Q / n, d / math.sqrt(n), u, theta, "tmp", dT0)
        tot += p
    return tot


options = [
    ("1 End-fire, cross-wind\nblows jet out the front", lambda Q, d, u: J.phi_device(Q, d, u, 270, "end-fire", dT0)),
    ("2 Back-fire (from back\nwall), wind along street", lambda Q, d, u: J.phi_device(Q, d, u, 90, "back-fire", dT0)),
    ("3 End-fire at upwind end\n(wind along street, tail)", lambda Q, d, u: J.phi_device(Q, d, u, 0, "end-fire", dT0)),
    ("4 = 3 + solid far-end\npanel (upper bound)", lambda Q, d, u: J.phi_device(Q, d, u, 0, "end-fire", dT0, walls=("back", "end1"))),
    ("5 = 1 + side panels\nhalve in-shelter wind", lambda Q, d, u: J.phi_device(Q, d, PANEL_K * u, 270, "end-fire", dT0)),
    ("6 = 1 split into 4\nsmaller outlets", lambda Q, d, u: multi_jet(Q, d, u, 270)),
]
opt_tab = {}
for k in ["teamB", "CS500"]:
    v = DEV[k]
    opt_tab[k] = [(nm, f(v["Q"], v["d"], Ua_med), f(v["Q"], v["d"], Ua_p90), f(v["Q"], v["d"], 0.0))
                  for nm, f in options]
    print(f"\nDesign options for {k} (phi at calm / Phoenix median Ua={Ua_med:.2f} / p90 Ua={Ua_p90:.2f}):")
    for nm, a, b, c0 in opt_tab[k]:
        print("  %-48s %.3f  %.3f  %.3f   -> zone drop %.1f / %.1f / %.1f C"
              % (nm.replace("\n", " "), c0, a, b, c0 * dT0, a * dT0, b * dT0))

# ------------------------------------------------------------------ 6. smart fan speed
print("\nSmart control: lowest outlet speed keeping phi >= 90% of its calm value (CS500 outlet, end-fire, cross-wind out front)")
d5 = DEV["CS500"]["d"]
phi_calm5 = J.phi_device(DEV["CS500"]["Q"], d5, 0, 270, "end-fire", dT0)
winds = np.array([0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5])
U0_need = []
for u in winds:
    lo, hi = 0.3, 40.0
    for _ in range(18):
        mid = 0.5 * (lo + hi)
        p = J.phi_device(mid * math.pi * d5 ** 2 / 4, d5, u, 270, "end-fire", dT0)
        if p >= 0.9 * phi_calm5: hi = mid
        else: lo = mid
    U0_need.append(hi)
U0_need = np.array(U0_need)
U0_max = DEV["CS500"]["U0"]
Pfrac = np.minimum(U0_need / U0_max, 1.0) ** 3
for u, U0n, pf in zip(winds, U0_need, Pfrac):
    print(f"  Ua={u:.2f} (U10={u / K_SHELTER:.2f}) -> U0 >= {U0n:.2f} m/s, r={U0n / u:.1f}, fan power ~{100 * pf:.1f}% of max")
ratio_fit = np.median(U0_need / winds)
print(f"  rule of thumb: U0 ~ {ratio_fit:.1f} x in-shelter wind")
# Phoenix hot hours: energy saving of wind-tracking speed vs always-full
need = np.interp(K_SHELTER * hot.wind_speed_10m.values, winds, U0_need, left=U0_need[0], right=np.inf)
pf_h = np.minimum(need / U0_max, 1.0) ** 3
print(f"  Phoenix hot hours: mean fan power {100 * pf_h.mean():.1f}% of max; hours needing > max speed:"
      f" {100 * np.mean(need > U0_max):.1f}%")

# ------------------------------------------------------------------ 7. cities
print("\nShare of hot daytime hours (10-19 h, T>=35 C; Singapore/Houston: T>=32 C) in which the cooler is")
print("'nearly useless' (shelter-average drop < 1 C, using that hour's own outlet drop), end-fire, cross-wind out front")
city_rows = []
for city in ["Phoenix", "LasVegas", "Seville", "Houston", "Singapore"]:
    df = pd.read_csv(os.path.join(SCR, "himcm_b", "data", f"{city}.csv"), parse_dates=["time"])
    thr = 35 if city in ("Phoenix", "LasVegas", "Seville") else 32
    h = df[(df.time.dt.hour.between(10, 19)) & (df.temperature_2m >= thr)].copy()
    if len(h) == 0:
        continue
    h["dT0"] = [0.85 * (T - C.T_wetbulb(T, RH)) for T, RH in zip(h.temperature_2m, h.relative_humidity_2m)]
    row = dict(city=city, thr=thr, n=len(h), U10_med=h.wind_speed_10m.median(), dT0_med=h.dT0.median())
    for k in ["teamB", "teamC", "CS500"]:
        phi_h = np.interp(K_SHELTER * h.wind_speed_10m.values, Ua, res[k]["cross_out"])
        dz = phi_h * h.dT0.values
        row[f"{k}_useless%"] = 100 * np.mean(dz < 1.0)
        row[f"{k}_mean_dT"] = dz.mean()
    city_rows.append(row)
city = pd.DataFrame(city_rows)
print(city.round(2).to_string(index=False))

# ================================================================== FIGURES
# F1 validation
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
xs = np.logspace(-1, 1.3, 50)
ax[0].fill_between(xs, 1.2 * xs ** 0.34, 2.6 * xs ** 0.28, color="0.85", label="Spread of experiments\n(Margason 1993, via Muppidi & Mahesh 2005)")
ax[0].plot(xs, 2.05 * xs ** 0.28, "k-", lw=2, label="Pratte & Baines (1967)")
for r, ls in [(4, ":"), (10, "--"), (15, "-.")]:
    d = 0.1
    jet = J.integrate_jet(r * math.pi * d * d / 4, d, 1.0, (1, 0, 0), (0, 0, 0), (0, 1, 0), ds=d / 40, s_max=20 * r * d)
    x = jet["pos"][:, 0] / (r * d); z = jet["pos"][:, 1] / (r * d)
    m = x > 0.1
    ax[0].plot(x[m], z[m], ls, color="#C44E52", label=f"Our model, r = {r}")
ax[0].set_xscale("log"); ax[0].set_yscale("log")
ax[0].set_xlabel("Downwind drift  x / (r d)   [-]"); ax[0].set_ylabel("Penetration across wind  z / (r d)   [-]")
ax[0].set_title("(a) Jet bent by wind: model vs experiments", fontsize=10)
ax[0].legend(fontsize=7.5, loc="lower right")
jet = J.integrate_jet(1.0, 0.4, 0.0, (0, 1, 0), (0, 0, 0), (1, 0, 0), ds=0.01, s_max=10)
xd = jet["pos"][:, 0] / 0.4
ax[1].plot(xd, 2 * jet["speed"] / jet["U0"], color="#C44E52", label="Our model (no wind)")
xx = np.linspace(3, 25, 50)
ax[1].plot(xx, np.minimum(5.8 / xx, 1), "k--", label="Measured decay 5.8 d/x\n(Hussein, Capp & George 1994)")
ax[1].set_xlabel("Distance from outlet  x / d   [-]"); ax[1].set_ylabel("Centre-line speed  U / U0   [-]")
ax[1].set_title("(b) Free jet slowing down (calm air)", fontsize=10)
ax[1].set_ylim(0, 1.1); ax[1].legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "T08_fig1_validation.png"), dpi=150); plt.close(fig)

# F2 plan-view maps
fig, ax = plt.subplots(1, 3, figsize=(12, 3.9), sharey=True)
gx, gy = np.meshgrid(np.linspace(-0.5, 7.5, 161), np.linspace(-3.5, 3.5, 141))
v = DEV["CS300"]
for a, u in zip(ax, [0.0, 1.0, 2.5]):
    _, jet = J.phi_device(v["Q"], v["d"], u, 270, "end-fire", dT0, return_jet=True)
    phi = J.phi_device(v["Q"], v["d"], u, 270, "end-fire", dT0)
    Cf = J.concentration_field(jet, gx, gy, 1.1)
    im = a.contourf(gx, gy, Cf * dT0, levels=[0.5, 1, 2, 4, 6, 8, 10, 12, 15, 19], cmap="Blues")
    a.plot([0, 5, 5, 0, 0], [0, 0, 3, 3, 0], "k-", lw=1)
    a.plot([0, 5], [3, 3], "k-", lw=4)                     # back wall
    a.text(2.5, 3.15, "back wall", ha="center", fontsize=8)
    a.text(2.5, -0.35, "open front (kerb)", ha="center", fontsize=8, va="top")
    a.plot(0, 1.5, "s", color="k", ms=7)
    if u > 0:
        a.annotate("", xy=(6.6, -1.6), xytext=(6.6, 0.4), arrowprops=dict(arrowstyle="->", lw=1.5))
        a.text(6.75, -0.6, f"wind\n{u:.1f} m/s", fontsize=8)
    a.set_title(f"In-shelter wind {u:.1f} m/s (10-m wind ≈ {u / K_SHELTER:.1f} m/s)\nφ = {phi:.3f}  → shelter-average drop {phi * dT0:.1f} °C", fontsize=9)
    a.set_xlabel("Along the kerb  x  [m]"); a.set_aspect("equal")
    a.set_xlim(-0.5, 7.5); a.set_ylim(-3.5, 3.5)
ax[0].set_ylabel("Depth  y  [m]")
fig.subplots_adjust(left=0.05, right=0.88, top=0.80, bottom=0.13, wspace=0.08)
cax = fig.add_axes([0.905, 0.15, 0.015, 0.62])
cb = fig.colorbar(im, cax=cax); cb.set_label("Air-temperature drop\nat 1.1 m height [°C]")
fig.suptitle("Where the cooled air goes: Cool-Space-300-class cooler (1.3 m³/s) at the left end, Phoenix design hour (outlet 18.8 °C colder)", fontsize=10)
fig.savefig(os.path.join(FIG, "T08_fig2_planview.png"), dpi=150); plt.close(fig)

# F3 phi vs wind
fig, ax = plt.subplots(figsize=(8.2, 5))
for k in ["CS500", "teamC", "CS300", "teamB"]:
    ax.plot(Ua, res[k]["cross_out"], "-", color=COL[k], lw=2, label=DEV[k]["label"] + " (jet model)")
for k, lab in [("teamC", "C"), ("teamB", "B")]:
    ax.plot(Ua, box[k], "--", color=COL[k], lw=1.2, label=f"Team box model, device {lab}")
ax.plot(0, cal["phi_large"], "D", color=COL["teamC"], ms=8, label="Calibrated φ from COMAP table (C: 0.44, B: 0.26)")
ax.plot(0, cal["phi_small"], "D", color=COL["teamB"], ms=8)
ax.axhline(PHI_USELESS, color="k", lw=1, ls=":")
ax.text(4.95, PHI_USELESS + 0.008, "φ = 0.053: shelter-average drop < 1 °C ('nearly useless')", ha="right", fontsize=8)
ax.set_xlabel("Wind speed inside the shelter at 1 m height  [m/s]")
ax.set_ylabel("Capture fraction φ  [-]\n(share of the air around people that came from the cooler)")
ax.set_xlim(0, 5); ax.set_ylim(0, 0.6)
sec = ax.secondary_xaxis("top", functions=(lambda x: x / K_SHELTER, lambda x: x * K_SHELTER))
sec.set_xlabel("Equivalent 10-m weather-station wind [m/s] (in-shelter = 0.4 × 10-m)")
ax.legend(fontsize=7.5, loc="upper right", framealpha=0.95)
ax.set_title("Cross-wind blowing the jet out of the open front (end-fire layout)", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "T08_fig3_phi_vs_wind.png"), dpi=150); plt.close(fig)

# F4 phi vs outlet diameter
fig, ax = plt.subplots(figsize=(7.5, 4.4))
ax.plot(dd, phi_d_end, "-o", ms=3, color="#C44E52", label="End-fire (throw 5 m along the shelter)")
ax.plot(dd, phi_d_back, "-o", ms=3, color="#4C72B0", label="Back-fire (throw 3 m toward the kerb)")
for lvl, nm in [(cal["phi_small"], "calibrated B 0.26"), (cal["phi_large"], "calibrated C 0.44")]:
    ax.axhline(lvl, color="0.5", ls="--", lw=1)
    ax.text(0.21, lvl + 0.008, nm, fontsize=8, color="0.3")
for nm, d, y, ha in [("team B", DEV["teamB"]["d"], 0.56, "right"), ("CS300", 0.457, 0.56, "left"),
                     ("team C", DEV["teamC"]["d"], 0.56, "left"),
                     ("Jetstream / Hurricane", 1.219, 0.47, "right"), ("CS500", 1.27, 0.56, "left")]:
    ax.axvline(d, color="0.8", lw=1, zorder=0)
    ax.text(d + (0.012 if ha == "left" else -0.012), y, nm, fontsize=7.5, rotation=90, va="bottom", ha=ha)
ax.set_xlabel("Outlet (fan) diameter d  [m]"); ax.set_ylabel("Capture fraction φ in calm air  [-]")
ax.set_ylim(0, 0.8); ax.legend(fontsize=8, loc="upper left")
ax.set_title("Calm air: φ depends on outlet SIZE and throw, not on airflow or fan power", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "T08_fig4_phi_vs_diameter.png"), dpi=150); plt.close(fig)

# F5 design options
fig, axs = plt.subplots(1, 2, figsize=(12, 4.8), sharey=False)
for a, k in zip(axs, ["teamB", "CS500"]):
    names = [o[0] for o in opt_tab[k]]
    y = np.arange(len(names))
    a.barh(y - 0.27, [o[3] * dT0 for o in opt_tab[k]], 0.27, color="#bbbbbb", label="calm")
    a.barh(y, [o[1] * dT0 for o in opt_tab[k]], 0.27, color="#4C72B0", label=f"Phoenix median hot-hour wind (in-shelter {Ua_med:.2f} m/s)")
    a.barh(y + 0.27, [o[2] * dT0 for o in opt_tab[k]], 0.27, color="#C44E52", label=f"Phoenix windy hour, 90th pct ({Ua_p90:.2f} m/s)")
    a.set_yticks(y); a.set_yticklabels(names, fontsize=8); a.invert_yaxis()
    a.set_xlabel("Shelter-average air-temperature drop [°C]\n(= φ × 18.8 °C, Phoenix design hour)")
    a.set_title(DEV[k]["label"], fontsize=10)
    a.axvline(1.0, color="k", ls=":", lw=1)
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=3, fontsize=8, frameon=False)
fig.tight_layout(rect=(0, 0.07, 1, 1)); fig.savefig(os.path.join(FIG, "T08_fig5_design_options.png"), dpi=150); plt.close(fig)

# F6 smart control
fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
ax[0].plot(winds, U0_need, "o-", color="#C44E52")
ax[0].axhline(U0_max, color="k", ls="--", lw=1); ax[0].text(0.3, U0_max + 0.3, f"full speed of a Cool-Space 500 ({U0_max:.1f} m/s)", fontsize=8)
ax[0].set_xlabel("In-shelter wind [m/s]"); ax[0].set_ylabel("Outlet speed needed [m/s]")
ax[0].set_title("(a) Speed that keeps φ at 90% of its calm value", fontsize=10)
ax[0].set_ylim(0, max(U0_max, U0_need.max()) * 1.2)
ax[1].hist(100 * pf_h, bins=np.linspace(0, 100, 21), color="#4C72B0")
ax[1].set_xlabel("Fan power needed, % of full power (fan law: power ∝ speed³)"); ax[1].set_ylabel("Phoenix hot hours [count]")
ax[1].set_title(f"(b) Wind-tracking fan speed: mean {100 * pf_h.mean():.0f}% of full power", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "T08_fig6_smart_speed.png"), dpi=150); plt.close(fig)
print("figures written")
