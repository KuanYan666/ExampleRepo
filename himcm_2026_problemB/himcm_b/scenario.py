"""Venue + device scenarios, and the efficiency metrics built on core.py."""
import math
import numpy as np
import pandas as pd
import core as C


# ---------------------------------------------------------------- solar position
def solar_altitude(lat, lon, when, tz_offset_h):
    """NOAA low-precision solar altitude, degrees."""
    doy = when.timetuple().tm_yday
    hr = when.hour + when.minute / 60.0
    g = math.radians((360 / 365.24) * (doy - 81))
    eot = 9.87 * math.sin(2 * g) - 7.53 * math.cos(g) - 1.5 * math.sin(g)   # minutes
    lstm = 15.0 * tz_offset_h
    tc = 4.0 * (lon - lstm) + eot
    lst = hr + tc / 60.0
    ha = math.radians(15.0 * (lst - 12.0))
    dec = math.radians(23.45 * math.sin(math.radians(360 / 365.0 * (doy - 81))))
    la = math.radians(lat)
    s = math.sin(dec) * math.sin(la) + math.cos(dec) * math.cos(la) * math.cos(ha)
    return math.degrees(math.asin(max(-1, min(1, s))))


# ---------------------------------------------------------------- venues
VENUES = {
    "bus_stop": dict(
        label="Open-sided bus shelter",
        area=15.0,          # m2 of waiting area
        A_open=24.0,        # m2 of open perimeter -> big leakage
        svf=0.45,           # roof blocks part of the sky
        shaded=True,        # roof blocks the direct beam
        headway_min=12.0,
        boardings_per_day=420,
    ),
    "rail_platform": dict(
        label="Semi-open rail-station waiting area",
        area=120.0,
        A_open=40.0,        # walls + roof, openings at the ends and the track side
        svf=0.15,
        shaded=True,
        headway_min=8.0,
        boardings_per_day=5200,
    ),
}

# airflow (m3/s) and power (kW). Airflow from typical portable evaporative cooler specs.
DEVICES = {
    "none":      dict(label="No system (shade only)",      P=0.00, Q=0.00,  kind="none"),
    "fan":       dict(label="A. Fan system",                P=0.25, Q=1.10,  kind="fan"),
    "evap":      dict(label="B. Evaporative cooler",        P=1.20, Q=1.10,  kind="evap"),
    "evap_big":  dict(label="C. Large evaporative cooler",  P=2.50, Q=2.50,  kind="evap"),
}

# ---------------------------------------------------------------- ridership shape
HOURLY_SHAPE = np.array([
    .002,.001,.001,.002,.008,.030,.065,.095,.085,.050,.040,.042,
    .048,.045,.048,.062,.090,.098,.070,.045,.030,.020,.012,.007])
HOURLY_SHAPE = HOURLY_SHAPE / HOURLY_SHAPE.sum()


def occupancy(venue, hour):
    """Little's law: N = lambda * W, random arrivals wait headway/2."""
    lam = venue["boardings_per_day"] * HOURLY_SHAPE[hour]     # people per hour
    return lam * (venue["headway_min"] / 60.0) / 2.0


# ---------------------------------------------------------------- calibration
def calibrate(design=(43.0, 12.0), v_still=0.3, eps=0.85, v_design=0.5, C_d=0.6):
    """Recover the hidden parameters from the problem's three claims.

    KEY MODELLING DECISION. The table says 'Effect on SHELTER', not 'effect at the
    device outlet'. So the 5 degC / 8 degC figures are DELIVERED, post-mixing values.
    We therefore fix the pad saturation efficiency at the manufacturer-typical
    eps = 0.85 and fit ONE free parameter -- the shelter's effective open area --
    so the mixing model reproduces BOTH evaporative claims at a common design hour.

    Two claims, one free parameter => the fit is over-determined by one, so the
    residual is a genuine validation of the model against the only data given.
    """
    Td, RHd = design
    v_fan = C.v_fan_from_claimed_CE(3.0, Td, RHd, v_still=v_still)
    wbd = Td - C.T_wetbulb(Td, RHd)
    outlet = eps * wbd                       # device-outlet drop at design

    def delivered(A, Q):
        return (Q / (Q + C_d * A * v_design)) * outlet

    lo, hi = 0.5, 200.0
    for _ in range(80):                      # least-squares fit on A
        mid = 0.5 * (lo + hi)
        err = (delivered(mid, 1.10) - 5.0) + (delivered(mid, 2.50) - 8.0)
        if err > 0: lo = mid
        else:       hi = mid
    A_fit = 0.5 * (lo + hi)
    resid = {"small": delivered(A_fit, 1.10) - 5.0, "large": delivered(A_fit, 2.50) - 8.0}
    return dict(v_fan=v_fan, wb_depression_design=wbd, eps_evap=eps, eps_evap_big=eps,
                A_open_fit=A_fit, outlet_drop_design=outlet, residual=resid,
                phi_small=1.10 / (1.10 + C_d * A_fit * v_design),
                phi_large=2.50 / (2.50 + C_d * A_fit * v_design),
                design=design, C_d=C_d, v_design=v_design)


# ---------------------------------------------------------------- hourly state
def shelter_state(row, venue, dev, cal, phi_override=None):
    """Return (T, RH, v_local, tr) inside the shelter for one hour and one device."""
    Ta, RH, vw = row.temperature_2m, row.relative_humidity_2m, row.wind_speed_10m
    v_local_base = max(0.3, 0.4 * vw)          # sheltered fraction of the free wind
    tr = C.mrt_outdoor(Ta, row.direct_radiation, row.diffuse_radiation,
                       row.sol_alt, svf=venue["svf"], shaded=venue["shaded"])

    if dev["kind"] == "none":
        return Ta, RH, v_local_base, tr

    if dev["kind"] == "fan":
        # fan moves air, changes nothing thermodynamically (0.25 kW of heat is negligible
        # against an open shelter's exchange rate, but we note it in the paper)
        return Ta, RH, max(v_local_base, cal["v_fan"]), tr

    # evaporative: supply air mixes with infiltrating ambient air
    eps = cal["eps_evap"] if dev["P"] < 2.0 else cal["eps_evap_big"]
    Ts, RHs, Ws = C.evaporative_cooler(Ta, RH, eps)
    A_open = venue.get("A_open_eff", venue["A_open"])
    phi = phi_override if phi_override is not None else \
        C.capture_fraction(dev["Q"], A_open, vw, C_d=cal.get("C_d", 0.6),
                           v_floor=cal.get("v_design", 0.5))
    Wa = C.W_from_RH(Ta, RH)
    Tz, Wz = C.mix(Ts, Ws, Ta, Wa, phi)
    RHz = C.RH_from_W(Tz, Wz)
    v_local = max(v_local_base, 0.35 + 0.9 * phi)    # the cooler also blows air
    return Tz, RHz, v_local, tr


def run(df, venue_key, device_key, cal, phi_override=None, subsample=1):
    venue, dev = VENUES[venue_key], DEVICES[device_key]
    base_dev = DEVICES["none"]
    rows = []
    d = df.iloc[::subsample]
    for row in d.itertuples():
        N = occupancy(venue, row.time.hour)
        Tb, RHb, vb, trb = shelter_state(row, venue, base_dev, cal)
        Tc, RHc, vc, trc = shelter_state(row, venue, dev, cal, phi_override)
        sb = C.SET(Tb, RHb, vb, trb)
        sc = C.SET(Tc, RHc, vc, trc)
        ub = C.UTCI(Tb, RHb, max(vb, 0.5), trb)
        uc = C.UTCI(Tc, RHc, max(vc, 0.5), trc)
        rows.append(dict(time=row.time, N=N, T=row.temperature_2m, RH=row.relative_humidity_2m,
                         wind=row.wind_speed_10m, set_base=sb, set_cool=sc,
                         utci_base=ub, utci_cool=uc, T_shelter=Tc, RH_shelter=RHc, v=vc,
                         P=dev["P"]))
    r = pd.DataFrame(rows)
    r["dSET"] = r.set_base - r.set_cool
    r["dD"] = [C.dissatisfied_fraction(a) - C.dissatisfied_fraction(b)
               for a, b in zip(r.set_base, r.set_cool)]
    r["dRisk"] = [C.heat_risk(a) - C.heat_risk(b) for a, b in zip(r.utci_base, r.utci_cool)]
    return r


def metrics(r, hours_per_step=1.0, duty="always"):
    """Aggregate to the three efficiency currencies + the headline energy."""
    if duty == "always":
        on = np.ones(len(r), bool)
    elif duty == "occupied":
        on = r.N.values >= 1.0
    else:  # smart: occupied AND hot
        on = (r.N.values >= 1.0) & (r.set_base.values >= 30.0)
    E = float((r.P.values * on).sum() * hours_per_step)          # kWh
    dser = np.where(on, r.dSET.values, 0.0)
    dD = np.where(on, r.dD.values, 0.0)
    dR = np.where(on, r.dRisk.values, 0.0)
    pdh = float((r.N.values * np.maximum(dser, 0)).sum() * hours_per_step)
    pch = float((r.N.values * np.maximum(dD, 0)).sum() * hours_per_step)
    prh = float((r.N.values * np.maximum(dR, 0)).sum() * hours_per_step)
    return dict(kWh=E,
                person_degC_h=pdh, person_comfort_h=pch, person_risk_h=prh,
                eta_deg=pdh / E if E else float("nan"),
                eta_comfort=pch / E if E else float("nan"),
                eta_risk=prh / E if E else float("nan"),
                mean_dSET=float(np.mean(dser)))
