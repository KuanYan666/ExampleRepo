"""T06 extras: decomposition eta = sigma*phi*COP_sys, stored-cold loophole, levers, scale check."""
import importlib
import T06_metrics as TM

print("DECOMPOSITION  eta_S = sigma x phi x COP_sys")
for name, kw in [("Baseline", {}), ("Doors fitted", dict(doors=True)), ("Night cover 12 h", dict(night_cover_inf_cut=0.43, night_hours=12))]:
    r = TM.run(name, **kw)
    phi = 1 - r["Q_inf"] / r["Q_tot"]; Qd = r["Q_tot"] * 24
    cop_sys = Qd / r["E"]; sigma = r["S"] / (phi * Qd)
    print(f"  {name:18s} sigma={sigma:6.1f} kg.h per kWh_heat(captured)  phi={phi:.3f}  COP_sys={cop_sys:.3f}"
          f"  product={sigma*phi*cop_sys:6.1f}  direct S/E={r['S']/r['E']:6.1f}")

print("\nSTORED-COLD LOOPHOLE: 10-minute outage")
r = TM.run("b")
q_leak = r["Q_inf"] + r["Q_cond"] if "Q_cond" in r else None
q_leak = r["Q_tot"] - r["P_aux"]
t = 10 / 60
S = TM.BASE["M_product"] * t
dT = q_leak * t * 3600 / (TM.BASE["M_product"] * 2.0)
E_restore = q_leak * t / r["COP"]
print(f"  heat leak with fans/lights off {q_leak:.2f} kW; product warms {dT:.2f} K in 10 min")
print(f"  naive ratio: {S:.0f} kg.h / 0 kWh = infinite;  with restore charge: {S:.0f}/{E_restore:.3f} = {S/E_restore:.0f} kg.h/kWh"
      f"  (running baseline: {r['S']/r['E']:.0f})")

print("\nLEVERS (kWh/day saved vs baseline 43.1)")
b = r["E"]
for name, kw in [("Doors", dict(doors=True)), ("Night cover 12 h", dict(night_cover_inf_cut=0.43, night_hours=12))]:
    print(f"  {name:20s} {b - TM.run(name, **kw)['E']:5.1f}")
# better machine: raise machine quality so baseline COP 1.7 -> 2.0
old = TM.ETA_MACHINE; TM.ETA_MACHINE = old * 2.0 / 1.7
print(f"  {'COP 1.7 -> 2.0':20s} {b - TM.run('cop')['E']:5.1f}")
TM.ETA_MACHINE = old

print("\nSCALE CHECK: does the verdict pattern change if the load is 5 kW instead of 2.5 kW?")
TM.BASE["Q_total"] = 5.0
importlib.reload  # (module constants recomputed below)
s0, l0 = TM.infil_dh(24, 55)
TM.M_INF0 = TM.BASE["Q_total"] * TM.BASE["inf_share"] / (s0 + l0)
TM.UA_COND = TM.BASE["Q_total"] * TM.BASE["cond_share"] / 42.0
TM.UA_COIL = TM.BASE["Q_total"] / TM.BASE["dT_coil"]
TM.LAT0 = TM.M_INF0 * l0
for k in ("P_fan", "P_light", "P_asw", "P_defrost"):
    TM.BASE[k] *= 2
import pandas as pd; pd.set_option("display.width", 200); pd.set_option("display.max_columns", 10)
M, P = TM.table()
M.columns = [c[:22] for c in M.columns]
print(M.iloc[:, [0, 2, 5, 6]].round(3))
print(f"  5 kW baseline energy {P.iloc[0]['E']:.1f} kWh/d = {P.iloc[0]['E']/TM.DOE_OPEN(3.0):.0%} of DOE cap")
