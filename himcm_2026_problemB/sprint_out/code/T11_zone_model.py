"""
T11 - Semi-open rail-station waiting area: a well-mixed ZONE model
(heat + moisture balance) that nests the team's bus-shelter model.

Everything is steady-state algebra except `simulate_surge`, which integrates the
two zone ODEs (air temperature, humidity ratio) through a train-headway sawtooth.

Units: T degC, W kg/kg dry air, Q m3/s, power W (kW only where labelled), N persons.
Sources for each equation are given in the memo T11_rail_station_zone.md.
"""
import sys, math, pathlib
import numpy as np
import pandas as pd
from scipy.optimize import fsolve
from scipy.integrate import solve_ivp

S_DIR = pathlib.Path(__file__).resolve().parents[2]          # scratchpad
sys.path.insert(0, str(S_DIR / "himcm_b"))
import core as C            # noqa: E402
import scenario as SC       # noqa: E402
from pythermalcomfort.models import two_nodes_gagge, set_tmp   # noqa: E402


def SET(T, RH, v, tr, met=1.1, clo=0.35):
    """Unrounded SET (core.SET rounds to 0.1 degC, too coarse for differences)."""
    return float(set_tmp(tdb=T, tr=tr, v=max(v, 0.1), rh=RH, met=met, clo=clo,
                         limit_inputs=False, round_output=False).set)

RHO, CP, HFG, G = 1.2, 1006.0, 2.43e6, 9.81    # kg/m3, J/kgK, J/kg (water at ~30 C), m/s2
AD = 1.8258                                     # m2 body surface area (pythermalcomfort default)
MET_W = 58.15                                   # W/m2 per met

# ----------------------------------------------------------------------------- venue
ZONE = dict(
    A_floor=120.0,     # m2  [ASSUMED: same as scenario.py rail_platform]
    H=3.5,             # m   ceiling height [ASSUMED]
    A_open=40.0,       # m2  open band on the track side [ASSUMED: scenario.py value]
    h_open=2.0,        # m   height of that opening [ASSUMED]
    kind="single",     # single-sided ventilation (openings on one wall only)
    C_w=0.025,         # single-sided wind coefficient, AM10 range 0.01-0.05 [VERIFIED range]
    Cd=0.6,            # discharge coefficient, AM10 "typical value 0.6" [VERIFIED]
    wind_factor=0.7,   # 10 m wind -> local wind at roof height in town [ASSUMED]
    aho=0.026,         # alpha/h_o for a light-coloured roof, m2K/W [VERIFIED secondary: ASHRAE via Al-Saud]
    dR=3.9,            # long-wave sky correction for horizontal roofs, K [VERIFIED secondary]
    U_roof=5.2,        # W/m2K single-skin metal canopy = 1/(1/17+1/7.5) [ASSUMED film coeffs]
    h_in=7.5,          # W/m2K underside film (conv+rad) [ASSUMED]
    svf=0.15,          # sky view factor through the opening [scenario.py]
    F_ceil=0.2,        # view factor person -> ceiling [ASSUMED]
    A_x=21.0,          # m2 cross-section the through-flow crosses (6 m x 3.5 m) [ASSUMED]
    v_min=0.2,         # m/s still-air floor inside [ASSUMED]
    met=1.1, clo=0.35, # same as core.SET defaults
    A_fan=15.0,        # m2 floor a single fan can serve (= bus-shelter area) [ASSUMED]
)

BUS = dict(ZONE, A_floor=15.0, H=2.5, kind="busstop", A_open=10.694, aho=0.0, U_roof=0.0,
           svf=0.45, F_ceil=0.0, A_x=7.5, A_fan=15.0)   # nested check only


def q_nat(z, U10, dT, Tm):
    """Natural exchange (m3/s). Wind and buoyancy combined in quadrature.
    single : Qw = C_w*A*U (AM10 eq 4.13); Qb = Cd*A/3*sqrt(g h |dT|/T) (Awbi 1996, CIBSE seminar eq 10)
    cross  : Qw = Cd*A*U*sqrt(dCp/2), dCp = 1 (AM10 eq 4.14); Qb two-vent (AM10 eq 4.12)
    busstop: the team's calibrated rule Q = 0.6*A*max(U10, 0.5) (core.capture_fraction)
    """
    if z["kind"] == "busstop":
        return 0.6 * z["A_open"] * max(U10, 0.5)
    U = z["wind_factor"] * U10
    Tk = Tm + 273.15
    if z["kind"] == "single":
        Qw = z["C_w"] * z["A_open"] * U
        Qb = z["Cd"] * z["A_open"] / 3.0 * math.sqrt(G * z["h_open"] * abs(dT) / Tk)
    else:  # cross: half the area on each wall
        A = z["A_open"] / 2
        Qw = z["Cd"] * A * U * math.sqrt(0.5)
        Qb = z["Cd"] * A * math.sqrt(G * z["h_open"] * abs(dT) / Tk)
    return math.sqrt(Qw**2 + Qb**2)


def body(T, tr, v, RH, met=1.1, clo=0.35):
    """Per-person heat released to the air (W): sensible, latent.
    Skin terms from the Gagge two-node model (pythermalcomfort), respiration from
    the standard ASHRAE Fundamentals Ch.9 expressions C_res = 0.0014 M (34 - t_a),
    E_res = 0.0173 M (5.87 - p_a[kPa])."""
    r = two_nodes_gagge(tdb=T, tr=tr, v=max(v, 0.1), rh=RH, met=met, clo=clo,
                        round_output=False)
    M = met * MET_W
    pa = RH / 100 * C.p_ws(T) / 1000.0
    c_res = 0.0014 * M * (34.0 - T)
    e_res = 0.0173 * M * (5.87 - pa)
    sens = (float(r.q_sensible) + c_res) * AD
    lat = (float(r.e_skin) + e_res) * AD
    return sens, lat


def weather_point(city, which="median"):
    """A representative summer afternoon (13-17 h) for a city from the cached data."""
    d = pd.read_csv(S_DIR / "himcm_b" / "data" / f"{city}.csv", parse_dates=["time"])
    a = d[d.time.dt.hour.between(13, 17)]
    f = (lambda s: s.median()) if which == "median" else (lambda s: s.quantile(0.95))
    loc = dict(Phoenix=(33.45, -112.07, -7), Houston=(29.76, -95.37, -5),
               LasVegas=(36.17, -115.14, -7), Seville=(37.39, -5.98, 2),
               Singapore=(1.35, 103.82, 8))[city]
    alt = SC.solar_altitude(loc[0], loc[1], pd.Timestamp("2025-07-15 15:00"), loc[2])
    return dict(To=float(f(a.temperature_2m)), RH=float(a.relative_humidity_2m.median()),
                U10=float(a.wind_speed_10m.median()), Idir=float(a.direct_radiation.median()),
                Idif=float(a.diffuse_radiation.median()), GHI=float(a.shortwave_radiation.median()),
                alt=alt, city=city)


CAL = SC.calibrate()          # team's bus-shelter calibration: eps = 0.85, v_fan, A_fit
DEV = SC.DEVICES


def solve_zone(wx, N, dev_key, z=ZONE, mode="O", cal=CAL, sun=True, people=True,
               eps=None):
    """Steady heat + moisture balance of a well-mixed zone.

    0 = rho cp Qs (Ts - Tz) + rho cp Qn (To - Tz) + N*s(Tz) + A*q_roof + P
    0 = rho Qs (Ws - Wz) + rho Qn (Wo - Wz) + N*l(Tz)/h_fg
    mode 'O': cooler draws OUTDOOR air;  mode 'R': cooler recirculates ZONE air.
    """
    dev = DEV[dev_key]
    To, RHo, U10 = wx["To"], wx["RH"], wx["U10"]
    Wo = C.W_from_RH(To, RHo)
    GHI = wx["GHI"] if sun else 0.0
    tr_sh = C.mrt_outdoor(To, wx["Idir"] if sun else 0, wx["Idif"] if sun else 0,
                          wx["alt"], svf=z["svf"], shaded=True)
    evap = dev["kind"] == "evap"
    Qs = dev["Q"] if evap else 0.0
    P = dev["P"] * 1000.0
    eps = cal["eps_evap"] if eps is None else eps

    def pieces(Tz, Wz):
        RHz = C.RH_from_W(Tz, max(Wz, 1e-5))
        Qn = max(q_nat(z, U10, Tz - To, 0.5 * (Tz + To)), 1e-4)
        if evap and mode == "O":
            Ts, _, Ws = C.evaporative_cooler(To, RHo, eps)
        elif evap:
            Ts, _, Ws = C.evaporative_cooler(Tz, RHz, eps)
        else:
            Ts, Ws = Tz, Wz
        v = max(z["v_min"], (Qs + Qn) / z["A_x"])
        q_roof = z["U_roof"] * (To + z["aho"] * GHI - (z["dR"] if sun else 0) - Tz)
        T_ceil = Tz + q_roof / z["h_in"] if z["h_in"] else Tz
        tr = (((1 - z["F_ceil"]) * (tr_sh + 273.15)**4 + z["F_ceil"] * (T_ceil + 273.15)**4)
              ** 0.25 - 273.15)
        s, l = body(Tz, tr, v, RHz, z["met"], z["clo"]) if (people and N > 0) else (0.0, 0.0)
        return dict(RHz=RHz, Qn=Qn, Ts=Ts, Ws=Ws, v=v, q_roof=q_roof, tr=tr, s=s, l=l)

    def resid(x):
        Tz, Wz = x[0], x[1] / 1000.0
        p = pieces(Tz, Wz)
        H = (RHO * CP * Qs * (p["Ts"] - Tz) + RHO * CP * p["Qn"] * (To - Tz)
             + N * p["s"] + z["A_floor"] * p["q_roof"] + P)
        M = RHO * Qs * (p["Ws"] - Wz) + RHO * p["Qn"] * (Wo - Wz) + N * p["l"] / HFG
        return [H / 1000.0, M * 1e3]

    x0 = [To - (5 if evap else -1), Wo * 1000 + (3 if evap else 0.5)]
    sol, info, ier, msg = fsolve(resid, x0, full_output=True)
    Tz, Wz = sol[0], sol[1] / 1000.0
    p = pieces(Tz, Wz)
    out = dict(Tz=Tz, Wz=Wz, RHz=p["RHz"], Qn=p["Qn"], Qs=Qs, phi=Qs / (Qs + p["Qn"]),
               v=p["v"], tr=p["tr"], s=p["s"], l=p["l"], G_people_s=N * p["s"],
               G_people_l=N * p["l"], G_roof=z["A_floor"] * p["q_roof"], P=P,
               cool_cap=RHO * CP * Qs * (To - p["Ts"]) if evap else 0.0,
               ok=(ier == 1), tau_s=z["A_floor"] * z["H"] / (Qs + p["Qn"]))
    # felt temperature
    set_main = SET(Tz, out["RHz"], out["v"], out["tr"], z["met"], z["clo"])
    if dev["kind"] == "fan":
        f = min(1.0, z["A_fan"] / z["A_floor"])
        set_fan = SET(Tz, out["RHz"], max(out["v"], cal["v_fan"]), out["tr"], z["met"], z["clo"])
        out["SET"] = f * set_fan + (1 - f) * set_main
    else:
        out["SET"] = set_main
    return out


def overwhelm_N_air(wx, dev_key, z=ZONE, s_person=None):
    """Closed form (mode O, fixed per-person gain): crowd at which T_zone = T_outdoor.
    rho cp Qs (To - Ts) = N s + Q_roof + P  ->  N = (cool_cap - Q_roof - P)/s ."""
    r0 = solve_zone(wx, 0, dev_key, z)
    Tq = wx["To"]
    s = s_person if s_person else body(Tq, r0["tr"], r0["v"], wx["RH"])[0]
    Qroof = z["A_floor"] * z["U_roof"] * (z["aho"] * wx["GHI"] - z["dR"])
    return (r0["cool_cap"] - Qroof - r0["P"]) / s, s, r0["cool_cap"], Qroof


# ----------------------------------------------------------------------------- surges
def simulate_surge(wx, N_mean, headway_min, dev_key="evap_big", z=ZONE, mode="O",
                   n_cycles=6, cal=CAL):
    """Zone ODEs through a train sawtooth: N rises linearly from 0 to 2*N_mean over one
    headway, then the train takes everyone (Little's law mean = N_mean).
      V rho cp dTz/dt = [heat terms of solve_zone]
      V rho    dWz/dt = [moisture terms]"""
    dev = DEV[dev_key]
    To, RHo, U10 = wx["To"], wx["RH"], wx["U10"]
    Wo = C.W_from_RH(To, RHo)
    H = headway_min * 60.0
    V = z["A_floor"] * z["H"]
    evap = dev["kind"] == "evap"
    Qs = dev["Q"] if evap else 0.0
    P = dev["P"] * 1000.0
    Ts_o, _, Ws_o = C.evaporative_cooler(To, RHo, cal["eps_evap"])
    tr_sh = C.mrt_outdoor(To, wx["Idir"], wx["Idif"], wx["alt"], svf=z["svf"], shaded=True)

    def Nt(t):
        return 2.0 * N_mean * ((t % H) / H)

    def rhs(t, y):
        Tz, Wz = y[0], y[1] / 1000
        RHz = C.RH_from_W(Tz, Wz)
        Qn = max(q_nat(z, U10, Tz - To, 0.5 * (Tz + To)), 1e-4)
        Ts, Ws = (Ts_o, Ws_o) if (evap and mode == "O") else \
            (C.evaporative_cooler(Tz, RHz, cal["eps_evap"])[0::2] if evap else (Tz, Wz))
        v = max(z["v_min"], (Qs + Qn) / z["A_x"])
        q_roof = z["U_roof"] * (To + z["aho"] * wx["GHI"] - z["dR"] - Tz)
        T_ceil = Tz + q_roof / z["h_in"]
        tr = (((1 - z["F_ceil"]) * (tr_sh + 273.15)**4 + z["F_ceil"] * (T_ceil + 273.15)**4)
              ** 0.25 - 273.15)
        N = Nt(t)
        s, l = body(Tz, tr, v, RHz, z["met"], z["clo"])
        dT = (RHO * CP * Qs * (Ts - Tz) + RHO * CP * Qn * (To - Tz) + N * s
              + z["A_floor"] * q_roof + P) / (V * RHO * CP)
        dW = (RHO * Qs * (Ws - Wz) + RHO * Qn * (Wo - Wz) + N * l / HFG) / (V * RHO)
        return [dT, dW * 1000]

    r0 = solve_zone(wx, N_mean, dev_key, z, mode)
    t_end = n_cycles * H
    t_eval = np.linspace(0, t_end, int(n_cycles * headway_min * 12) + 1)   # every 5 s
    sol = solve_ivp(rhs, (0, t_end), [r0["Tz"], r0["Wz"] * 1000], t_eval=t_eval,
                    max_step=10.0, rtol=1e-6)
    return sol.t, sol.y[0], sol.y[1] / 1000, np.array([Nt(t) for t in sol.t]), r0


def feel(wx, Tz, Wz, dev_key="evap_big", z=ZONE):
    """SET for a given zone state (used along ODE trajectories), with air speed and
    mean radiant temperature computed exactly as in solve_zone."""
    dev = DEV[dev_key]
    To = wx["To"]
    Qs = dev["Q"] if dev["kind"] == "evap" else 0.0
    RHz = C.RH_from_W(Tz, Wz)
    Qn = max(q_nat(z, wx["U10"], Tz - To, 0.5 * (Tz + To)), 1e-4)
    v = max(z["v_min"], (Qs + Qn) / z["A_x"])
    tr_sh = C.mrt_outdoor(To, wx["Idir"], wx["Idif"], wx["alt"], svf=z["svf"], shaded=True)
    q_roof = z["U_roof"] * (To + z["aho"] * wx["GHI"] - z["dR"] - Tz)
    T_ceil = Tz + q_roof / z["h_in"]
    tr = (((1 - z["F_ceil"]) * (tr_sh + 273.15)**4 + z["F_ceil"] * (T_ceil + 273.15)**4) ** 0.25 - 273.15)
    return SET(Tz, RHz, v, tr, z["met"], z["clo"])
