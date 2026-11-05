"""T10 part 5: all three COMAP devices on ONE scale (felt temperature drop, FTD, degC),
hour by hour over summer 2025 daytime, five cities.  Simple device models:
  A fan     : adds VF m/s at the person on top of the shelter breeze (vector sum)   [ASSUMED]
  B, C evap : air drop = phi * eps * (T - Twb), eps = 0.85, phi = 0.26 / 0.44         [team calibration]
Shade assumed: radiant temperature = air temperature before cooling and is NOT lowered."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from T10_lib import *  # noqa
from T10_4_fan_harm_map import verdicts

VF = 1.0
EPS = 0.85
DEV = {"A fan (0.25 kW)": dict(P=0.25), "B evap (1.2 kW)": dict(P=1.2, phi=0.26),
       "C large evap (2.5 kW)": dict(P=2.5, phi=0.44)}

if __name__ == "__main__":
    out = []
    for city in ["Phoenix", "LasVegas", "Seville", "Houston", "Singapore"]:
        d = pd.read_csv(S + f"/himcm_b/data/{city}.csv", parse_dates=["time"])
        d = d[d.time.dt.hour.between(7, 20) & (d.temperature_2m >= 28)].iloc[::2]
        for r in d.itertuples():
            T, RH = r.temperature_2m, r.relative_humidity_2m
            v0 = max(0.2, 0.4 * r.wind_speed_10m)
            v1 = (v0 ** 2 + VF ** 2) ** 0.5
            wbd = T - C.T_wetbulb(T, RH)
            s, u, c, _, _ = [float(x[0]) for x in verdicts([T], [RH], v0, v1)]
            row = dict(city=city, T=T, RH=RH, v0=v0,
                       fan_ftd=ftd_fan(T, RH, v0, v1), fan_utci_harm=u < 0, fan_core_harm=c < -0.005)
            for k, phi in [("B", 0.26), ("C", 0.44)]:
                dT = phi * EPS * wbd
                row[f"{k}_dTair"] = dT
                row[f"{k}_ftd"] = ftd_evap(T, RH, dT, v0)
            out.append(row)
    df = pd.DataFrame(out)
    df.to_csv(S + "/sprint_out/code/T10_5_hourly.csv", index=False)

    g = df.groupby("city", sort=False).agg(
        hours=("T", "size"), T=("T", "mean"), RH=("RH", "mean"), v0=("v0", "mean"),
        fan_ftd=("fan_ftd", "mean"), fan_utci_harm=("fan_utci_harm", "mean"),
        fan_core_harm=("fan_core_harm", "mean"),
        B_air=("B_dTair", "mean"), B_ftd=("B_ftd", "mean"),
        C_air=("C_dTair", "mean"), C_ftd=("C_ftd", "mean"))
    g["B_ratio"] = g.B_ftd / g.B_air
    g["C_ratio"] = g.C_ftd / g.C_air
    g["fan_per_kW"] = g.fan_ftd / 0.25
    g["B_per_kW"] = g.B_ftd / 1.2
    g["C_per_kW"] = g.C_ftd / 2.5
    pd.set_option("display.width", 200)
    print("Daytime (07-20 h) hours with T >= 28 C, every 2nd hour, Jun 1 - Sep 15 2025")
    print("ftd = felt temperature drop (degC, ambient-equivalent); air = air-temperature drop (degC)")
    print(g.round(2).to_string())
    g.to_csv(S + "/sprint_out/code/T10_5_city_summary.csv")

    fig, ax = plt.subplots(figsize=(10, 5.2))
    cities = list(g.index)
    x = np.arange(len(cities))
    w = 0.17
    ax.bar(x - 2 * w, g.fan_ftd, w, color="#1b9e77", label="A fan: felt drop")
    ax.bar(x - w, g.B_air, w, color="white", edgecolor="#7570b3", hatch="///", label="B evap: AIR drop")
    ax.bar(x, g.B_ftd, w, color="#7570b3", label="B evap: felt drop")
    ax.bar(x + w, g.C_air, w, color="white", edgecolor="#d95f02", hatch="///", label="C large evap: AIR drop")
    ax.bar(x + 2 * w, g.C_ftd, w, color="#d95f02", label="C large evap: felt drop")
    for i, c in enumerate(cities):
        ax.text(i - 2 * w, g.fan_ftd.iloc[i] + 0.12, f"{g.fan_ftd.iloc[i]:.1f}", ha="center", fontsize=7.5)
        ax.text(i, g.B_ftd.iloc[i] + 0.12, f"{g.B_ftd.iloc[i]:.1f}", ha="center", fontsize=7.5)
        ax.text(i + 2 * w, g.C_ftd.iloc[i] + 0.12, f"{g.C_ftd.iloc[i]:.1f}", ha="center", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{c}\n{g['T'].iloc[i]:.0f} °C, {g['RH'].iloc[i]:.0f}% RH\nbreeze {g.v0.iloc[i]:.1f} m/s"
                        for i, c in enumerate(cities)], fontsize=8.5)
    ax.set_ylabel("mean drop over hot daytime hours (°C)")
    ax.set_title("One scale: felt temperature drop vs air-temperature drop, summer 2025 daytime hours ≥ 28 °C\n"
                 "(fan adds 1 m/s; coolers use the team's capture fractions; shade, hot surfaces not cooled)",
                 fontsize=10)
    ax.legend(fontsize=8, ncol=3, loc="upper right")
    ax.set_ylim(0, max(g.C_air.max(), g.fan_ftd.max()) * 1.35)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(S + "/sprint_out/figs/T10_one_scale_cities.png", dpi=150)
    print("saved figs/T10_one_scale_cities.png")
