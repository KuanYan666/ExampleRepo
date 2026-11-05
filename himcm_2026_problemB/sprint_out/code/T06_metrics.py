"""
T06 - Stress-testing candidate definitions of "cooling efficiency" for an open freezer case.

One small daily energy-balance model of a 2.5 m open vertical low-temperature case is run
through a set of limiting-case scenarios.  Every candidate metric is computed in every
scenario, and we check whether it moves in the direction common sense demands.

Run:  python3 T06_metrics.py         (prints all tables; writes T06_results.csv)
Units: kW, kWh/day, degC, kg, h.
Every number is tagged in the memo (T06_metric_design.md) as VERIFIED or ASSUMED.
"""
import sys, os, math
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "himcm_b"))
import core as C  # psychrometrics (ASHRAE Hyland-Wexler)

# ------------------------------------------------------------------ constants
CP_AIR = 1.006           # kJ/(kg K) dry air
H_SUB = 2501.0 + 334.0   # kJ/kg: vapour -> liquid -> ice (water arrives as vapour, leaves as frost)
T_CASE = -18.0           # degC case air / product set point  [team baseline]
RH_CASE = 90.0           # % inside case [team baseline]
T_SAFE = -15.0           # degC: EU Dir. 89/108/EEC Art 5(2)(a): -18 C with <=3 C tolerance in retail cabinets

# ------------------------------------------------------------------ baseline case (team numbers)
BASE = dict(
    Q_total=2.5,          # kW total refrigeration load at 24 C / 55 % RH  [team; probably LOW, see memo]
    inf_share=0.75,       # infiltration share of load [team; lit. 67-85 %]
    cond_share=0.06, rad_share=0.06,
    P_fan=0.10, P_light=0.10, P_asw=0.05, P_defrost=0.075,   # kW electrical, all ends up as heat in case [ASSUMED split of team's 13 %]
    COP=1.7,              # machine COP at baseline [team]
    T_store=24.0, RH_store=55.0,
    T_cond=35.0,          # condensing temperature, degC [team]
    dT_coil=10.0,         # air-to-refrigerant temperature difference at baseline [ASSUMED, cf. Hill Phoenix O2MZD: -17 F evap vs -5 F discharge air = 6.7 K]
    M_product=300.0,      # kg product on display [ASSUMED]
    TDA=3.0,              # m2 total display area = 2.5 m x 1.2 m projected height [ASSUMED]
)

KWH_PER_DAY = 24.0


def infil_dh(T_store, RH_store):
    """Enthalpy carried in per kg of store air that ends up at case conditions (kJ/kg dry air)."""
    W_s = C.W_from_RH(T_store, RH_store)
    W_c = C.W_from_RH(T_CASE, RH_CASE)
    sens = CP_AIR * (T_store - T_CASE)
    lat = max(W_s - W_c, 0.0) * H_SUB
    return sens, lat


# calibrate fixed parameters from the baseline
_s0, _l0 = infil_dh(BASE["T_store"], BASE["RH_store"])
M_INF0 = BASE["Q_total"] * BASE["inf_share"] / (_s0 + _l0)          # kg/s of store air "consumed"
UA_COND = BASE["Q_total"] * BASE["cond_share"] / (BASE["T_store"] - T_CASE)   # kW/K walls
UA_COIL = BASE["Q_total"] / BASE["dT_coil"]                          # kW/K evaporator coil
T_EVAP0 = T_CASE - BASE["dT_coil"]
CARNOT_REFRIG0 = (T_EVAP0 + 273.15) / (BASE["T_cond"] - T_EVAP0)
ETA_MACHINE = BASE["COP"] / CARNOT_REFRIG0                           # machine 2nd-law quality, held fixed
LAT0 = M_INF0 * _l0


def rad_load(T_store, base_share=BASE["rad_share"]):
    """Radiation from store surfaces to the cold product, scaled with T^4 difference."""
    k = BASE["Q_total"] * base_share / ((BASE["T_store"] + 273.15) ** 4 - (T_CASE + 273.15) ** 4)
    return k * ((T_store + 273.15) ** 4 - (T_CASE + 273.15) ** 4)


def run(name, T_store=24.0, RH_store=55.0, T_cond=35.0, inf_mult=1.0, rad_mult=1.0,
        fan_mult=1.0, extra_heat=0.0, extra_aux=0.0, product_kg=None, on=True,
        night_cover_inf_cut=0.0, night_hours=0.0, doors=False, condenser="remote", _big_coil=False):
    """Daily-average energy balance of the case. Returns a dict of physical results."""
    M = BASE["M_product"] if product_kg is None else product_kg
    sens, lat = infil_dh(T_store, RH_store)

    # ---- air-curtain fan: affinity law P ~ (flow)^3; infiltration is U-shaped in curtain flow
    P_fan = BASE["P_fan"] * fan_mult ** 3
    v = fan_mult
    curtain = 1 + (4.0 * (1 - v) ** 2 if v < 1 else 1.2 * (v - 1) ** 2)   # [ASSUMED shape, see memo]
    m_inf = M_INF0 * inf_mult * curtain
    if doors:
        m_inf *= 0.20                       # doors cut infiltration 80 % [team assumption]
    # night cover: infiltration cut for night_hours of 24
    m_inf_day = m_inf * (1 - night_cover_inf_cut * night_hours / 24.0)

    Q_inf_sens = m_inf_day * sens
    Q_inf_lat = m_inf_day * lat
    Q_inf = Q_inf_sens + Q_inf_lat
    Q_cond = UA_COND * (T_store - T_CASE) * (1.15 if doors else 1.0)     # door frames conduct more [ASSUMED]
    Q_rad = rad_load(T_store) * rad_mult * (0.6 if doors else 1.0)       # glass blocks some IR [ASSUMED]
    P_defrost = BASE["P_defrost"] * (Q_inf_lat / LAT0 if LAT0 > 0 else 1.0)  # defrost scales with frost
    P_asw = BASE["P_asw"] + (0.15 if doors else 0.0)                      # door anti-sweat heaters [ASSUMED]
    P_aux = P_fan + BASE["P_light"] + P_asw + P_defrost + extra_aux
    Q_tot = Q_inf + Q_cond + Q_rad + P_aux + extra_heat                   # all aux electricity becomes case heat

    # ---- machine: evaporator temperature sags when load rises (fixed coil UA)
    # (_big_coil: a coil so large the evaporator never sags - isolates the pure "COP rewards load" effect)
    T_evap = T_EVAP0 if _big_coil else T_CASE - Q_tot / UA_COIL
    cop_refrig_carnot = (T_evap + 273.15) / (T_cond - T_evap)
    COP = ETA_MACHINE * cop_refrig_carnot

    if not on:
        E_comp = 0.0; P_aux_on = 0.0; Q_removed = 0.0
    else:
        E_comp = Q_tot / COP * KWH_PER_DAY
        P_aux_on = P_aux
        Q_removed = Q_tot * KWH_PER_DAY
    E = E_comp + P_aux_on * KWH_PER_DAY

    # ---- service: kg of product x hours inside the safe band (<= -15 C)
    if on:
        hours_safe = 24.0
    else:
        # switched off: heat leak (without aux) warms product lumped mass; c_frozen ~2.0 kJ/kgK [ASSUMED]
        q_leak = Q_inf + Q_cond + Q_rad
        hours_safe = min(24.0, M * 2.0 * (T_SAFE - T_CASE) / max(q_leak, 1e-9) / 3600.0) if M > 0 else 0.0
    S = M * hours_safe                                                    # kg h / day

    # ---- store side (system boundary).  Remote condenser: store LOSES the heat that came from it.
    from_store = (Q_inf + Q_cond + Q_rad) * KWH_PER_DAY if on else 0.0    # kWh/day of heat pulled out of the store
    if condenser == "remote":
        store_net = -from_store                                          # negative = case cools the store
    else:  # integral / self-contained: condenser in the store
        store_net = E                                                    # net heat into the store = electricity

    # reservoir-based Carnot (product -18 C, heat sink = condenser air ~10 K below T_cond [ASSUMED])
    T_sink = T_cond - 10.0
    carnot_res = (T_CASE + 273.15) / (T_sink - T_CASE)

    return dict(scenario=name, T_store=T_store, RH_store=RH_store, T_cond=T_cond,
                Q_tot=Q_tot, Q_inf=Q_inf, Q_inf_lat=Q_inf_lat, P_aux=P_aux, T_evap=T_evap,
                COP=COP if on else float("nan"), E=E, S=S, hours_safe=hours_safe, M=M,
                carnot_res=carnot_res, carnot_refrig=cop_refrig_carnot, store_net=store_net,
                doors=doors, on=on, m_inf=m_inf_day)


# ------------------------------------------------------------------ the candidate metrics
PRICE = 0.1337         # $/kWh  EIA Electric Power Monthly Table 5.3, commercial 2025 [VERIFIED]
GRID = 775.218 * 0.453592 / 1000   # kg CO2e/kWh  eGRID2023 US total output rate rev1 [VERIFIED]
GWP_404A = 3922        # AR4 [VERIFIED]
LEAK = 0.20            # per year, EPA GreenChill ">20 %" [VERIFIED as lower bound]
CHARGE_KG_PER_KW = 1.75 * 0.453592 / 0.29307   # EPA GreenChill advanced target 1.75 lb/MBH -> kg/kW [VERIFIED target]
VALUE_KG = 6.0         # $/kg retail value of frozen product [ASSUMED]
DOE_OPEN = lambda tda_m2: 2.2 * tda_m2 * 10.7639 + 6.85     # VOP.RC.L, 10 CFR 431.66(e) [VERIFIED]
DOE_DOOR = lambda tda_m2: 0.49 * tda_m2 * 10.7639 + 2.61    # VCT.RC.L [VERIFIED]
EU_SAE = lambda tda_m2: (7.5 + 19.3 * tda_m2) * 1.0 * 1.0   # kWh/day, vertical supermarket freezer, L1 [VERIFIED]


def metrics(r, ref):
    """ref = the same case with doors under the same conditions (benchmark #7)."""
    E, S, Q = r["E"], r["S"], r["Q_tot"]
    on = r["on"]
    m = {}
    m["1 Energy/day (kWh/d)"] = E
    m["2a COP machine"] = r["COP"]
    m["2b Heat removed per kWh (system COP)"] = (Q * 24 / E) if (on and E > 0) else float("nan")
    m["3 2nd-law eff. (system COP / Carnot)"] = ((Q * 24 / E) / r["carnot_res"]) if (on and E > 0) else float("nan")
    m["4 kWh/d per m2 TDA"] = E / BASE["TDA"]
    m["5 Service kg.h per kWh"] = (S / E) if E > 0 else (float("inf") if S > 0 else float("nan"))
    m["6 Capture phi = 1 - Q_inf/Q_tot"] = (1 - r["Q_inf"] / Q) if on else float("nan")
    m["7 Benchmark E_doors/E"] = (ref["E"] / E) if E > 0 else float("inf")
    co2 = E * GRID + Q * CHARGE_KG_PER_KW * 2 * LEAK * GWP_404A / 365.0   # x2: conventional ~2x advanced [ASSUMED]
    m["10a CO2e kg/day"] = co2
    m["10b Cost $/day (electricity)"] = E * PRICE
    lost = 0.0 if r["hours_safe"] >= 24 else r["M"] * VALUE_KG
    m["9 Net benefit $/day (vs. losing the stock)"] = -lost - E * PRICE   # value of a working day is 0 loss
    return m


SCEN = [
    ("Baseline (24 C/55 %, summer)", {}),
    ("Switched off", dict(on=False)),
    ("Empty case", dict(product_kg=0.0)),
    ("Doors fitted", dict(doors=True)),
    ("Night cover 12 h", dict(night_cover_inf_cut=0.43, night_hours=12)),
    ("Winter store (21 C/30 %, Tcond 25 C)", dict(T_store=21.0, RH_store=30.0, T_cond=25.0)),
    ("Very humid store (24 C/75 %)", dict(RH_store=75.0)),
    ("Air-curtain fan +50 % flow", dict(fan_mult=1.5)),
    ("Extra 0.3 kW lights inside", dict(extra_aux=0.3)),
    ("Aisle draft: infiltration x1.3", dict(inf_mult=1.3)),
    ("Draft x1.3, oversized coil", dict(inf_mult=1.3, _big_coil=True)),
]


def table():
    rows, phys = [], []
    for name, kw in SCEN:
        r = run(name, **kw)
        kw_ref = dict(kw); kw_ref["doors"] = True
        kw_ref.pop("night_cover_inf_cut", None); kw_ref.pop("night_hours", None)
        kw_ref["on"] = True; kw_ref.pop("product_kg", None)
        ref = run("ref", **kw_ref)
        m = metrics(r, ref)
        m["scenario"] = name
        rows.append(m); phys.append(r)
    return pd.DataFrame(rows).set_index("scenario"), pd.DataFrame(phys).set_index("scenario")


def mt_validation():
    """Validate the infiltration-humidity model against Faramarzi et al. 2000 (ACEEE p.3.132):
    open vertical MT dairy/meat cases: RH 55 -> 35 % at 75 F cut TOTAL cooling load 20.7-20.8 %.
    Our model of an MT case: case air +2 C / 90 % RH, infiltration 80 % of load (their Fig. 2)."""
    Ts = (75 - 32) / 1.8
    Tc = 2.0
    def dh(RH):
        Ws, Wc = C.W_from_RH(Ts, RH), C.W_from_RH(Tc, 90.0)
        return CP_AIR * (Ts - Tc) + max(Ws - Wc, 0) * 2501.0
    share = 0.80
    new = (1 - share) + share * dh(35) / dh(55)
    return 1 - new


if __name__ == "__main__":
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print("=" * 100)
    print("CALIBRATION")
    print(f"  per kg store air: sensible {_s0:.1f} kJ, latent {_l0:.1f} kJ -> latent share {_l0/(_s0+_l0):.0%}")
    print(f"  infiltration mass flow {M_INF0*1000:.1f} g/s ({M_INF0/1.2*1000:.0f} L/s)")
    print(f"  baseline T_evap {T_EVAP0:.0f} C; Carnot(refrigerant {T_EVAP0:.0f}->{BASE['T_cond']:.0f} C) = {CARNOT_REFRIG0:.2f}"
          f" -> machine 2nd-law quality {ETA_MACHINE:.2f}")
    for lab, tc, th in [("team: -18 -> 35 C", -18, 35), ("refrigerant: -28 -> 35 C", -28, 35),
                        ("reservoirs: product -18 -> outdoor 25 C", -18, 25),
                        ("reservoirs: product -18 -> store 24 C", -18, 24),
                        ("reservoirs: product -18 -> winter outdoor 0 C", -18, 0)]:
        print(f"  Carnot COP {lab:45s} = {(tc+273.15)/(th-tc):.2f}")
    print(f"  Eurovent REC implied COP at T0=-28 C, Tc=35 C: {0.34*(245.15)/(35+28):.2f};"
          f" AHRI 1200-2023 Table 1 EER at -20 F = 6.88 Btu/Wh -> COP {6.88/3.412:.2f}")
    print(f"  MT validation: model predicts RH 55->35 % cuts total load by {mt_validation():.1%}"
          f" (Faramarzi et al. 2000 measured 20.7-20.8 %)")

    M, P = table()
    print("\n" + "=" * 100); print("PHYSICS PER SCENARIO")
    print(P[["Q_tot", "Q_inf", "Q_inf_lat", "P_aux", "T_evap", "COP", "E", "hours_safe", "S", "store_net"]].round(3))
    print("\n" + "=" * 100); print("METRICS PER SCENARIO")
    print(M.round(3).T)
    base = P.loc["Baseline (24 C/55 %, summer)"]
    print("\n  DOE cap (VOP.RC.L) at TDA 3.0 m2:", round(DOE_OPEN(3.0), 1), "kWh/d;",
          "doored cap (VCT.RC.L):", round(DOE_DOOR(3.0), 1), "kWh/d; ratio", round(DOE_OPEN(3.0) / DOE_DOOR(3.0), 2))
    print("  EU SAE (vertical freezer L1) at TDA 3.0 m2:", round(EU_SAE(3.0), 1), "kWh/d -> baseline EEI",
          f"{base['E']/EU_SAE(3.0):.0%}")
    print(f"  baseline E = {base['E']:.1f} kWh/d = {base['E']/DOE_OPEN(3.0):.0%} of DOE cap")
    print(f"  store heat balance (remote condenser): case pulls {-base['store_net']:.1f} kWh/d of heat OUT of the store")
    # refrigerant vs electricity CO2e
    e_co2 = base["E"] * GRID * 365 / 1000
    ref_lo = base["Q_tot"] * CHARGE_KG_PER_KW * LEAK * GWP_404A / 1000
    print(f"  annual CO2e: electricity {e_co2:.1f} t; R-404A leakage {ref_lo:.1f} t (advanced charge) to {2*ref_lo:.1f} t (conventional ~2x)")
    print(f"  charge allocated to case: {base['Q_tot']*CHARGE_KG_PER_KW:.1f} kg (advanced) / {2*base['Q_tot']*CHARGE_KG_PER_KW:.1f} kg (conv.)")

    M.to_csv(os.path.join(HERE, "T06_results.csv"))
    P.to_csv(os.path.join(HERE, "T06_physics.csv"))
