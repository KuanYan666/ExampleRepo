"""T11 - every summer-2025 afternoon hour (13-17 h): felt-overwhelm crowd and dSET at N=0/200."""
import pathlib, numpy as np, pandas as pd
from scipy.optimize import brentq
import T11_zone_model as M, scenario as SC

OUT = pathlib.Path(__file__).parent / "T11_out"
LOC = dict(Phoenix=(33.45, -112.07, -7), Houston=(29.76, -95.37, -5))
rows = []
for city, (la, lo, tz) in LOC.items():
    d = pd.read_csv(M.S_DIR / "himcm_b" / "data" / f"{city}.csv", parse_dates=["time"])
    d = d[d.time.dt.hour.between(13, 17)].iloc[::2]          # every 2nd afternoon hour
    for r in d.itertuples():
        wx = dict(To=r.temperature_2m, RH=r.relative_humidity_2m, U10=r.wind_speed_10m,
                  Idir=r.direct_radiation, Idif=r.diffuse_radiation, GHI=r.shortwave_radiation,
                  alt=SC.solar_altitude(la, lo, r.time, tz))
        e0 = M.solve_zone(wx, 0, "none")["SET"]
        f = lambda N: M.solve_zone(wx, N, "evap_big")["SET"] - e0
        f0, f1 = f(0), f(3000)
        N_ow = brentq(f, 0, 3000, xtol=2) if (f0 < 0 < f1) else (0.0 if f0 >= 0 else 3000.0)
        b200 = M.solve_zone(wx, 200, "none")["SET"]; c200 = M.solve_zone(wx, 200, "evap_big")["SET"]
        rows.append(dict(city=city, time=r.time, To=r.temperature_2m, RH=r.relative_humidity_2m,
                         wbd=r.temperature_2m - r.wet_bulb_temperature_2m, N_ow=N_ow,
                         dSET0=e0 - M.solve_zone(wx, 0, "evap_big")["SET"], dSET200=b200 - c200))
df = pd.DataFrame(rows)
df.to_csv(OUT / "seasonal.csv", index=False)
for c, g in df.groupby("city"):
    print(c, "hours", len(g), "N_ow median %.0f IQR %.0f-%.0f" % (g.N_ow.median(), g.N_ow.quantile(.25), g.N_ow.quantile(.75)),
          "share hours N_ow<200: %.0f%%" % (100 * (g.N_ow < 200).mean()),
          "| dSET N=0 mean %.2f, N=200 mean %.2f" % (g.dSET0.mean(), g.dSET200.mean()),
          "| ratio(new/old) at N=200 mean %.2f" % ((g.dSET200 / g.dSET0.where(g.dSET0.abs() > 0.05)).median()))
