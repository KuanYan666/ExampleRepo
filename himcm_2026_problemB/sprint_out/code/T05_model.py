"""T05 - transparent daily energy balance of a 2.5 m open vertical LOW-temperature
(frozen food) multideck case.

Every function is vectorised: pass floats or numpy arrays.
Units: T in degC, power in kW, energy in kWh/day, mass flow in kg/s.

Baseline hardware = Hussmann Excel F6 open multi-deck frozen food case,
technical data sheet P/N 0522419_H (Oct 2017), 8-ft model (2.448 m), scaled to 2.5 m.
"""
import numpy as np

SIGMA = 5.670374419e-8          # W/m2K4, Stefan-Boltzmann (CODATA)
P_ATM = 101325.0                # Pa
CP_AIR = 1.006                  # kJ/kg K, dry air (ASHRAE Fundamentals ch.1)
H_SG = 2834.0                   # kJ/kg, latent heat of sublimation of ice near 0 C (2501 + 333)
C_FROZEN = 1.9                  # kJ/kg K, frozen food specific heat [ASSUMED, typical 1.7-2.1]
L_CASE = 2.5                    # m
FT8 = 96.375 * 0.0254           # 2.448 m: F6 8-ft case length (data sheet p.2)
SCALE = L_CASE / FT8            # scale 8-ft data-sheet watts to 2.5 m
TDA = 1.14 * L_CASE             # m2, AHRI total display area, F6: 1.14 m2/m (p.5)
V_USE = 0.72 * L_CASE           # m3, usable cube, F6: 0.72 m3/m (p.5)


def p_ws_water(T):
    """Saturation vapour pressure over liquid water, Pa (ASHRAE Fundamentals 2017 ch.1 eq.6)."""
    Tk = np.asarray(T) + 273.15
    c = (-5.8002206e3, 1.3914993, -4.8640239e-2, 4.1764768e-5, -1.4452093e-8, 6.5459673)
    return np.exp(c[0] / Tk + c[1] + c[2] * Tk + c[3] * Tk**2 + c[4] * Tk**3 + c[5] * np.log(Tk))


def p_ws_ice(T):
    """Saturation vapour pressure over ICE, Pa (ASHRAE Fundamentals 2017 ch.1 eq.5).
    Check: -20 C -> 103.26 Pa (ASHRAE table 3: 103.24 Pa)."""
    Tk = np.asarray(T) + 273.15
    C = (-5.6745359e3, 6.3925247, -9.677843e-3, 6.2215701e-7, 2.0747825e-9, -9.484024e-13, 4.1635019)
    return np.exp(C[0] / Tk + C[1] + C[2] * Tk + C[3] * Tk**2 + C[4] * Tk**3 + C[5] * Tk**4 + C[6] * np.log(Tk))


def W(pw):
    return 0.621945 * pw / (P_ATM - pw)


# ----------------------------------------------------------------------------- baseline
# Frost collected on the coil = defrost water. F6: 8.2 lb/ft/day (+-15%), p.3.
FROST_BASE = 8.2 * 0.45359 * 8 * SCALE          # kg/day for 2.5 m  (~30.4 kg/day)
T0, RH0, TDA0 = 24.0, 55.0, -22.0
DW0 = W(RH0 / 100 * p_ws_water(T0)) - W(p_ws_ice(TDA0))
M_INF0 = FROST_BASE / 86400 / DW0                 # kg/s of store air that ends up in the case

# name: (baseline, low, high, aspect group, unit, source tag)
PARAMS = {
    "T_store":  (24.0, 21.0, 26.0, "Store climate", "C", "ASHRAE 72 test 75.2 F [V]; range [A]"),
    "RH_store": (55.0, 35.0, 60.0, "Store climate", "%", "ASHRAE 72 55% [V]; 35-55 tested by Faramarzi 2000 [V]; 60 [A]"),
    "r_inf":    (1.0, 0.7, 1.5, "Air curtain", "x", "range reproduces 67-81% infiltration share [derived]"),
    "T_DA":     (-22.0, -25.0, -18.0, "Case temperature", "C", "F6 -8 F [V]; F6* -3 F [V]; -25 [A]"),
    "dT_coil":  (4.4, 3.0, 8.0, "Refrigeration machine", "K", "F6 -8 F air / -16 F evap [V]; 8 K frosted coil [A]"),
    "T_cond":   (35.0, 25.0, 45.0, "Refrigeration machine", "C", "ASHRAE 72 SCT 95 F [V]; 25-45 [A]"),
    "eta_II":   (0.45, 0.35, 0.55, "Refrigeration machine", "-", "AHRI 1200 EER implies ~0.51 [derived]; range [A]"),
    "UA":       (6.25, 4.0, 10.0, "Insulation (conduction)", "W/K", "50 mm PU foam, ~6 m2/m [A]"),
    "epsF":     (0.5, 0.3, 0.8, "Radiation", "-", "emissivity x view factor [A]"),
    "P_light":  (0.0394, 0.0394, 0.181, "Lights", "kW", "F6 LED 38.6 W to T8 177 W per 8 ft [V]"),
    "h_light":  (24.0, 12.0, 24.0, "Lights", "h/day", "DOE/AHRI test 24 h [V]; 12 h night-off [A]"),
    "f_light":  (0.75, 0.5, 1.0, "Lights", "-", "share of lamp heat entering case [A]"),
    "P_fan":    (0.0735, 0.04, 0.15, "Evaporator fans", "kW", "F6 4x12 W ECM-type = 72 W per 8 ft [V]; 150 W old motors [A]"),
    "P_ambfan": (0.0092, 0.005, 0.02, "Evaporator fans", "kW", "F6 ambient curtain fans 9 W per 8 ft [V]; range [A]"),
    "P_ash":    (0.388, 0.25, 0.45, "Anti-sweat heaters", "kW", "F6 180 + 200 W per 8 ft, constant on [V]; range [A]"),
    "duty_ash": (1.0, 0.3, 1.0, "Anti-sweat heaters", "-", "F6 'constant on' [V]; 0.3 with humidity control [A]"),
    "f_ash":    (0.45, 0.2, 0.7, "Anti-sweat heaters", "-", "share of heater heat entering case [A]"),
    "P_def":    (3.40, 1.40, 3.40, "Defrost", "kW", "F6 U-heater 1370 W / total 3330 W per 8 ft [V]"),
    "n_def":    (2.0, 1.0, 4.0, "Defrost", "1/day", "F6 every 12 h [V]; 1-4 [A]"),
    "t_def":    (25.0, 15.0, 30.0, "Defrost", "min", "F6 failsafe 30 min [V]; 15-25 [A]"),
    "f_def":    (0.5, 0.3, 0.8, "Defrost", "-", "share of heater energy re-removed by compressor [A]"),
    "m_restock": (100.0, 30.0, 300.0, "Product loading", "kg/day", "[A]"),
    "dT_arr":   (5.0, 2.0, 15.0, "Product loading", "K", "product arrives warmer than case [A]"),
    "kappa":    (0.0, -0.33, 0.33, "Store HVAC interaction", "kWh_e/kWh_th", "AC COP ~3 credit / heat-pump COP ~3 penalty [A]"),
    "rho_load": (250.0, 150.0, 400.0, "Product stocked (service)", "kg/m3", "kg product per m3 usable cube [A]"),
}
BASE = {k: v[0] for k, v in PARAMS.items()}


def case_model(p, frost_coupling=True):
    """Return dict of loads (kW) and daily energies (kWh/day). p: dict of floats/arrays."""
    g = lambda k: np.asarray(p.get(k, BASE[k]), dtype=float)
    Ts, RH, Tda = g("T_store"), g("RH_store"), g("T_DA")

    # --- infiltration: store air that is entrained by the air curtain and cooled/dried to T_DA
    m_inf = M_INF0 * g("r_inf")
    dW = np.maximum(W(RH / 100 * p_ws_water(Ts)) - W(p_ws_ice(Tda)), 0.0)
    Q_inf_s = m_inf * CP_AIR * (Ts - Tda)                    # kW
    Q_inf_l = m_inf * dW * H_SG                               # kW
    frost = m_inf * dW * 86400                                # kg/day of frost

    # --- conduction and radiation
    Q_cond = g("UA") * (Ts - Tda) / 1000
    T_prod = Tda + 4.0          # product surface ~0 F when air is -8 F (AHRI 1200 LT rating 0 F) [A]
    Q_rad = g("epsF") * SIGMA * TDA * ((Ts + 273.15)**4 - (T_prod + 273.15)**4) / 1000

    # --- defrost: duration grows with frost (Faramarzi 2000: -74% latent -> -40% duration)
    t_def = g("t_def")
    if frost_coupling:
        t_def = np.minimum(t_def * (0.46 + 0.54 * frost / FROST_BASE), 30.0)
    h_def = g("n_def") * t_def / 60.0                         # h/day heaters on
    E_def = g("P_def") * h_def                                # kWh/day electricity

    # --- internal electrical loads (kWh/day of electricity)
    E_light = g("P_light") * g("h_light")
    E_fan = (g("P_fan") + g("P_ambfan")) * 24
    E_ash = g("P_ash") * g("duty_ash") * 24
    E_prod_th = g("m_restock") * C_FROZEN * g("dT_arr") / 3600   # kWh_th/day

    # --- thermal energy the refrigeration machine must remove per day (kWh_th/day)
    parts_th = {
        "Infiltration - sensible": Q_inf_s * 24,
        "Infiltration - latent (frost)": Q_inf_l * 24,
        "Conduction": Q_cond * 24,
        "Radiation": Q_rad * 24,
        "Lights (heat inside case)": g("f_light") * E_light,
        "Evaporator fans": g("P_fan") * 24,
        "Anti-sweat (heat inside case)": g("f_ash") * E_ash,
        "Defrost heat re-removed": g("f_def") * E_def,
        "Product loading": E_prod_th,
    }
    E_th = sum(parts_th.values())

    # --- machine: COP = eta_II * Carnot COP between evaporator and condenser
    Tev = Tda - g("dT_coil") + 273.15
    Tcd = g("T_cond") + 273.15
    COP = g("eta_II") * Tev / (Tcd - Tev)
    E_comp = E_th / COP

    # --- optional store HVAC interaction: net cold the case dumps into the store
    Q_store_cold = (Q_inf_s + Q_inf_l + Q_cond + Q_rad) * 24 \
        - (1 - g("f_light")) * E_light - (1 - g("f_ash")) * E_ash - g("P_ambfan") * 24
    E_hvac = g("kappa") * Q_store_cold

    E_case = E_comp + E_light + E_fan + E_ash + E_def          # case boundary (DOE-like)
    M_prod = V_USE * g("rho_load")
    return dict(parts_th=parts_th, E_th=E_th, Q_avg=E_th / 24, COP=COP, E_comp=E_comp,
                E_light=E_light, E_fan=E_fan, E_ash=E_ash, E_def=E_def, E_hvac=E_hvac,
                E_case=E_case, E_store=E_case + E_hvac, frost=frost, t_def=t_def,
                M_prod=M_prod, m_inf=m_inf, dW=dW,
                y_day=E_case, y_kg=E_case / M_prod, y_tda=E_case / TDA)


if __name__ == "__main__":
    r = case_model(BASE)
    print(f"case length {L_CASE} m, TDA {TDA:.2f} m2 ({TDA/0.0929:.1f} ft2), usable cube {V_USE:.2f} m3")
    print(f"infiltrating air M_INF0 = {M_INF0:.4f} kg/s  (= {M_INF0/1.2*1000:.0f} L/s), dW = {DW0*1000:.2f} g/kg")
    print(f"frost {r['frost']:.1f} kg/day (F6 sheet: {FROST_BASE:.1f})")
    print("thermal load breakdown (average kW and share):")
    for k, v in r["parts_th"].items():
        print(f"   {k:<32}{v/24:6.3f} kW  {100*v/r['E_th']:5.1f}%")
    print(f"   {'TOTAL':<32}{r['Q_avg']:6.3f} kW   (F6 rating 1490 Btu/h/ft -> {1490*8*SCALE/3412.14:.2f} kW)")
    sens = 24 * case_model(BASE)["parts_th"]["Infiltration - sensible"] / 24
    print(f"COP {r['COP']:.2f}; Carnot {r['COP']/BASE['eta_II']:.2f}")
    for k in ("E_comp", "E_light", "E_fan", "E_ash", "E_def", "E_case"):
        print(f"   {k:<8}{r[k]:6.1f} kWh/day  {100*r[k]/r['E_case']:5.1f}%")
    print(f"per m2 TDA {r['y_tda']:.1f} kWh/m2/day; per kg product {r['y_kg']*1000:.1f} Wh/kg/day; M = {r['M_prod']:.0f} kg")
    TDAft = TDA / 0.09290304
    print(f"DOE 2017 VOP.RC.L limit 2.2*TDA+6.85 = {2.2*TDAft+6.85:.1f} kWh/day")
    # AHRI-1200-style CDEC: EER 6.98 at -19 F adjusted dew point (Table 1)
    cec = r["Q_avg"] * 3412.14 * (24 - r["t_def"] * BASE["n_def"] / 60) / (6.98 * 1000)
    print(f"AHRI-style CDEC = CEC {cec:.1f} + direct {r['E_light']+r['E_fan']+r['E_ash']+r['E_def']:.1f} = "
          f"{cec + r['E_light']+r['E_fan']+r['E_ash']+r['E_def']:.1f} kWh/day")
    print(f"store HVAC cold dumped {(r['E_hvac'] if BASE['kappa'] else 0):.1f}; Q_store_cold per day:",
          f"{case_model({**BASE,'kappa':1})['E_hvac']:.1f} kWh_th/day")
    # infiltration share vs r_inf
    for ri in (0.7, 1.0, 1.5, 2.0):
        q = case_model({**BASE, "r_inf": ri})
        s = (q["parts_th"]["Infiltration - sensible"] + q["parts_th"]["Infiltration - latent (frost)"]) / q["E_th"]
        print(f"r_inf {ri}: infiltration share {100*s:.0f}%, latent share of infiltration "
              f"{100*q['parts_th']['Infiltration - latent (frost)']/(q['parts_th']['Infiltration - sensible']+q['parts_th']['Infiltration - latent (frost)']):.0f}%")
    # RH 55 -> 35 check vs Faramarzi 2000 (MT dairy: latent -74%, total load -20.8%, defrost -40%)
    a, b = case_model(BASE), case_model({**BASE, "RH_store": 35})
    print(f"RH 55->35: latent {100*(b['parts_th']['Infiltration - latent (frost)']/a['parts_th']['Infiltration - latent (frost)']-1):.0f}%,"
          f" total load {100*(b['E_th']/a['E_th']-1):.1f}%, defrost time {100*(b['t_def']/a['t_def']-1):.0f}%,"
          f" case energy {100*(b['E_case']/a['E_case']-1):.1f}%")
