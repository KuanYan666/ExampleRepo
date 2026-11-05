"""T10 part 2: invert the ASHRAE 55 cooling effect.
What air speed AT THE PERSON must the fan deliver for 'feels 3 C cooler' to be true?"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from T10_lib import *  # noqa

VGRID = np.round(np.arange(0.11, 5.001, 0.01), 3)


def ce_curve(T, RH, tr=None, met=MET, clo=CLO):
    tr = T if tr is None else tr
    n = len(VGRID)
    return np.asarray(cooling_effect(tdb=np.full(n, T), tr=np.full(n, tr), vr=VGRID,
                                     rh=np.full(n, RH), met=met, clo=clo).ce, float)


def v_needed(target, T, RH, **kw):
    ce = ce_curve(T, RH, **kw)
    k = np.argmax(ce >= target)
    if ce[k] < target:
        return np.nan
    if k == 0:
        return VGRID[0]
    return np.interp(target, [ce[k - 1], ce[k]], [VGRID[k - 1], VGRID[k]])


if __name__ == "__main__":
    print("=" * 78)
    print("A. CE (degC) vs air speed, standing person, 0.36 clo, 1.2 met, tr = T")
    print("=" * 78)
    cases = {"design hour (team)": (43, 12), "Phoenix typical": (41.3, 13),
             "Seville typical": (36.2, 21), "Houston typical": (32.5, 56),
             "Singapore typical": (31.3, 62), "indoor office": (27, 50),
             "humid heatwave": (36, 80)}
    vs = [0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0]
    print(f"{'case':22s} {'T':>5} {'RH':>4} | " + " ".join(f"{v:>5}" for v in vs) +
          " | v for CE=3")
    rows = []
    for name, (T, RH) in cases.items():
        ce = [CE(T, RH, v) for v in vs]
        v3 = v_needed(3.0, T, RH)
        rows.append(dict(case=name, T=T, RH=RH, v_CE3=v3, CE_at_0p8=CE(T, RH, 0.8)))
        print(f"{name:22s} {T:5.1f} {RH:4.0f} | " + " ".join(f"{c:5.2f}" for c in ce) +
              f" | {v3:5.2f} m/s")
    pd.DataFrame(rows).to_csv(S + "/sprint_out/code/T10_2_cases.csv", index=False)

    print("\nWHO says: AC at 27 C + fan 'will make the room feel 4 C cooler'.")
    for RH in (40, 50, 60):
        print(f"   at 27 C / {RH}% RH, CE = 4 C needs v = {v_needed(4.0, 27, RH):.2f} m/s")

    print("\n" + "=" * 78)
    print("B. SENSITIVITY of the speed needed for CE = 3 C to the personal factors")
    print("=" * 78)
    for name, (T, RH) in [("dry: Phoenix", (41.3, 13)), ("humid: Houston", (32.5, 56))]:
        for met in (1.0, 1.2, 1.4):
            for clo in (0.36, 0.57):
                print(f"   {name:15s} met={met} clo={clo}:  v = {v_needed(3.0, T, RH, met=met, clo=clo):.2f} m/s")
        print(f"   {name:15s} radiant +5 C (tr=T+5):  v = {v_needed(3.0, T, RH, tr=T + 5):.2f} m/s")

    print("\nTeam helper core.v_fan_from_claimed_CE (still air 0.3 m/s, met 1.1, clo 0.35,"
          " metabolic convection floor ON):")
    for T, RH in [(43, 12), (41.3, 13), (32.5, 56)]:
        print(f"   {T}/{RH}:  core.py says {C.v_fan_from_claimed_CE(3.0, T, RH):.2f} m/s;"
              f"  ASHRAE-55 definition (this memo) says {v_needed(3.0, T, RH):.2f} m/s")

    # ------------------------------------------------------------- map
    Ts = np.arange(26, 47, 1.0)
    RHs = np.arange(5, 96, 5.0)
    V3 = np.full((len(RHs), len(Ts)), np.nan)
    CE08 = np.full_like(V3, np.nan)
    for j, T in enumerate(Ts):
        for i, RH in enumerate(RHs):
            if e_bom(T, RH) > 60:      # physically extreme, skip (beyond any city here)
                continue
            V3[i, j] = v_needed(3.0, T, RH)
            CE08[i, j] = CE(T, RH, 0.8)
    np.save(S + "/sprint_out/code/T10_2_V3.npy", V3)

    fig, ax = plt.subplots(figsize=(8.6, 5.6))
    lv = [0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0]
    cs = ax.contourf(Ts, RHs, V3, levels=lv, cmap="viridis_r", extend="both")
    cl = ax.contour(Ts, RHs, V3, levels=[0.5, 0.8, 1.0, 1.5], colors="white", linewidths=1.0)
    ax.clabel(cl, fmt=lambda x: f"{x:.1f} m/s", fontsize=8)
    cb = fig.colorbar(cs, ax=ax)
    cb.set_label("air speed at the person needed for CE = 3 °C  (m/s)")
    ax.contour(Ts, RHs, CE08, levels=[3.0], colors="red", linewidths=2.2, linestyles="--")
    ax.plot([], [], "r--", lw=2.2, label="ASHRAE 55 limit 0.8 m/s gives exactly 3 °C\n"
                                         "(above-left of line: 0.8 m/s is not enough)")
    pts = {"Phoenix": (41.3, 13), "Las Vegas": (39.9, 7), "Seville": (36.2, 21),
           "Houston": (32.5, 56), "Singapore": (31.3, 62), "design hour": (43, 12)}
    for k, (T, RH) in pts.items():
        ax.plot(T, RH, "o", color="orange", mec="k", ms=7)
        ax.annotate(k, (T, RH), xytext=(5, 5), textcoords="offset points", fontsize=8.5,
                    color="k", bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
    ax.set_xlabel("air temperature (°C)   [mean radiant temperature = air temperature]")
    ax.set_ylabel("relative humidity (%)")
    ax.set_title("How hard must the fan blow for 'feels 3 °C cooler' to be true?\n"
                 "ASHRAE 55 cooling effect, standing person, 0.36 clo, 1.2 met", fontsize=11)
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(S + "/sprint_out/figs/T10_fan_speed_for_3C.png", dpi=150)
    print("\nsaved figs/T10_fan_speed_for_3C.png")

    # ------------------------------------------------------------- C. "3 C cooler than WHAT?"
    print("\n" + "=" * 78)
    print("C. '3 C cooler' THAN WHAT?  The ASHRAE CE compares with still air (0.1 m/s).")
    print("   A bus shelter already has a breeze v0.  Speed needed for 3 C relative to v0:")
    print("=" * 78)
    v0s = [0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 1.5]
    sel = {"design 43/12": (43, 12), "Phoenix 41.3/13": (41.3, 13), "Seville 36.2/21": (36.2, 21),
           "Houston 32.5/56": (32.5, 56), "Singapore 31.3/62": (31.3, 62), "humid 36/80": (36, 80)}
    res = {}
    print(f"{'case':18s} | " + " ".join(f"v0={v:<4}" for v in v0s))
    for k, (T, RH) in sel.items():
        res[k] = [v_for_CE_rel(3.0, T, RH, v0) for v0 in v0s]
        print(f"{k:18s} | " + " ".join(f"{x:7.2f}" for x in res[k]))
    pd.DataFrame(res, index=v0s).to_csv(S + "/sprint_out/code/T10_2_baseline_table.csv")

    print("\nTypical afternoon breeze inside a shelter (ASSUMED 0.4 x 10-m wind, as in core.py):")
    for city in ["Phoenix", "LasVegas", "Seville", "Houston", "Singapore"]:
        d = pd.read_csv(S + f"/himcm_b/data/{city}.csv", parse_dates=["time"])
        aft = d[d.time.dt.hour.between(12, 18)]
        print(f"   {city:10s} median 10-m wind {aft.wind_speed_10m.median():4.1f} m/s -> "
              f"shelter breeze ~{0.4 * aft.wind_speed_10m.median():4.2f} m/s")

    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    vv = np.arange(0.1, 0.701, 0.025)
    colors = {"Phoenix 41.3/13": "#d95f02", "Seville 36.2/21": "#e6ab02",
              "Houston 32.5/56": "#1b9e77", "humid 36/80": "#7570b3"}
    for k, col in colors.items():
        T, RH = sel[k]
        y = [v_for_CE_rel(3.0, T, RH, v0) for v0 in vv]
        ax.plot(vv, y, color=col, lw=2.2, label=f"{k.split()[0]}  ({T} °C, {RH}% RH)")
    ax.axhline(0.8, color="red", ls="--", lw=1.2)
    ax.text(0.33, 0.62, "ASHRAE 55 cap without occupant control: 0.8 m/s", color="red", fontsize=8,
            ha="left")
    ax.axvspan(0.56, 0.7, color="0.85", alpha=0.6)
    ax.text(0.63, 3.0, "3 °C felt cooling\nunreachable even\nat 6 m/s", ha="center", fontsize=8.5)
    ax.axvline(0.1, color="grey", ls=":", lw=1)
    ax.text(0.115, 5.6, "ASHRAE 'still air'\nreference", fontsize=8, color="grey", va="top")
    ax.set_ylim(0, 6)
    ax.set_xlim(0.1, 0.7)
    ax.set_xlabel("breeze already present at the person without the fan, v0 (m/s)")
    ax.set_ylabel("air speed the fan must create at the person (m/s)")
    ax.set_title("'Feels 3 °C cooler' — than what?\nSpeed needed depends mostly on the breeze you compare against",
                 fontsize=11)
    ax.legend(fontsize=8.5, loc="upper center")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(S + "/sprint_out/figs/T10_fan_3C_vs_baseline_breeze.png", dpi=150)
    print("saved figs/T10_fan_3C_vs_baseline_breeze.png")
