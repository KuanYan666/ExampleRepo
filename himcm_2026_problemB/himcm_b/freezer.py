"""Task 1: the open freezer case. Theoretical model -> where it breaks."""
import core as C

CP = 1.006
H_FG = 2501.0      # vaporisation, kJ/kg
H_IF = 334.0       # fusion, kJ/kg  -> vapour that enters a freezer condenses AND freezes
H_SUB = H_FG + H_IF

STORE = (24.0, 55.0)      # aisle air
CASE = (-18.0, 90.0)      # inside the case
T_COND = 35.0             # condenser rejects heat at ~35 C

print("=" * 70)
print("STEP 1  THE IDEAL MACHINE  (second law: there is a floor you cannot beat)")
print("=" * 70)
Tc, Th = CASE[0] + 273.15, T_COND + 273.15
cop_carnot = Tc / (Th - Tc)
print(f"  cold side {CASE[0]} C = {Tc:.2f} K,  hot side {T_COND} C = {Th:.2f} K")
print(f"  COP_Carnot = Tc/(Th-Tc) = {cop_carnot:.2f}")
for cop_real in (1.3, 1.7, 2.0):
    print(f"  real COP {cop_real}  ->  second-law efficiency {100*cop_real/cop_carnot:.0f}%")

print()
print("=" * 70)
print("STEP 2  WHAT THE AIR CARRIES IN  (the open front)")
print("=" * 70)
W_store = C.W_from_RH(*STORE)
W_case = C.W_from_RH(*CASE)
dT = STORE[0] - CASE[0]
dW = W_store - W_case
q_sens = CP * dT
q_lat = dW * H_SUB
print(f"  store air {STORE[0]} C / {STORE[1]}% RH   -> W = {W_store*1000:.2f} g/kg")
print(f"  case  air {CASE[0]} C / {CASE[1]}% RH   -> W = {W_case*1000:.3f} g/kg")
print(f"  temperature difference : {dT:.0f} C")
print(f"  moisture difference    : {dW*1000:.2f} g/kg")
print()
print(f"  SENSIBLE load per kg of air : cp*dT      = {q_sens:6.1f} kJ/kg  ({100*q_sens/(q_sens+q_lat):.0f}%)")
print(f"  LATENT   load per kg of air : dW*h_sub   = {q_lat:6.1f} kJ/kg  ({100*q_lat/(q_sens+q_lat):.0f}%)")
print(f"  TOTAL                                    = {q_sens+q_lat:6.1f} kJ/kg")
print()
print("  -> every kg of aisle air that falls in costs MORE to dry than to chill.")
print("  -> and that water becomes FROST on the coil, which must be melted off later.")

print()
print("=" * 70)
print("STEP 3  A WHOLE CASE  (2.5 m open vertical display case)")
print("=" * 70)
TOTAL_LOAD = 2.5           # kW, typical for a 2.5 m case
INFIL_SHARE = 0.75         # literature: 67-85%
q_inf = TOTAL_LOAD * INFIL_SHARE
m_inf = q_inf / (q_sens + q_lat)
print(f"  assumed total refrigeration load : {TOTAL_LOAD:.1f} kW")
print(f"  infiltration share (literature)  : {100*INFIL_SHARE:.0f}%  -> {q_inf:.2f} kW")
print(f"  implied infiltrating air         : {m_inf:.3f} kg/s = {m_inf/1.2*1000:.0f} L/s of aisle air")
print()
breakdown = {
    "Infiltration - sensible": q_inf * q_sens / (q_sens + q_lat),
    "Infiltration - latent (frost)": q_inf * q_lat / (q_sens + q_lat),
    "Conduction through insulation": TOTAL_LOAD * 0.06,
    "Radiation into the opening": TOTAL_LOAD * 0.06,
    "Lights, fans, defrost": TOTAL_LOAD * 0.13,
}
for k, v in breakdown.items():
    print(f"    {k:<32} {v:5.2f} kW   {100*v/TOTAL_LOAD:4.1f}%")
print(f"    {'TOTAL':<32} {sum(breakdown.values()):5.2f} kW")

print()
print("=" * 70)
print("STEP 4  ENERGY IS CONSERVED -- THE HEAT DOES NOT DISAPPEAR")
print("=" * 70)
for cop in (1.7,):
    W_elec = TOTAL_LOAD / cop
    Q_rej = TOTAL_LOAD + W_elec
    print(f"  heat pulled out of the case   : {TOTAL_LOAD:.2f} kW")
    print(f"  electrical work to do it      : {W_elec:.2f} kW   (COP = {cop})")
    print(f"  heat dumped at the condenser  : {Q_rej:.2f} kW   <- conservation of energy")
    print()
    print(f"  If that condenser sits inside the building, the shop's air conditioning")
    print(f"  must now remove {Q_rej:.2f} kW. At store-AC COP 3.0 that costs another "
          f"{Q_rej/3.0:.2f} kW.")
    print(f"  TOTAL electricity for one freezer case: {W_elec + Q_rej/3.0:.2f} kW")

print()
print("=" * 70)
print("STEP 5  THE TWO LEVERS, COMPARED")
print("=" * 70)
print("  Lever A - better machine: raise COP 1.7 -> 2.0 (hard, and Carnot caps it at "
      f"{cop_carnot:.1f})")
print(f"     saves {TOTAL_LOAD/1.7 - TOTAL_LOAD/2.0:.3f} kW "
      f"({100*(TOTAL_LOAD/1.7-TOTAL_LOAD/2.0)/(TOTAL_LOAD/1.7):.0f}% of compressor power)")
print("  Lever B - fit doors: cut infiltration by 80% (ordinary engineering, no physics limit)")
new_load = TOTAL_LOAD - 0.8 * q_inf
print(f"     load {TOTAL_LOAD:.2f} -> {new_load:.2f} kW, "
      f"saves {TOTAL_LOAD/1.7 - new_load/1.7:.3f} kW "
      f"({100*(TOTAL_LOAD-new_load)/TOTAL_LOAD:.0f}% of compressor power)")
