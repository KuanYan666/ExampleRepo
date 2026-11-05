"""T10 part 4: when does a fan stop helping or start harming?
Three model verdicts (SET comfort, UTCI, two-node core temperature) vs lab evidence
and public-health cut-offs.  Then: how many summer hours fall in each zone, per city."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from T10_lib import *  # noqa

V0, V1 = 0.2, 2.0   # m/s at the person: without fan / with fan  [ASSUMED]


def verdicts(T, RH, v0=V0, v1=V1):
    """Arrays in, arrays out.  Positive = fan helps."""
    T, RH = np.asarray(T, float), np.asarray(RH, float)
    kw = dict(met=MET, clo=CLO, limit_inputs=False, round_output=False)
    dSET = (np.asarray(set_tmp(tdb=T, tr=T, v=np.full_like(T, v0), rh=RH, **kw).set)
            - np.asarray(set_tmp(tdb=T, tr=T, v=np.full_like(T, v1), rh=RH, **kw).set))
    u = lambda v: np.asarray(utci(tdb=T, tr=T, v=np.full_like(T, max(0.5, v * LOGLAW_1p1_TO_10)),
                                  rh=RH, limit_inputs=False).utci, float)
    dUTCI = u(v0) - u(v1)
    f = lambda v: use_fans_heatwaves(tdb=T, tr=T, v=np.full_like(T, v), rh=RH, **kw)
    a, b = f(v0), f(v1)
    dCore = np.asarray(a.t_core) - np.asarray(b.t_core)
    return dSET, dUTCI, dCore, np.asarray(a.heat_strain), np.asarray(b.heat_strain)


if __name__ == "__main__":
    Ts = np.arange(30, 50.01, 0.5)
    RHs = np.arange(5, 90.01, 2.5)
    TT, RR = np.meshgrid(Ts, RHs)
    ok = np.vectorize(e_bom)(TT, RR) < 75          # drop physically absurd corner
    dS, dU, dC, hs0, hs1 = [x.reshape(TT.shape) for x in verdicts(TT.ravel(), RR.ravel())]
    for arr in (dS, dU, dC):
        arr[~ok] = np.nan

    print("=" * 84)
    print(f"A. FAN VERDICTS  (fan raises air speed at the person from {V0} to {V1} m/s, tr = T)")
    print("   + = fan helps, - = fan harms.  dSET, dUTCI in C; dCore in C of core temperature")
    print("=" * 84)
    print(f"{'T':>4} {'RH':>4} | {'dSET':>6} {'dUTCI':>6} {'dCore':>6} | strain no-fan/fan")
    pts = [(32, 70), (34, 80), (36, 25), (36, 45), (36, 80), (38, 30), (40, 15), (40, 50), (42, 15),
           (42, 50), (44, 12), (46, 10), (47, 10), (48, 10)]
    for T, RH in pts:
        s, u, c, h0, h1 = [float(x[0]) for x in verdicts([T], [RH])]
        print(f"{T:>4} {RH:>4} | {s:6.2f} {u:6.2f} {c:6.3f} | {int(h0)}/{int(h1)}")

    print("\nB. Crossover: lowest temperature at which each model says the fan HARMS, by humidity")
    print(f"{'RH':>4} | {'SET':>6} {'UTCI':>6} {'core':>6}")
    for RH in [10, 20, 30, 40, 50, 60, 70, 80]:
        i = np.argmin(abs(RHs - RH))
        out = []
        for arr in (dS, dU, dC):
            row = arr[i]
            j = np.where(row < (0 if arr is not dC else -0.005))[0]
            out.append(f"{Ts[j[0]]:6.1f}" if len(j) else "  none")
        print(f"{RH:>4} | " + " ".join(out))

    # ------------------------------------------------------------- figure
    fig, ax = plt.subplots(figsize=(9.6, 6.2))
    ax.contourf(Ts, RHs, np.where(dC < -0.005, 1.0, np.nan), levels=[0.5, 1.5], colors=["#f4a582"],
                alpha=0.75)
    ax.contour(Ts, RHs, dU, levels=[0], colors="#2166ac", linewidths=2.4)
    if np.nanmin(dS) < 0:
        ax.contour(Ts, RHs, dS, levels=[0], colors="k", linewidths=1.5, linestyles=":")
    ax.plot([], [], color="#2166ac", lw=2.4, label="UTCI: fan harmful below/right of this line")
    ax.fill_between([], [], color="#f4a582", label="two-node model: fan RAISES core temperature")
    ax.plot([], [], "k:", lw=1.5, label="SET: fan never harmful in this range" if np.nanmin(dS) >= 0
            else "SET: fan harmful beyond this line")
    guides = [(32.2, "CDC\n90 °F", "0.3"), (35, "WHO\n35 °C", "0.3"),
              (37, "Morris21\nolder+med", "purple"), (39, "Morris21\nyoung", "purple"),
              (40.6, "WHO\n40 °C", "0.3")]
    for x, lab, col in guides:
        ax.axvline(min(x, 40), color=col, ls="--", lw=1)
    top = ax.secondary_xaxis("top")
    top.set_xticks([g[0] for g in guides])
    top.set_xticklabels([g[1] for g in guides], fontsize=7.5)
    top.tick_params(length=0)
    lab_pts = [(36, 80, "o", "g", "Ravanelli 2015: helps to ~80% RH"),
               (42, 50, "o", "g", "Ravanelli 2015: helps to ~50% RH"),
               (40, 50, "s", "g", "Morris 2019: helps"),
               (47, 10, "X", "r", "Morris 2019: harms (even comfort)"),
               (36, 45, "D", "0.4", "O'Connor 2024, age 65-85:\nno core-temp benefit")]
    offs = [(8, -3), (8, 6), (8, -16), (-8, 4), (-9, -3)]
    for (T, RH, m, c, lab), (dx, dy) in zip(lab_pts, offs):
        ax.plot(T, RH, m, color=c, mec="k", ms=10, zorder=5)
        ax.annotate(lab, (T, RH), xytext=(dx, dy), textcoords="offset points", fontsize=7.5,
                    ha="left" if dx > 0 else "right",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85), zorder=6)
    ax.set_xlim(30, 50)
    ax.set_ylim(5, 90)
    ax.set_xlabel("air temperature (°C)   [shade: mean radiant temperature = air temperature]")
    ax.set_ylabel("relative humidity (%)")
    ax.set_title(f"Where does a fan stop helping?  Fan: {V0} → {V1} m/s at the person, "
                 "standing, 0.36 clo\n(top axis: public-health fan cut-offs)", fontsize=11)
    ax.legend(loc="lower left", fontsize=8, framealpha=0.95)
    fig.tight_layout()
    fig.savefig(S + "/sprint_out/figs/T10_fan_harm_map.png", dpi=150)
    print("\nsaved figs/T10_fan_harm_map.png")

    # ------------------------------------------------------------- city hours
    print("\n" + "=" * 84)
    print("C. SHARE OF SUMMER DAYTIME HOURS (07-20 h, Jun 1-Sep 15 2025) IN EACH ZONE")
    print("=" * 84)
    print(f"{'city':10s} {'>32.2C':>7} {'>35C':>6} {'>39C':>6} {'>40C':>6} | {'UTCI harm':>9} "
          f"{'core harm':>9} {'SET harm':>8}")
    rows = []
    for city in ["Phoenix", "LasVegas", "Seville", "Houston", "Singapore"]:
        d = pd.read_csv(S + f"/himcm_b/data/{city}.csv", parse_dates=["time"])
        d = d[d.time.dt.hour.between(7, 20)]
        T, RH = d.temperature_2m.values, d.relative_humidity_2m.values
        hot = T >= 30
        s, u, c, _, _ = verdicts(T[hot], RH[hot])
        n = len(T)
        r = dict(city=city, cdc=(T > 32.2).mean(), who35=(T > 35).mean(), m39=(T > 39).mean(),
                 who40=(T > 40).mean(), utci=(u < 0).sum() / n, core=(c < -0.005).sum() / n,
                 set=(s < 0).sum() / n)
        rows.append(r)
        print(f"{city:10s} {100*r['cdc']:6.1f}% {100*r['who35']:5.1f}% {100*r['m39']:5.1f}% "
              f"{100*r['who40']:5.1f}% | {100*r['utci']:8.1f}% {100*r['core']:8.1f}% {100*r['set']:7.1f}%")
    pd.DataFrame(rows).to_csv(S + "/sprint_out/code/T10_4_city_zones.csv", index=False)
