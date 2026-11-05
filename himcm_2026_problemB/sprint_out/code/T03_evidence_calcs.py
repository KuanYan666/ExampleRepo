"""T03 evidence-table helper calculations (HiMCM 2026 Problem B).

Every input number below is copied from a source named in the comment.
Outputs: printed tables + figs/T03_cop_conventions.png + figs/T03_rh_sensitivity.png

Run:  python3 T03_evidence_calcs.py
"""
import math
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "figs")
os.makedirs(FIG, exist_ok=True)
P = 101325.0  # Pa, sea-level pressure [ASSUMED: test rooms near sea level]


# ---------------------------------------------------------------- psychrometrics
def p_ws_water(T):
    """Saturation pressure over liquid water, Pa (Hyland-Wexler, ASHRAE Fundamentals ch.1 eq.6)."""
    Tk = T + 273.15
    C = [-5.8002206e3, 1.3914993, -4.8640239e-2, 4.1764768e-5, -1.4452093e-8, 6.5459673]
    return math.exp(C[0] / Tk + C[1] + C[2] * Tk + C[3] * Tk**2 + C[4] * Tk**3 + C[5] * math.log(Tk))


def p_ws_ice(T):
    """Saturation pressure over ice, Pa (Hyland-Wexler, ASHRAE Fundamentals ch.1 eq.5)."""
    Tk = T + 273.15
    C = [-5.6745359e3, 6.3925247, -9.677843e-3, 6.2215701e-7, 2.0747825e-9, -9.484024e-13, 4.1635019]
    return math.exp(C[0] / Tk + C[1] + C[2] * Tk + C[3] * Tk**2 + C[4] * Tk**3 + C[5] * Tk**4
                    + C[6] * math.log(Tk))


def W_from_RH(T, RH):
    pw = RH * (p_ws_water(T) if T >= 0 else p_ws_ice(T))
    return 0.621945 * pw / (P - pw)


def W_from_wetbulb(T, Twb):
    """ASHRAE Fundamentals ch.1 eq.33 (Twb > 0 C)."""
    Ws = W_from_RH(Twb, 1.0)
    return ((2501 - 2.326 * Twb) * Ws - 1.006 * (T - Twb)) / (2501 + 1.86 * T - 4.186 * Twb)


def h_air(T, W):
    """Moist-air enthalpy, kJ per kg dry air."""
    return 1.006 * T + W * (2501 + 1.86 * T)


def infiltration_split(T_amb, W_amb, T_case):
    """Heat removed when 1 kg (dry) of store air is cooled to T_case, saturated, water leaving as ice
    (T_case<0) or liquid (T_case>=0).  Returns sensible, latent, total in kJ/kg_da."""
    W_case = W_from_RH(T_case, 1.0)
    dW = max(W_amb - W_case, 0.0)
    h_cond = (-333.4 + 2.09 * T_case) if T_case < 0 else 4.186 * T_case   # ice or water enthalpy, kJ/kg
    total = h_air(T_amb, W_amb) - h_air(T_case, W_case) - dW * h_cond
    sensible = (1.006 + 1.86 * W_case) * (T_amb - T_case)
    return sensible, total - sensible, total


print("=" * 78)
print("1) Store test conditions used by the standards, and what 1 kg of infiltrated air costs")
print("=" * 78)
conds = {
    "ASHRAE 72 / DOE (24.0 C db, 18.0 C wb)": (24.0, W_from_wetbulb(24.0, 18.0)),
    "ISO 23953 class 0 (20 C, 50 %)":          (20.0, W_from_RH(20.0, 0.50)),
    "ISO 23953 class 3 = EU Set 1 (25 C, 60 %)": (25.0, W_from_RH(25.0, 0.60)),
    "EU Set 2 (30 C, 55 %) ice-cream freezers": (30.0, W_from_RH(30.0, 0.55)),
    "Team's store (24 C, 55 %)":                (24.0, W_from_RH(24.0, 0.55)),
}
rows = []
for name, (T, W) in conds.items():
    RH = W * P / (0.621945 + W) / p_ws_water(T)
    sF, lF, tF = infiltration_split(T, W, -18.0)   # freezer case air
    sM, lM, tM = infiltration_split(T, W, 2.0)     # chilled case air (example)
    rows.append((name, T, RH, W * 1000, sF, lF, tF, lF / tF, tM, lM / tM))
    print(f"{name:44s} RH={RH*100:4.1f}%  W={W*1000:5.2f} g/kg | to -18C: sens {sF:5.1f} lat {lF:5.1f} "
          f"tot {tF:5.1f} kJ/kg (latent {lF/tF*100:4.1f}%) | to +2C: tot {tM:5.1f} (latent {lM/tM*100:4.1f}%)")
base = rows[0][6]
print(f"Freezer load per kg infiltrated air, ISO class 3 vs ASHRAE 72: {rows[2][6]/base:.3f}x "
      f"(+{(rows[2][6]/base-1)*100:.1f}%)")
print(f"Same, ISO class 0 vs ASHRAE 72: {rows[1][6]/base:.3f}x")

# ---------------------------------------------------------------- COP conventions
print()
print("=" * 78)
print("2) What COP each rating convention ASSUMES for the compressor rack")
print("=" * 78)
# AHRI 1200-2023 (I-P) Table 1, Low Temperature/Ice Cream column (adjusted dew point degF -> EER Btu/Wh)
ahri_lt_F = np.arange(-36, 0, 1.0)
ahri_lt_EER = np.array([5.48, 5.56, 5.64, 5.73, 5.81, 5.90, 5.98, 6.06, 6.15, 6.24, 6.33, 6.41, 6.50, 6.60,
                        6.70, 6.78, 6.88, 6.98, 7.08, 7.19, 7.29, 7.39, 7.49, 7.60, 7.70, 7.81, 7.92, 8.03,
                        8.14, 8.25, 8.36, 8.48, 8.59, 8.71, 8.83, 8.95])
# Medium/High Temperature column, 0..55 degF
ahri_mt_F = np.arange(0, 56, 1.0)
ahri_mt_EER = np.array([9.25, 9.37, 9.50, 9.63, 9.76, 9.87, 10.03, 10.19, 10.36, 10.52, 10.69, 10.87, 11.05,
                        11.22, 11.40, 11.58, 11.79, 11.99, 12.19, 12.39, 12.59, 12.85, 13.04, 13.27, 13.49,
                        13.72, 13.95, 14.18, 14.47, 14.73, 14.98, 15.27, 15.56, 15.84, 16.13, 16.42, 16.63,
                        16.93, 17.23, 17.53, 17.84, 18.15, 18.47, 18.79, 19.12, 19.45, 19.79, 20.13, 20.48,
                        20.83, 21.19, 21.55, 21.91, 22.28, 22.66, 23.04])
assert len(ahri_lt_F) == len(ahri_lt_EER) and len(ahri_mt_F) == len(ahri_mt_EER)
BTU_PER_WH = 3.412


def cop_ahri(T_dew_C, low_temp):
    """AHRI 1200-2023 sec 5.1.2.1: adjusted dew point = dew point - 3.0 F (LT) or - 2.0 F (MT)."""
    TF = T_dew_C * 9 / 5 + 32 - (3.0 if low_temp else 2.0)
    if low_temp:
        return np.interp(TF, ahri_lt_F, ahri_lt_EER) / BTU_PER_WH
    return np.interp(TF, ahri_mt_F, ahri_mt_EER) / BTU_PER_WH


def cop_iso(T_evap_C, Tc_C=35.0):
    """EN ISO 23953-2 (as reproduced in BIO IS 2007 Lot 12, Box 1-3): REC = t*Phi*(Tc-T0)/(0.34*T0)."""
    T0 = T_evap_C + 273.15
    return 0.34 * T0 / ((Tc_C + 273.15) - T0)


def cop_carnot(T_evap_C, Tc_C=35.0):
    T0 = T_evap_C + 273.15
    return T0 / ((Tc_C + 273.15) - T0)


for label, Te, lt in [("Team's Carnot (evap = case air -18 C)", -18, True),
                      ("Freezer, evap -30 C", -30, True), ("Freezer, evap -35 C", -35, True),
                      ("Chilled, evap -8.3 C (=17 F, ORNL baseline)", -8.33, False)]:
    print(f"{label:46s} Carnot(35C) {cop_carnot(Te):4.2f} | ISO 0.34*Carnot {cop_iso(Te):4.2f} | "
          f"AHRI table {cop_ahri(Te, lt):4.2f}")
# Measured: ORNL/TM-2004/292 Table ES-1 baseline: 12,989 Btu/h load, 1,460 W compressor (condenser excluded)
cop_meas = 12989 / BTU_PER_WH / 1460
print(f"Measured compressor-only COP, ORNL baseline chilled case (SET 17 F, SCT 95 F): {cop_meas:.2f}")

Te = np.linspace(-40, 0, 81)
fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=150)
ax.plot(Te, [cop_carnot(t) for t in Te], color="#888888", ls="--", lw=1.6,
        label="Carnot limit, condensing 35 °C (ideal)")
TeL = np.linspace((-36 + 3 - 32) * 5 / 9, (-1 + 3 - 32) * 5 / 9, 60)  # stay inside the AHRI LT table
ax.plot(TeL, [cop_ahri(t, True) for t in TeL], color="#1f6fb4", lw=2.2,
        label="US rating: AHRI 1200-2023 Table 1 (LT column)")
TeM = np.linspace((0 + 2 - 32) * 5 / 9, 0, 40)  # inside the AHRI MT table
ax.plot(TeM, [cop_ahri(t, False) for t in TeM], color="#1f6fb4", lw=2.2, ls=":",
        label="US rating: AHRI 1200-2023 Table 1 (MT column)")
ax.plot(Te, [cop_iso(t) for t in Te], color="#d1495b", lw=2.2,
        label="EU rating: ISO 23953-2, 0.34 × Carnot, 35 °C")
ax.scatter([-8.33], [cop_meas], color="black", zorder=5, label="Measured, ORNL 2004 chilled case")
ax.axhline(1.7, color="#2a9d8f", lw=1.4, label="Team's assumed freezer COP = 1.7")
ax.axvspan(-38, -28, color="#f2cc8f", alpha=0.35, lw=0)
ax.text(-37.6, 0.25, "typical freezer-case\nevaporating range", fontsize=8)
ax.set_xlabel("Refrigerant evaporating temperature (°C)")
ax.set_ylabel("COP = heat removed ÷ compressor electricity (–)")
ax.set_title("The same case gets a different 'compressor energy' depending on which rulebook rates it",
             fontsize=9)
ax.set_ylim(0, 7)
ax.grid(alpha=0.3)
ax.legend(fontsize=7.2, loc="upper left", framealpha=0.95)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "T03_cop_conventions.png"))
plt.close(fig)

# ---------------------------------------------------------------- regulator metrics worked example
print()
print("=" * 78)
print("3) Worked example: one 2.5 m freezer case under the US and EU metrics")
print("=" * 78)
L_m = 2.5
Dh_m = 1.3      # [ASSUMED] projected visible-product height of a vertical open freezer case
TDA_m2 = L_m * Dh_m
TDA_ft2 = TDA_m2 / 0.09290304
MDEC_open = 2.2 * TDA_ft2 + 6.85   # 10 CFR 431.66(e)(1) VOP.RC.L
MDEC_door = 0.49 * TDA_ft2 + 2.61  # 10 CFR 431.66(e)(1) VCT.RC.L
print(f"TDA = {TDA_m2:.2f} m2 = {TDA_ft2:.1f} ft2 (assumed Dh = {Dh_m} m)")
print(f"US DOE limit, open (VOP.RC.L):  {MDEC_open:5.1f} kWh/day  = {MDEC_open/TDA_m2:4.1f} kWh/day per m2")
print(f"US DOE limit, glass door (VCT.RC.L): {MDEC_door:5.1f} kWh/day  = {MDEC_door/TDA_m2:4.1f} kWh/day per m2")
print(f"  -> DOE lets an open freezer use {MDEC_open/MDEC_door:.1f}x a doored one of the same TDA")
# EU 2019/2024 Annex III: SAE = 365*P*(M+N*Y)*C ; vertical supermarket freezer M=7.5 N=19.3 ; L1 C=1.00 ; remote P=1.00
SAE_day = 1.00 * (7.5 + 19.3 * TDA_m2) * 1.00
print(f"EU reference SAE/365 for ANY vertical freezer cabinet, open or doored: {SAE_day:5.1f} kWh/day")
print(f"  EU ecodesign cap from 1 Sep 2023: EEI <= 80 %  ->  E_daily <= {0.8*SAE_day:5.1f} kWh/day")
for E in (40, 60, 80):
    eei = E / SAE_day * 100
    cls = "A" if eei < 10 else "B" if eei < 20 else "C" if eei < 35 else "D" if eei < 50 else \
        "E" if eei < 65 else "F" if eei < 80 else "G"
    print(f"  a case measuring {E} kWh/day -> EEI {eei:5.1f} %  label class {cls}")

# Team's case: 2.5 kW refrigeration load, compressor via AHRI EER at dew point -30 C
Q_kW = 2.5
Q_btuh = Q_kW * 1000 * BTU_PER_WH
for Tdew in (-30, -35):
    EER = cop_ahri(Tdew, True) * BTU_PER_WH
    CEC = Q_btuh * (24 - 1.0) / (EER * 1000)  # assume 1 h/day defrost (no refrigeration) [ASSUMED]
    print(f"Team case 2.5 kW load, dew {Tdew} C: AHRI EER {EER:.2f} -> CEC {CEC:4.1f} kWh/day (compressor only)")
    REC = Q_kW * (24 - 1.0) / cop_iso(Tdew)
    print(f"   same case, ISO 23953 REC with T0 = {Tdew} C: {REC:4.1f} kWh/day")

# ---------------------------------------------------------------- RH sensitivity, SCE ACEEE 2000
print()
print("=" * 78)
print("4) Store humidity -> case load (SCE/Faramarzi et al. ACEEE 2000, Fig. 5, 75 F dry bulb)")
print("=" * 78)
RH = np.array([35, 40, 45, 50, 55.0])
meat = np.array([1293, 1368, 1453, 1527, 1631.0])    # Btu/hr-ft, Fig. 5 bar labels
dairy = np.array([1409, 1493, 1594, 1675, 1779.0])
for nm, y in (("Meat (open vertical, MT)", meat), ("Dairy/deli (open vertical, MT)", dairy)):
    b, a = np.polyfit(RH, y, 1)
    E = b * 55 / np.polyval([b, a], 55)
    print(f"{nm:32s} slope {b:5.1f} Btu/hr-ft per %RH ({b*0.9615:4.1f} W/m per %RH); "
          f"elasticity at 55% RH = {E:.2f}; 55->35% drop {100*(1-y[0]/y[-1]):4.1f}%")
fig, ax = plt.subplots(figsize=(6.4, 4.0), dpi=150)
ax.plot(RH, meat * 0.9615, "o-", color="#d1495b", label="Open vertical meat case")
ax.plot(RH, dairy * 0.9615, "s-", color="#1f6fb4", label="Open vertical dairy/deli case")
ax.set_xlabel("Store relative humidity at 24 °C (75 °F) dry bulb (%)")
ax.set_ylabel("Measured total case cooling load (W per m of case)")
ax.set_title("Same store temperature, drier air: ~21 % less load (SCE lab data, 2000)", fontsize=9)
ax.grid(alpha=0.3)
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "T03_rh_sensitivity.png"))
plt.close(fig)

# ---------------------------------------------------------------- doors: compressor vs total
print()
print("=" * 78)
print("5) Doors: why -72 % compressor became only -18 % total (Fricke & Becker 2010, field, 24 ft each)")
print("=" * 78)
open_ = dict(comp=42.20, lights=5.18, fans=5.69, ash=0.0)
door = dict(comp=11.70, lights=11.93, fans=4.58, ash=15.50)
to, td = sum(open_.values()), sum(door.values())
for k in open_:
    print(f"{k:7s} open {open_[k]:6.2f}  doored {door[k]:6.2f} kWh/day")
print(f"total   open {to:6.2f}  doored {td:6.2f} kWh/day -> saving {100*(1-td/to):.1f}% ; "
      f"compressor saving {100*(1-door['comp']/open_['comp']):.1f}%")
print(f"if doored case had no anti-sweat heat and same lights as open: "
      f"{door['comp']+open_['lights']+door['fans']:.2f} kWh/day -> saving "
      f"{100*(1-(door['comp']+open_['lights']+door['fans'])/to):.1f}%")

# ---------------------------------------------------------------- shares from ORNL Table ES-1
print()
print("=" * 78)
print("6) Shares computed from ORNL/TM-2004/292 Table ES-1 (baseline 8 ft chilled open multideck)")
print("=" * 78)
tot, inf, cond, rad, internal = 12989, 10674, 526, 1016, 773
print(f"infiltration {inf/tot*100:.1f}% | radiation {rad/tot*100:.1f}% | conduction {cond/tot*100:.1f}% | "
      f"lights+fans {internal/tot*100:.1f}%")
print(f"load per metre: {tot/BTU_PER_WH/2.4384:.0f} W/m ; electric power: compressor 1460 W of 1687 W "
      f"= {1460/1687*100:.0f}% ; fans {115/1687*100:.1f}% ; lights {112/1687*100:.1f}%")
q_dag = 280 * 0.000471947 / 2.4384  # m2/s per metre of case, from 280 cfm through DAG on 8 ft
for v_fpm in (186, 292, 350):
    v = v_fpm * 0.00508
    print(f"DAG flow 280 cfm, mean jet speed {v_fpm} fpm = {v:.2f} m/s -> implied DAG width {q_dag/v*1000:.0f} mm")
nu = 1.33e-5  # m2/s, air near -1 C [ASSUMED]
print(f"Re = 4200 with width w and speed v=q/w gives v*w = {4200*nu:.4f} m2/s vs measured q = {q_dag:.4f} m2/s")

# ---------------------------------------------------------------- indicative LT single-deck breakdown
print()
print("=" * 78)
print("7) Indicative daily energy split, Hillphoenix O2MZD 8 ft frozen-food single deck (tech sheet)")
print("=" * 78)
Q = 587 * 8                     # Btu/h, 'Conventional' BTUH/ft x 8 ft (tech sheet)
EER = np.interp(-17 - 3, ahri_lt_F, ahri_lt_EER)   # evaporator -17 F, AHRI LT adjustment -3 F
t_def = 2 * 0.5                 # h/day: 2 defrosts/day (sheet) x 30 min each [ASSUMED; sheet fail-safe = 60 min]
parts = {"compressor (AHRI calc)": Q * (24 - t_def) / (EER * 1000),
         "defrost heaters 2400 W": 2.4 * t_def,
         "anti-condensate heaters 82 W": 0.082 * 24,
         "fans 22 W": 0.022 * 24}
tot = sum(parts.values())
for k, v in parts.items():
    print(f"{k:30s} {v:5.2f} kWh/day  {v/tot*100:4.1f}%")
print(f"{'total':30s} {tot:5.2f} kWh/day ; EER used {EER:.2f} Btu/Wh (COP {EER/3.412:.2f})")
