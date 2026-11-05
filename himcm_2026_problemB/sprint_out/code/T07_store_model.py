"""T07 - The supermarket as a NESTED system: outdoors -> store -> freezer case.

Hourly, quasi-steady heat AND moisture balance of the store air, coupled to
(a) open vertical freezer (LT, low-temperature) cases and (b) open fridge (MT,
medium-temperature) cases, with front-door infiltration driven by customer traffic.

Run:  python3 T07_store_model.py      (needs numpy, pandas; weather JSON cached in data_T07/)

Why quasi-steady (algebra each hour, no ODE)?  The store air time constant is ~30 min
(team timescale analysis) and our weather is hourly, so each hour the store is close to
its own equilibrium.  Product and frost are slow, but they are not what this task asks.

Units: T degC, W (humidity ratio) kg/kg dry air, mass flow kg/s, power kW, energy kWh.
"""
import json, os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data_T07")
P_ATM = 101325.0
CP = 1.006          # kJ/kg/K dry air                         [VERIFIED: ASHRAE Fund. Ch.1]
H_FG = 2501.0       # kJ/kg latent heat, vapour -> water        [VERIFIED: ASHRAE Fund. Ch.1]
H_SG = 2835.0       # kJ/kg latent heat, vapour -> ice (frost)  [VERIFIED: standard value]
RHO = 1.2           # kg/m3 air density near 20 degC          [VERIFIED: standard value]


# ------------------------------------------------------------------ psychrometrics (vectorised)
def p_ws(T):
    """Saturation vapour pressure over liquid water, Pa (Hyland-Wexler, ASHRAE Fund. Ch.1),
    same formula as himcm_b/core.py but numpy-vectorised."""
    Tk = np.asarray(T, float) + 273.15
    c = (-5.8002206e3, 1.3914993, -4.8640239e-2, 4.1764768e-5, -1.4452093e-8, 6.5459673)
    return np.exp(c[0] / Tk + c[1] + c[2] * Tk + c[3] * Tk**2 + c[4] * Tk**3 + c[5] * np.log(Tk))


def W_from_RH(T, RH):
    pw = np.asarray(RH, float) / 100.0 * p_ws(T)
    return 0.621945 * pw / (P_ATM - pw)


def RH_from_W(T, W):
    pw = P_ATM * np.asarray(W, float) / (0.621945 + np.asarray(W, float))
    return np.minimum(100.0, 100.0 * pw / p_ws(T))


# ------------------------------------------------------------------ door infiltration
# PNNL-20026 (Cho, Gowri & Liu 2010), Tables 6 & 10: ASHRAE / Yuill RP-763 method
# Q = C_A * A * R_p, automatic 3 ft x 7 ft door (21 ft2), outdoor 60 F.
# (door openings per hour, cfm).  Pairs taken from Table 6 (all prototypes <= 20 ft tall)
# and Table 10 (quick-service restaurant sensitivity runs).
PNNL_NO_VEST = np.array([(1, 40), (6, 187), (9, 275), (15, 432), (57, 1302), (63, 1417),
                         (72, 1585), (81, 1751), (90, 1913), (99, 2073), (108, 2231),
                         (117, 2386), (153, 3006)], float)
PNNL_VEST = np.array([(1, 21), (6, 108), (9, 162), (15, 260), (57, 826), (90, 1237),
                      (153, 1986)], float)
CFM = 0.000471947   # m3/s per cfm


def fit_power(tab):
    b, ln_a = np.polyfit(np.log(tab[:, 0]), np.log(tab[:, 1]), 1)
    return np.exp(ln_a), b


A_NV, B_NV = fit_power(PNNL_NO_VEST)
A_V, B_V = fit_power(PNNL_VEST)


def door_flow_m3s(N, T_out, vestibule=False):
    """Door infiltration, m3/s, for N door openings per hour.
    Temperature correction from PNNL-20026 Table 9: +7.0 % going 60 F -> -40 F, i.e.
    +0.07 % per degF colder than 60 F (and -0.035 %/F warmer; we use one slope)."""
    a, b = (A_V, B_V) if vestibule else (A_NV, B_NV)
    N = np.asarray(N, float)
    q = np.where(N > 0, a * np.maximum(N, 1e-9) ** b, 0.0) * CFM
    T_F = np.asarray(T_out) * 9 / 5 + 32
    return q * (1 + 0.0007 * (60 - T_F))


# ------------------------------------------------------------------ store definition
STORE = dict(
    area=2294.0,        # m2  = 24,695 ft2 PNNL stand-alone retail prototype   [VERIFIED: PNNL-20026 Tab.1]
    height=6.1,         # m   = 20 ft                                          [VERIFIED: PNNL-20026 Tab.1]
    UA=2.0,             # kW/K roof+walls+glazing                              [ASSUMED: U~0.35-0.5 W/m2K on ~5000 m2]
    ach_env=0.10,       # 1/h background envelope leakage                      [ASSUMED]
    vent_area=0.3e-3,   # m3/s per m2 floor (0.06 cfm/ft2)                     [ASSUMED: ASHRAE 62.1 retail, recalled]
    vent_person=3.8e-3, # m3/s per person (7.5 cfm)                            [ASSUMED: ASHRAE 62.1, recalled]
    q_light=25.0e-3,    # kW/m2 lights + checkouts + deli/bakery + RTU fans, open hours [ASSUMED]
    q_light_night=5.0e-3,
    p_sens=0.075, p_lat=0.055,  # kW per shopper                               [VERIFIED: ASHRAE 1997 Fund. Ch.28 Tab.3]
    T_cool=24.0, T_heat=21.0,   # thermostat dead band, degC                   [ASSUMED; 23.9 C = case rating point]
    RH_cap=55.0,        # % used only in the 'humidity-controlled' variant     [VERIFIED: case makers' 55 % ceiling, via ORNL 2011 & web]
    T_coil=13.0, W_coil=None,   # AC supply air 13 C, ~ saturated at 12 C       [ASSUMED: typical rooftop unit]
    COP_AC=3.0,         # rooftop AC, kW cooling / kW electricity              [ASSUMED: as team's nested.py]
    eta_heat=0.80,      # gas furnace efficiency                               [ASSUMED]
    kWh_per_kg_dehum=0.77,  # extra dehumidification (over-cool+reheat)        [VERIFIED: Khattar 1992 0.25-0.45 kWh/lb, midpoint, via ORNL 2011 p.1]
    open_from=7, open_to=22,  # opening hours                                  [ASSUMED]
    N_peak=153.0,       # door openings/h at peak                              [VERIFIED: PNNL-20026 Tab.5, Yuill field data, 52 stores]
    N_offpeak=15.0,     # off-peak openings/h (= peak/10)                      [VERIFIED: PNNL-20026 Tab.5]
    N_closed=2.0,       # staff/deliveries while closed                        [ASSUMED]
)
STORE["W_coil"] = float(W_from_RH(12.0, 100.0))
STORE["vol"] = STORE["area"] * STORE["height"]

# Freezer (LT) case: one 2.5 m open vertical case, rated at 23.9 C / 55 % RH
T_LT, RH_LT = -18.0, 90.0              # case air                              [team baseline]
W_LT = float(W_from_RH(T_LT, RH_LT))
LT = dict(n=12, Q_rated=2.5, f_inf=0.75, Q_wallrad=0.30, P_int=0.325,
          # n cases [ASSUMED]; 2.5 kW, 75 % infiltration [team baseline]; split of the
          # remaining 0.625 kW into walls/radiation (from store) vs fans/lights/heaters [ASSUMED]
          T=T_LT, W=W_LT, h_phase=H_SG, COP_ref=1.7, Tc_ref=35.0)
# Fridge (MT) lineup (lumped), always on a remote rooftop rack
T_MT = 3.0
W_MT = float(W_from_RH(T_MT, 90.0))
MT = dict(Q_rated=45.0, f_inf=0.70, Q_wallrad=7.0, P_int=6.5,   # [ASSUMED sizes]
          T=T_MT, W=W_MT, h_phase=H_FG, COP_ref=2.5, Tc_ref=35.0)  # COP 2.5 [VERIFIED: Westphalen 1996 via ORNL Tab.6]
T_EVAP_OFFSET = 10.0    # evaporator 10 K below case air                       [ASSUMED]
T_RATED, RH_RATED = 23.9, 55.0                                                 # [VERIFIED: EnergyPlus Eng. Ref.]
W_RATED = float(W_from_RH(T_RATED, RH_RATED))


def calibrate(case):
    """Air mass flow through the curtain that reproduces the rated infiltration load."""
    per_kg = CP * (T_RATED - case["T"]) + case["h_phase"] * (W_RATED - case["W"])
    case["m_inf"] = case["f_inf"] * case["Q_rated"] / per_kg   # kg/s per case (or lineup)
    case["per_kg_rated"] = per_kg
    return case


calibrate(LT); calibrate(MT)


def case_load(case, T_i, W_i):
    """Evaporator load (kW) of ONE LT case or the whole MT lineup.
    returns total, sensible-from-store, latent-from-store, internal electrical."""
    m = case["m_inf"]
    sens = m * CP * (T_i - case["T"]) + case["Q_wallrad"] * (T_i - case["T"]) / (T_RATED - case["T"])
    lat = m * case["h_phase"] * np.maximum(W_i - case["W"], 0.0)
    return sens + lat + case["P_int"], sens, lat, case["P_int"]


def cop(case, T_cond):
    """Carnot-scaled COP: fixed fraction of the Carnot COP, calibrated so COP = COP_ref
    at 35 C condensing.  Evaporating temperature = case air - 10 K."""
    Te = case["T"] - T_EVAP_OFFSET + 273.15
    carnot = Te / (np.asarray(T_cond) + 273.15 - Te)
    carnot_ref = Te / (case["Tc_ref"] + 273.15 - Te)
    return case["COP_ref"] * carnot / carnot_ref


def T_cond_remote(T_out):
    """Rooftop air-cooled condenser: outdoor + 10 K, floating head pressure,
    floor 21 C                                                               [ASSUMED]"""
    return np.maximum(np.asarray(T_out) + 10.0, 21.0)


# ------------------------------------------------------------------ traffic schedule
def door_schedule(hours, N_peak, S=STORE):
    """Door openings per hour.  Open hours follow a two-hump shopping profile scaled so
    the busiest hour = N_peak and the quietest open hour ~ N_peak/10 (PNNL off-peak ratio).
    The shape itself is ASSUMED (lunch + after-work peaks)."""
    h = np.asarray(hours, float)
    shape = 0.65 * np.exp(-0.5 * ((h - 12.5) / 1.8) ** 2) + 1.0 * np.exp(-0.5 * ((h - 17.5) / 1.8) ** 2)
    hh = np.arange(24)
    shp_all = 0.65 * np.exp(-0.5 * ((hh - 12.5) / 1.8) ** 2) + 1.0 * np.exp(-0.5 * ((hh - 17.5) / 1.8) ** 2)
    shape = shape / shp_all.max()
    is_open = (h >= S["open_from"]) & (h < S["open_to"])
    N = np.where(is_open, N_peak * (0.1 + 0.9 * shape), S["N_closed"] * (N_peak > 0))
    return N, is_open


# ------------------------------------------------------------------ weather
def load_weather(city):
    with open(os.path.join(DATA, f"wx_{city}_2023.json")) as f:
        j = json.load(f)
    df = pd.DataFrame(j["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    df = df.rename(columns={"temperature_2m": "T_o", "relative_humidity_2m": "RH_o"})
    df["T_o"] = df["T_o"].interpolate().bfill().ffill()
    df["RH_o"] = df["RH_o"].interpolate().bfill().ffill()
    df["W_o"] = W_from_RH(df["T_o"].values, df["RH_o"].values)
    return df


# ------------------------------------------------------------------ the hourly solver
def simulate(wx, N_peak=153.0, vestibule=False, config="remote", rh_control=False,
             n_LT=None, door_override=None, people_peak=153.0, S=STORE):
    """config: 'remote'   - LT condenser on the roof (typical supermarket rack)
               'plugin'   - self-contained LT cases, condenser heat dumped in the store
               'reclaim'  - remote rack + heat-reclaim coil: in heating hours up to 80 % of
                            the LT condenser heat is delivered to the store            [ASSUMED 80 %]
    rh_control: if True the HVAC holds store RH <= 55 % (extra dehumidification cost).
    door_override: if given, a fixed array of door flow (m3/s) replacing the schedule.
    people_peak: shoppers are set by the BASELINE traffic (people = openings/2 at
                 people_peak), so changing N_peak changes only the air through the door."""
    n_LT = LT["n"] if n_LT is None else n_LT
    T_o, W_o = wx["T_o"].values, wx["W_o"].values
    hour = wx["time"].dt.hour.values
    N, is_open = door_schedule(hour, N_peak, S)
    q_door = door_flow_m3s(N, T_o, vestibule) if door_override is None else door_override
    N_people, _ = door_schedule(hour, people_peak, S)
    people = np.where(is_open, N_people / 2.0, 3.0)   # PNNL rule: shoppers in store = openings/2
    m_door = RHO * q_door
    m_env = RHO * S["ach_env"] * S["vol"] / 3600.0
    m_vent = RHO * np.where(is_open, S["vent_area"] * S["area"] + S["vent_person"] * people, 0.0)
    m_out = m_door + m_env + m_vent             # outdoor air entering (same mass leaves)
    q_int = np.where(is_open, S["q_light"], S["q_light_night"]) * S["area"] + S["p_sens"] * people
    g_lat = S["p_lat"] * people / H_FG          # kg/s water from shoppers

    Tc_rem_LT = T_cond_remote(T_o)
    Tc_rem_MT = T_cond_remote(T_o)

    # ---------- sensible balance  G(T_i) = gains into store air at store temperature T_i
    def gains(T_i, W_i, Q_LT_cond_in):
        _, s_LT, _, _ = case_load(LT, T_i, W_i)
        _, s_MT, _, _ = case_load(MT, T_i, W_i)
        return ((S["UA"] + m_out * CP) * (T_o - T_i) + q_int + Q_LT_cond_in
                - n_LT * s_LT - s_MT)

    W_i = np.full_like(T_o, W_RATED)
    T_i = np.full_like(T_o, S["T_cool"])
    Q_cond_in = np.zeros_like(T_o)
    for _ in range(30):                          # fixed-point iteration T <-> W <-> condenser heat
        G_hi = gains(S["T_cool"], W_i, Q_cond_in)
        G_lo = gains(S["T_heat"], W_i, Q_cond_in)
        cooling = G_hi > 0
        heating = G_lo < 0
        floating = ~cooling & ~heating
        # G is linear in T_i, so interpolate in the dead band
        T_float = S["T_heat"] + (S["T_cool"] - S["T_heat"]) * G_lo / np.where(G_lo - G_hi == 0, 1, G_lo - G_hi)
        T_new = np.where(cooling, S["T_cool"], np.where(heating, S["T_heat"], T_float))
        Q_cool_s = np.where(cooling, G_hi, 0.0)
        Q_heat_need = np.where(heating, -G_lo, 0.0)

        # ---------- moisture balance at T_new
        m_sup = Q_cool_s / (CP * (T_new - S["T_coil"]))
        num = m_out * W_o + g_lat + n_LT * LT["m_inf"] * LT["W"] + MT["m_inf"] * MT["W"]
        den = m_out + n_LT * LT["m_inf"] + MT["m_inf"]
        W_wet = (num + m_sup * S["W_coil"]) / (den + m_sup)
        W_dry = num / den
        W_new = np.where(W_wet > S["W_coil"], W_wet, np.minimum(W_dry, np.maximum(W_wet, S["W_coil"])))
        coil_ok = W_new > S["W_coil"]
        m_coil_water = np.where(coil_ok, m_sup * (W_new - S["W_coil"]), 0.0)
        extra_dehum = np.zeros_like(T_o)
        if rh_control:
            W_cap = W_from_RH(T_new, S["RH_cap"])
            over = W_new > W_cap
            # water the HVAC must additionally remove to hold W_cap (balance residual)
            extra_dehum = np.where(over, (num + m_sup * S["W_coil"] - (den + m_sup) * W_cap)
                                   , 0.0)
            extra_dehum = np.maximum(extra_dehum, 0.0)
            # coil water at W_cap
            m_coil_water = np.where(over, m_sup * np.maximum(W_cap - S["W_coil"], 0), m_coil_water)
            W_new = np.where(over, W_cap, W_new)

        # ---------- LT condenser heat
        Q_LT_tot, _, _, _ = case_load(LT, T_new, W_new)
        if config == "plugin":
            cop_LT = cop(LT, T_new + 12.0)        # in-store condenser ~ store + 12 K [ASSUMED]
            Q_cond_new = n_LT * Q_LT_tot * (1 + 1 / cop_LT)
        elif config == "reclaim":
            Tc = np.where(heating, np.maximum(Tc_rem_LT, 30.0), Tc_rem_LT)  # hold 30 C to make useful heat
            cop_LT = cop(LT, Tc)
            avail = 0.8 * n_LT * Q_LT_tot * (1 + 1 / cop_LT)
            Q_cond_new = np.where(heating, avail, 0.0)
        else:
            cop_LT = cop(LT, Tc_rem_LT)
            Q_cond_new = np.zeros_like(T_o)
        if config == "reclaim":
            # reclaim heat cannot exceed the heating need (excess dumped on the roof)
            need_without = -gains(S["T_heat"], W_new, 0.0)
            Q_cond_new = np.where(heating, np.minimum(Q_cond_new, np.maximum(need_without, 0)), 0.0)
        conv = np.max(np.abs(W_new - W_i)) < 1e-8 and np.max(np.abs(Q_cond_new - Q_cond_in)) < 1e-4
        W_i, T_i, Q_cond_in = W_new, T_new, Q_cond_new
        if conv:
            break

    G_hi = gains(S["T_cool"], W_i, Q_cond_in); G_lo = gains(S["T_heat"], W_i, Q_cond_in)
    Q_cool_s = np.where(T_i >= S["T_cool"] - 1e-9, np.maximum(G_hi, 0), 0.0)
    Q_heat = np.where(T_i <= S["T_heat"] + 1e-9, np.maximum(-G_lo, 0), 0.0)

    Q_LT_tot, s_LT, l_LT, p_LT = case_load(LT, T_i, W_i)
    Q_MT_tot, s_MT, l_MT, p_MT = case_load(MT, T_i, W_i)
    cop_MT = cop(MT, Tc_rem_MT)
    E_LT = n_LT * (Q_LT_tot / cop_LT + p_LT)          # kW electricity, freezer lineup
    E_MT = Q_MT_tot / cop_MT + p_MT
    Q_cool_lat = m_coil_water * H_FG
    E_AC = (Q_cool_s + Q_cool_lat) / S["COP_AC"] + extra_dehum * 3600 * S["kWh_per_kg_dehum"]
    gas = Q_heat / S["eta_heat"]
    E_light = q_int - S["p_sens"] * people

    out = pd.DataFrame(dict(time=wx["time"], T_o=T_o, RH_o=wx["RH_o"].values, W_o=W_o,
                            N=N, q_door=q_door, T_i=T_i, W_i=W_i, RH_i=RH_from_W(T_i, W_i),
                            Q_LT_case=Q_LT_tot, Q_LT_sens=s_LT, Q_LT_lat=l_LT,
                            cop_LT=cop_LT, E_LT=E_LT, E_MT=E_MT,
                            credit_LT=n_LT * (s_LT + l_LT), credit_LT_sens=n_LT * s_LT,
                            Q_cool_s=Q_cool_s, Q_cool_lat=Q_cool_lat, extra_dehum=extra_dehum,
                            E_AC=E_AC, Q_heat=Q_heat, gas=gas, Q_cond_in=Q_cond_in, E_light=E_light,
                            mode=np.where(Q_cool_s > 0, "cool", np.where(Q_heat > 0, "heat", "float"))))
    out["E_total_site"] = out.E_LT + out.E_MT + out.E_AC + out.E_light + out.gas
    return out


def annual(o):
    return dict(E_LT=o.E_LT.sum(), E_MT=o.E_MT.sum(), E_AC=o.E_AC.sum(), gas=o.gas.sum(),
                E_light=o.E_light.sum(), total=o.E_total_site.sum(),
                RH_mean=o.RH_i.mean(), hours_cool=(o["mode"] == "cool").sum(),
                hours_heat=(o["mode"] == "heat").sum())


if __name__ == "__main__":
    print(f"door power-law fit, no vestibule : Q[cfm] = {A_NV:.1f} * N^{B_NV:.3f}")
    print(f"door power-law fit, vestibule    : Q[cfm] = {A_V:.1f} * N^{B_V:.3f}")
    for N, q in PNNL_NO_VEST[[0, 3, 8, 12]]:
        print(f"   N={N:5.0f}/h  PNNL {q:6.0f} cfm   fit {A_NV*N**B_NV:6.0f} cfm")
    print(f"LT case: curtain air flow m_inf = {LT['m_inf']:.4f} kg/s per case; "
          f"{LT['per_kg_rated']:.1f} kJ per kg at rating point")
    print(f"MT lineup: m_inf = {MT['m_inf']:.3f} kg/s")
    print(f"W at 23.9C/55% = {W_RATED*1000:.2f} g/kg ; W_LT = {W_LT*1000:.3f} g/kg ; coil W = {STORE['W_coil']*1000:.2f} g/kg")
    print(f"COP_LT remote: Tc=21 -> {cop(LT,21):.2f}, Tc=35 -> {cop(LT,35):.2f}, Tc=45 -> {cop(LT,45):.2f}")
    # elasticity checks at the rating point
    base = case_load(LT, 23.9, W_RATED)[0]
    dRH = (case_load(LT, 23.9, float(W_from_RH(23.9, 56)))[0] - base) / base * 100
    dT = (case_load(LT, 24.9, W_RATED)[0] - base) / base * 100
    lat_base = case_load(LT, 23.9, W_RATED)[2]
    dlat = (case_load(LT, 23.9, float(W_from_RH(23.9, 56)))[2] - lat_base) / lat_base * 100
    print(f"LT case load: +1 %RH -> {dRH:+.2f} % of total ; latent part {dlat:+.2f} % of latent ;"
          f" +1 K (same W) -> {dT:+.2f} %; LHR = {lat_base/base:.3f}")
    Tc = LT["T"]
    em = 2.6520E-2 + 1.0780E-3 * Tc - 6.0256E-5 * Tc**2 + 1.2373E-6 * Tc**3
    eh = 2.0376E-2 + 2.4378E-4 * Tc + 1.1400E-5 * Tc**2 + 1.8110E-7 * Tc**3
    print(f"EnergyPlus case-temperature method slope at {Tc} C: horizontal {eh*100:.2f} %/RH, "
          f"vertical {em*100:.2f} %/RH of latent load")
