"""Should this be a differential equation? Answer by computing TIME CONSTANTS.
A state needs an ODE only if it changes on a timescale comparable to what you measure."""
import core as C
CP_AIR, CP_FROZEN, H_SUB = 1.006, 2.0, 2835.0

print("="*78); print("TIME CONSTANTS  tau = (heat capacity) / (rate of heat exchange)")
print("="*78)

rows = []
# 1. air inside the case
m_air_case = 1.0*1.45                      # ~1 m3 of cold dense air
C_case = m_air_case*CP_AIR                 # kJ/K
m_inf = 0.027                              # kg/s falling in (computed in freezer.py)
rows.append(("Air inside the case", C_case/(m_inf*CP_AIR), "swapped out by the air curtain"))

# 2. shop air
V_shop, ach = 5000.0, 2.0
m_shop = V_shop*1.2; C_shop = m_shop*CP_AIR
m_vent = V_shop*ach/3600*1.2
rows.append(("Shop air", C_shop/(m_vent*CP_AIR), "ventilation + door exchange"))

# 3. the product
m_prod, UA_prod = 200.0, 0.100            # kg, kW/K  (packaging insulates it)
rows.append(("The FOOD itself", m_prod*CP_FROZEN/UA_prod, "packaging + still air around it"))

# 4. frost
rows.append(("Frost on the coil", 6*3600.0, "grows until the defrost timer fires"))
# 5. door events
rows.append(("One door opening", 8.0, "a few seconds, many times an hour"))

for name, tau, why in sorted(rows, key=lambda r: r[1]):
    if tau < 90:   t = f"{tau:6.0f} s"
    elif tau < 5400: t = f"{tau/60:6.1f} min"
    else: t = f"{tau/3600:6.1f} h"
    print(f"  {name:<22} tau = {t}     ({why})")

print()
print("  YOUR WEATHER DATA ARRIVES ONCE PER HOUR  <-- the resolution that matters")
print()
print("  FASTER than an hour  -> already settled, use algebra (no ODE)")
print("  SIMILAR to an hour   -> needs a differential equation")
print("  MUCH faster + repeats-> average it into a rate, do not simulate each event")

print(); print("="*78)
print("IS THE FEEDBACK LOOP ACTUALLY STRONG?  (heat out -> shop warms -> load rises)")
print("="*78)
T_shop, RH_shop = 24.0, 55.0
W_shop = C.W_from_RH(T_shop, RH_shop); W_case = C.W_from_RH(-18.0, 90.0)
base = CP_AIR*(T_shop-(-18.0)) + (W_shop-W_case)*H_SUB
print(f"  baseline load per kg of air : {base:.1f} kJ/kg")
print(f"  shop 1 degC warmer          : +{CP_AIR:.2f} kJ/kg  = +{100*CP_AIR/base:.1f}%")
print(f"  shop 1 g/kg wetter          : +{H_SUB/1000:.2f} kJ/kg  = +{100*H_SUB/1000/base:.1f}%")
print(f"  -> moisture is {(H_SUB/1000)/CP_AIR:.1f}x more potent per unit than temperature")

print()
T_out, RH_out = 32.0, 60.0
W_out = C.W_from_RH(T_out, RH_out)
dT, dW = T_out-T_shop, W_out-W_shop
q_T, q_W = CP_AIR*dT, dW*H_SUB
print(f"  WHEN THE SHOP DOOR OPENS (outdoor {T_out}C/{RH_out}% vs shop {T_shop}C/{RH_shop}%):")
print(f"    the air it lets in is {dT:.0f} degC warmer and {dW*1000:.1f} g/kg wetter")
print(f"    extra load from TEMPERATURE : {q_T:5.1f} kJ/kg   {100*q_T/(q_T+q_W):4.1f}%")
print(f"    extra load from MOISTURE    : {q_W:5.1f} kJ/kg   {100*q_W/(q_T+q_W):4.1f}%")
print()
print("  -> the door's damage is mostly WATER, not heat. A temperature-only")
print("     differential equation would miss three-quarters of the effect.")
