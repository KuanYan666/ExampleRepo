"""Main run: three systems x four climates x two venues, three efficiency currencies."""
import pandas as pd, numpy as np, math
import core as C, scenario as S

CITY_TZ = {"Phoenix": -7, "LasVegas": -7, "Houston": -5, "Singapore": 8, "Seville": 2}
CITY_LL = {"Phoenix": (33.45, -112.07), "LasVegas": (36.17, -115.14),
           "Houston": (29.76, -95.37), "Singapore": (1.35, 103.82), "Seville": (37.39, -5.98)}


def load(city, subsample=3):
    df = pd.read_csv(f"data/{city}.csv")
    df["time"] = pd.to_datetime(df["time"])
    lat, lon = CITY_LL[city]
    df["sol_alt"] = [S.solar_altitude(lat, lon, t, CITY_TZ[city]) for t in df.time]
    return df.iloc[::subsample].reset_index(drop=True)


cal = S.calibrate()
print("CALIBRATION AGAINST THE PROBLEM'S OWN TABLE")
print(f"  fan air speed (from 'feels 3C cooler')      : {cal['v_fan']:.2f} m/s")
print(f"  pad saturation efficiency (fixed, lit.)     : {cal['eps_evap']:.2f}")
print(f"  device-outlet drop at design hour           : {cal['outlet_drop_design']:.1f} C")
print(f"  FITTED effective open area of the shelter   : {cal['A_open_fit']:.1f} m2")
print(f"  => capture fraction phi, small / large      : {cal['phi_small']:.3f} / {cal['phi_large']:.3f}")
print(f"  => cooling LOST to the atmosphere           : {100*(1-cal['phi_small']):.1f}% / "
      f"{100*(1-cal['phi_large']):.1f}%")
print(f"  residual vs the two claims (validation)     : {cal['residual']['small']:+.2f} C / "
      f"{cal['residual']['large']:+.2f} C\n")

# the bus stop's open area is the FITTED value; the rail box is more enclosed
S.VENUES["bus_stop"]["A_open_eff"] = cal["A_open_fit"]
S.VENUES["rail_platform"]["A_open_eff"] = cal["A_open_fit"] * 1.6

rows = []
for city in ["Phoenix", "LasVegas", "Seville", "Houston", "Singapore"]:
    df = load(city)
    for venue in ["bus_stop", "rail_platform"]:
        for dev in ["fan", "evap", "evap_big"]:
            r = S.run(df, venue, dev, cal, subsample=1)
            for duty in ["always", "smart"]:
                m = S.metrics(r, hours_per_step=3.0, duty=duty)
                rows.append(dict(city=city, venue=venue, device=dev, duty=duty, **m))
            # climate descriptors
            if dev == "fan" and venue == "bus_stop" and duty == "always":
                pass
    print(f"  {city}: mean T {df.temperature_2m.mean():.1f}C, "
          f"mean RH {df.relative_humidity_2m.mean():.0f}%, "
          f"mean wet-bulb depression "
          f"{np.mean([t - C.T_wetbulb(t, h) for t, h in zip(df.temperature_2m, df.relative_humidity_2m)]):.1f}C")

res = pd.DataFrame(rows)
res.to_csv("results.csv", index=False)

pd.set_option("display.width", 200)
for venue in ["bus_stop", "rail_platform"]:
    print("\n" + "=" * 92)
    print(f"{S.VENUES[venue]['label'].upper()}   (always-on)")
    print("=" * 92)
    sub = res[(res.venue == venue) & (res.duty == "always")]
    p = sub.pivot(index="city", columns="device",
                  values="eta_deg").reindex(["Phoenix", "LasVegas", "Seville", "Houston", "Singapore"])
    print("\n  EFFICIENCY  eta_deg  [person x degC x h of felt cooling per kWh]")
    print(p.round(2).to_string())
    print("\n  winner by eta_deg: ", p.idxmax(axis=1).to_dict())
    p2 = sub.pivot(index="city", columns="device", values="eta_comfort").reindex(p.index)
    print("\n  EFFICIENCY  eta_comfort  [person-hours of discomfort avoided per kWh]")
    print(p2.round(3).to_string())
    print("\n  winner by eta_comfort: ", p2.idxmax(axis=1).to_dict())
    p3 = sub.pivot(index="city", columns="device", values="eta_risk").reindex(p.index)
    print("\n  EFFICIENCY  eta_risk  [person-hours of UTCI heat-stress weight removed per kWh]")
    print(p3.round(3).to_string())
    print("\n  winner by eta_risk: ", p3.idxmax(axis=1).to_dict())

print("\n" + "=" * 92)
print("SMART CONTROL (run only when someone is waiting AND SET_base >= 30C), bus stop")
print("=" * 92)
a = res[(res.venue == "bus_stop") & (res.duty == "always")].set_index(["city", "device"])
s = res[(res.venue == "bus_stop") & (res.duty == "smart")].set_index(["city", "device"])
cmp = pd.DataFrame({"kWh_always": a.kWh, "kWh_smart": s.kWh,
                    "energy_saved_%": 100 * (1 - s.kWh / a.kWh),
                    "service_kept_%": 100 * s.person_comfort_h / a.person_comfort_h,
                    "eta_comfort_always": a.eta_comfort, "eta_comfort_smart": s.eta_comfort})
print(cmp.round(2).to_string())
