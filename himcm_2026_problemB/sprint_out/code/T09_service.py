"""T09 step 4: people-weighted service  S = sum_t N_t * dSET_t * dt  and how occupancy
changes (or does not change) which device is 'most efficient'.

Uses the team's bus-shelter model unchanged (himcm_b/core.py, scenario.py, calibrate()).
Weather: cached Open-Meteo hourly data, 1 Jun - 15 Sep 2025. Occupancy: real NYC stops
(weekday hourly profile, applied to every day of the season -- an assumption).
"""
import sys, pathlib, pickle
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import T09_common as T
sys.path.insert(0, str(T.S.parent / "himcm_b"))
import numpy as np, pandas as pd
import core as C, scenario as SC

CITY_TZ = {"Phoenix": -7, "LasVegas": -7, "Houston": -5, "Singapore": 8, "Seville": 2}
CITY_LL = {"Phoenix": (33.45, -112.07), "LasVegas": (36.17, -115.14),
           "Houston": (29.76, -95.37), "Singapore": (1.35, 103.82), "Seville": (37.39, -5.98)}
CITIES = ["Phoenix", "LasVegas", "Seville", "Houston", "Singapore"]
DEVS = ["fan", "evap", "evap_big"]
NAME = {"fan": "A fan", "evap": "B evap", "evap_big": "C large evap"}
RHO_AIR = 1.15            # kg/m3 near 35 C  [ASSUMED: standard moist-air density, +/-3%]


def load(city):
    df = pd.read_csv(T.S.parent / "himcm_b" / "data" / f"{city}.csv")
    df["time"] = pd.to_datetime(df["time"])
    lat, lon = CITY_LL[city]
    df["sol_alt"] = [SC.solar_altitude(lat, lon, t, CITY_TZ[city]) for t in df.time]
    return df


def hourly_physics(cache=T.D / "T09_physics_cache.pkl"):
    """dSET, dRisk and water use for every hour, city and device with N = 1 person."""
    if cache.exists():
        return pickle.load(open(cache, "rb"))
    cal = SC.calibrate()
    SC.VENUES["bus_stop"]["A_open_eff"] = cal["A_open_fit"]
    SC.occupancy = lambda venue, hour: 1.0            # we apply real occupancy afterwards
    out = {}
    for city in CITIES:
        df = load(city)
        for dev in DEVS:
            r = SC.run(df, "bus_stop", dev, cal)
            r["hour"] = r.time.dt.hour
            if SC.DEVICES[dev]["kind"] == "evap":     # water evaporated = m_air * dW
                eps = cal["eps_evap"]
                w = []
                for row in df.itertuples():
                    _, _, Wout = C.evaporative_cooler(row.temperature_2m, row.relative_humidity_2m, eps)
                    w.append(RHO_AIR * SC.DEVICES[dev]["Q"] * (Wout - C.W_from_RH(
                        row.temperature_2m, row.relative_humidity_2m)) * 3600.0)   # kg/h = L/h
                r["water_L_h"] = w
            else:
                r["water_L_h"] = 0.0
            out[(city, dev)] = r
            print(f"  physics {city:9s} {dev:8s}: mean dSET {r.dSET.mean():5.2f} C, "
                  f"water {r.water_L_h.mean():5.1f} L/h")
    out["cal"] = cal
    pickle.dump(out, open(cache, "wb"))
    return out


def season_metrics(r, L_by_hour, P, policy="smart_occ", cap=None):
    """Aggregate one device-season.
    policy: 'always'      on 24 h/day
            'smart'       on when hot (SET_base >= 30 C) and the device helps (dSET > 0)
            'smart_occ'   'smart' AND someone is waiting (presence sensor): expected on-time
                          fraction in an hour is P(N >= 1) = 1 - exp(-L)
    cap: max persons the device can serve at once (None = everyone in the shelter)."""
    L = L_by_hour[r.hour.values]
    good = np.maximum(r.dSET.values, 0.0)
    risk = np.maximum(r.dRisk.values, 0.0)
    helpful_hot = (r.set_base.values >= 30.0) & (r.dSET.values > 0)
    if policy == "always":
        on = np.ones(len(r))
    elif policy == "smart":
        on = helpful_hot.astype(float)
    else:
        on = helpful_hot * T.p_occupied(L)
    served = L if cap is None else np.array([T.expected_min(l, cap) for l in L])
    # with a presence sensor, nobody is missed: service when on = served (conditional on N>=1
    # the device is on, and E[N; N>=1] = E[N]).  For 'smart' the same holds.
    sw = helpful_hot if policy != "always" else np.ones(len(r), bool)
    S = float((served * good * sw).sum())                     # person-degC-h
    Rk = float((served * risk * sw).sum())                    # person-risk-h
    E = float(P * on.sum())                                   # kWh
    Wt = float((r.water_L_h.values * on).sum()) / 1000.0      # m3
    return dict(S_pdh=S, risk=Rk, kWh=E, water_m3=Wt, hours_on=float(on.sum()),
                eta=S / E if E else np.nan, S_space=float((good * sw).sum()),
                eta_space=float((good * sw).sum()) / E if E else np.nan)


if __name__ == "__main__":
    phys = hourly_physics()
    occ = T.occupancy_table()
    stops = ["303317", "102949", "102445", "551928"]
    lab = occ.drop_duplicates("stop_id").set_index("stop_id").label
    Lh = {s: occ[occ.stop_id == s].sort_values("hour").L.values for s in stops}
    Lh["flat1"] = np.ones(24)                                  # one person, all day
    rows = []
    for city in CITIES:
        for s in list(Lh):
            for dev in DEVS:
                for pol in ["always", "smart", "smart_occ"]:
                    m = season_metrics(phys[(city, dev)], Lh[s], SC.DEVICES[dev]["P"], pol)
                    rows.append(dict(city=city, stop=s, device=dev, policy=pol, **m))
    res = pd.DataFrame(rows)
    res.to_csv(T.D / "T09_service_results.csv", index=False)
    pd.set_option("display.width", 220)

    print("\n=== eta = person-degC-h of felt cooling per kWh, policy = smart_occ ===")
    p = res[res.policy == "smart_occ"].pivot_table(index=["city", "stop"], columns="device", values="eta")
    p["winner"] = p[DEVS].idxmax(axis=1)
    p["A/C ratio"] = p.fan / p.evap_big
    print(p.round(2).to_string())

    print("\n=== does occupancy change the ranking?  eta ratio fan/large-evap by policy ===")
    q = res.pivot_table(index=["city", "policy"], columns=["stop", "device"], values="eta")
    for city in CITIES:
        for pol in ["always", "smart", "smart_occ"]:
            line = []
            for s in ["flat1"] + stops:
                line.append(q.loc[(city, pol), (s, "fan")] / q.loc[(city, pol), (s, "evap_big")])
            print(f"  {city:9s} {pol:9s} " + "  ".join(f"{v:5.2f}" for v in line))
    print("  (columns: flat 1 person, B41, Bx15, Bx41, Q67)")

    print("\n=== season totals for the Bx15 stop (406 boardings/day), smart_occ ===")
    t = res[(res.stop == "102949") & (res.policy == "smart_occ")][
        ["city", "device", "S_pdh", "risk", "kWh", "water_m3", "hours_on", "eta"]]
    print(t.round(1).to_string(index=False))

    # ---------------------------------------------------------------- capacity effect
    print("\n=== coverage cap: fan serves at most c people; coolers serve whole shelter (cap 12) ===")
    cap_rows = []
    for city in ["Phoenix", "Houston"]:
        for s in stops:
            base = {d: season_metrics(phys[(city, d)], Lh[s], SC.DEVICES[d]["P"], "smart_occ", cap=12)
                    for d in ["evap", "evap_big"]}
            for c in [1, 2, 3, 4, 6, 8, 12]:
                f = season_metrics(phys[(city, "fan")], Lh[s], SC.DEVICES["fan"]["P"], "smart_occ", cap=c)
                cap_rows.append(dict(city=city, stop=s, cap_fan=c, eta_fan=f["eta"],
                                     S_fan=f["S_pdh"], S_C=base["evap_big"]["S_pdh"],
                                     eta_B=base["evap"]["eta"], eta_C=base["evap_big"]["eta"]))
    cr = pd.DataFrame(cap_rows)
    cr.to_csv(T.D / "T09_capacity_results.csv", index=False)
    print(cr.round(2).to_string(index=False))
