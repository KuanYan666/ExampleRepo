"""T10 part 3: an evaporative cooler's FELT benefit is smaller than its AIR-temperature drop.
Two reasons, separated:
  (1) humidity rises (evaporation is constant-enthalpy: heat is swapped, not removed);
  (2) the cooler chills the AIR but not the hot roof/ground/walls (mean radiant temp. tr).
The air speed is held fixed so the fan-like effect of the cooler's blower is excluded."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from T10_lib import *  # noqa

V = 0.5  # m/s at the person, both before and after [ASSUMED: light shelter breeze]


def felt(T, RH, tr, v=V):
    return dict(SET=SET(T, RH, v, tr), UTCI=UTCI(T, RH, v, tr),
                AT=AT_bom(T, RH, v * LOGLAW_1p1_TO_10), HI=HI_nws(T, RH),
                Humidex=humidex_eccc(T, RH), WBGT=WBGT_bom(T, RH))


def gap(T, RH, dT, radiant_follows=False, tr_offset=0.0):
    st = evap_state(T, RH, dT)
    if st is None:
        return None
    Tn, RHn = st
    tr0 = T + tr_offset
    tr1 = tr0 - dT if radiant_follows else tr0
    a, b = felt(T, RH, tr0), felt(Tn, RHn, tr1)
    out = {k: a[k] - b[k] for k in a}
    out.update(T_new=Tn, RH_new=RHn, dW_gkg=1000 * (C.W_from_RH(Tn, RHn) - C.W_from_RH(T, RH)))
    return out


if __name__ == "__main__":
    print("=" * 92)
    print("A. 'Air 5 C / 8 C cooler' -> how much cooler does it FEEL?  (v fixed at 0.5 m/s)")
    print("   felt drop in each index, degC.   tr = mean radiant temperature")
    print("=" * 92)
    cases = {"design 43/12": (43, 12), "Phoenix 41.3/13": (41.3, 13), "Seville 36.2/21": (36.2, 21),
             "Houston 32.5/56": (32.5, 56), "Singapore 31.3/62": (31.3, 62)}
    rows = []
    for name, (T, RH) in cases.items():
        for dT in (5, 8):
            for lab, rf, off in [("tr fixed = T", False, 0.0), ("tr falls with air", True, 0.0),
                                 ("tr fixed = T+10", False, 10.0)]:
                g = gap(T, RH, dT, rf, off)
                if g is None:
                    print(f"{name:18s} dT={dT}: IMPOSSIBLE (wet-bulb depression only "
                          f"{T - C.T_wetbulb(T, RH):.1f} C)")
                    break
                rows.append(dict(case=name, dT_air=dT, radiant=lab, **g))
    df = pd.DataFrame(rows)
    show = df[["case", "dT_air", "radiant", "RH_new", "dW_gkg", "SET", "UTCI", "AT", "HI",
               "Humidex", "WBGT"]].round(2)
    print(show.to_string(index=False))
    df.to_csv(S + "/sprint_out/code/T10_3_evap_gap.csv", index=False)

    print("\nFelt fraction f = (felt drop in SET) / (air drop):")
    for name in cases:
        for dT in (5, 8):
            sub = df[(df.case == name) & (df.dT_air == dT)]
            if len(sub):
                f = {r.radiant: r.SET / dT for r in sub.itertuples()}
                print(f"   {name:18s} dT={dT}:  " + "   ".join(f"{k}: {v:.2f}" for k, v in f.items()))

    print("\n" + "=" * 92)
    print("B. ONE SCALE: how big an AIR drop does an evaporative cooler need to match a fan that")
    print("   truly gives CE = 3 C (still air reference)?  (tr fixed = T, v fixed)")
    print("=" * 92)
    for name, (T, RH) in cases.items():
        lo, hi = 0.0, T - C.T_wetbulb(T, RH) - 1e-3
        if gap(T, RH, hi)["SET"] < 3.0:
            print(f"   {name:18s} even saturating the air (drop {hi:.1f} C) gives only "
                  f"{gap(T, RH, hi)['SET']:.2f} C felt")
            continue
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            if gap(T, RH, mid)["SET"] < 3.0:
                lo = mid
            else:
                hi = mid
        print(f"   {name:18s} air must drop {mid:.2f} C to feel 3 C cooler (SET)")

    print("\n" + "=" * 92)
    print("C. THE ONE SCALE: felt temperature drop FTD (ambient-equivalent degC, same unit as the")
    print("   ASHRAE cooling effect in which the fan's '3 C' is written).")
    print("=" * 92)
    print(f"{'case':18s} {'dT_air':>6} {'v0':>4} | {'FTD surfaces hot':>16} {'FTD surfaces cool':>17}"
          f" | humidity cost  radiant cost")
    rows = []
    for name, (T, RH) in cases.items():
        for dT in (5, 8):
            for v0 in (0.5, 1.0):
                a = ftd_evap(T, RH, dT, v0)
                b = ftd_evap(T, RH, dT, v0, radiant_follows=True)
                if np.isnan(a):
                    continue
                rows.append(dict(case=name, dT=dT, v0=v0, ftd_hot=a, ftd_cool=b))
                print(f"{name:18s} {dT:6d} {v0:4.1f} | {a:16.2f} {b:17.2f} | {dT - b:8.2f} C   {b - a:8.2f} C")
    pd.DataFrame(rows).to_csv(S + "/sprint_out/code/T10_3_ftd.csv", index=False)

    # ------------------------------------------------------------- figure
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 5.0), gridspec_kw=dict(width_ratios=[1.1, 1]))
    ax = axs[0]
    idx = ["SET", "UTCI", "AT", "HI", "Humidex", "WBGT"]
    labels = ["SET", "UTCI", "BoM AT", "NWS HI", "Humidex", "WBGT\n(BoM approx)"]
    x = np.arange(len(idx))
    w = 0.38
    for k, (name, col) in enumerate([("design 43/12", "#d95f02"), ("Houston 32.5/56", "#1b9e77")]):
        r = df[(df.case == name) & (df.dT_air == 5) & (df.radiant == "tr fixed = T")].iloc[0]
        vals = [r[i] for i in idx]
        b = ax.bar(x + (k - 0.5) * w, vals, w, color=col, label=name.replace(" ", " (") + ")")
        for xi, vi in zip(x + (k - 0.5) * w, vals):
            ax.text(xi, vi + (0.08 if vi >= 0 else -0.35), f"{vi:.1f}", ha="center", fontsize=8)
    ax.axhline(5, color="k", ls="--", lw=1.2)
    ax.text(5.55, 5.1, "air drop = 5 °C", ha="right", fontsize=8.5)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("felt drop (°C of the index)")
    ax.set_ylim(0, 7.2)
    ax.set_title("(a) Air 5 °C cooler: what each index says it FEELS like\n"
                 "(air speed fixed 0.5 m/s, hot surfaces unchanged)", fontsize=10)
    ax.legend(fontsize=8.5, loc="upper left", ncol=2)

    ax = axs[1]
    RHs = np.arange(5, 71, 2.5)
    for T, col in [(35, "#1b9e77"), (40, "#e6ab02"), (45, "#d95f02")]:
        for rf, ls, lab in [(True, "-", "surfaces cool too"), (False, "--", "surfaces stay hot")]:
            f = []
            for RH in RHs:
                g = gap(T, RH, 3.0, radiant_follows=rf)
                f.append(np.nan if g is None else g["SET"] / 3.0)
            ax.plot(RHs, f, ls, color=col, lw=2, label=f"{T} °C, {lab}")
    ax.set_xlabel("outdoor relative humidity before cooling (%)")
    ax.set_ylabel("felt fraction  f = ΔSET / ΔT_air")
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.3)
    ax.set_title("(b) Share of a 3 °C air drop that is actually felt (SET)", fontsize=10)
    ax.legend(fontsize=7.5, ncol=2, loc="upper center")
    fig.tight_layout()
    fig.savefig(S + "/sprint_out/figs/T10_evap_felt_vs_air.png", dpi=150)
    print("\nsaved figs/T10_evap_felt_vs_air.png")
