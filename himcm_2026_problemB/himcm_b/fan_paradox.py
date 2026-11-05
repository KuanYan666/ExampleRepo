"""
THE FAN PARADOX: SET says the fan always helps; UTCI says it HURTS in hot-dry air.
The physiological literature (Jay et al.) sides with UTCI. Map the disagreement.
"""
import numpy as np
import core as C, scenario as S

cal = S.calibrate()
S.VENUES["bus_stop"]["A_open_eff"] = cal["A_open_fit"]
V = S.VENUES["bus_stop"]


class Row:
    def __init__(s, T, RH, w=1.0):
        s.temperature_2m=T; s.relative_humidity_2m=RH; s.wind_speed_10m=w
        s.direct_radiation=0.0; s.diffuse_radiation=120.0; s.sol_alt=40.0


def deltas(T, RH, dev):
    row = Row(T, RH)
    Tb,RHb,vb,trb = S.shelter_state(row, V, S.DEVICES["none"], cal)
    Tc,RHc,vc,trc = S.shelter_state(row, V, S.DEVICES[dev], cal)
    return (C.SET(Tb,RHb,vb,trb)-C.SET(Tc,RHc,vc,trc),
            C.UTCI(Tb,RHb,max(vb,.5),trb)-C.UTCI(Tc,RHc,max(vc,.5),trc))

Ts  = np.arange(28, 51, 2)
RHs = np.arange(10, 95, 5)

print("="*92)
print("SIGN OF THE FAN'S EFFECT ON UTCI   (+ = fan helps, - = fan makes it WORSE)")
print("="*92)
print("  T\\RH " + "".join(f"{int(r):>6}" for r in RHs))
for T in Ts:
    line = f"  {T:>3}  "
    for RH in RHs:
        _, du = deltas(T, RH, "fan")
        line += f"{du:>6.2f}"
    print(line)

print("\n" + "="*92)
print("WHERE DOES THE FAN TURN HARMFUL?  (UTCI crossover temperature by humidity)")
print("="*92)
for RH in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
    cross = None
    for T in np.arange(26, 52, 0.25):
        _, du = deltas(T, RH, "fan")
        if du < 0: cross = T; break
    print(f"  RH={RH:>3}% : fan becomes harmful above "
          + (f"{cross:.1f} C" if cross else "52 C (never, in range)"))

print("\n" + "="*92)
print("SET vs UTCI DISAGREEMENT ON THE FAN (the model-choice problem, in numbers)")
print("="*92)
print(f"{'T':>4} {'RH':>4} | {'dSET':>7} {'dUTCI':>7} | verdict")
for T,RH in [(32,70),(34,80),(36,40),(38,30),(40,20),(42,15),(44,12),(46,10),(48,10)]:
    ds, du = deltas(T,RH,"fan")
    v = "agree: helps" if ds>0 and du>0 else ("DISAGREE: SET helps, UTCI harms" if ds>0>du else "agree: harms")
    print(f"{T:>4} {RH:>4} | {ds:>7.2f} {du:>7.2f} | {v}")

print("\n" + "="*92)
print("PUBLIC-HEALTH FAN CUT-OFFS DISAGREE TOO -- energy consequence of each rule")
print("="*92)
import pandas as pd
for city in ["Phoenix","LasVegas","Seville","Houston","Singapore"]:
    df = pd.read_csv(f"data/{city}.csv")
    T = df.temperature_2m.values
    tot = len(T)
    print(f"  {city:<10} hours above CDC 32.2C: {100*(T>32.2).mean():5.1f}%   "
          f"above WHO 40C: {100*(T>40).mean():5.1f}%   "
          f"above our UTCI-derived cut-off: see map")
