"""Design map: which device wins, as a function of (T, RH)? And where is the crossover?

Occupancy cancels when comparing devices at the same hour, so this is a clean
per-person, per-kW comparison. This is the figure that should go on page 1.
"""
import numpy as np, math
import core as C, scenario as S

cal = S.calibrate()
S.VENUES["bus_stop"]["A_open_eff"] = cal["A_open_fit"]
V = S.VENUES["bus_stop"]
WIND = 1.0


class Row:  # duck-type an itertuples row
    def __init__(self, T, RH):
        self.temperature_2m = T; self.relative_humidity_2m = RH
        self.wind_speed_10m = WIND; self.direct_radiation = 0.0
        self.diffuse_radiation = 120.0; self.sol_alt = 40.0


def per_kW(T, RH, dev):
    row = Row(T, RH)
    Tb, RHb, vb, trb = S.shelter_state(row, V, S.DEVICES["none"], cal)
    Tc, RHc, vc, trc = S.shelter_state(row, V, S.DEVICES[dev], cal)
    sb, sc = C.SET(Tb, RHb, vb, trb), C.SET(Tc, RHc, vc, trc)
    ub, uc = C.UTCI(Tb, RHb, max(vb, .5), trb), C.UTCI(Tc, RHc, max(vc, .5), trc)
    P = S.DEVICES[dev]["P"]
    return dict(dSET=(sb - sc) / P,
                dComfort=(C.dissatisfied_fraction(sb) - C.dissatisfied_fraction(sc)) / P,
                dRisk=(C.heat_risk(ub) - C.heat_risk(uc)) / P,
                set_base=sb, utci_base=ub)


DEVS = ["fan", "evap", "evap_big"]
Ts = np.arange(28, 49, 2)
RHs = np.arange(10, 95, 5)

for metric, title in [("dComfort", "COMFORT per kWh"), ("dRisk", "HEAT-STRESS RISK removed per kWh")]:
    print("=" * 86)
    print(f"WINNING DEVICE BY {title}   (F=fan, E=evap, L=large evap, .=nothing works)")
    print("=" * 86)
    print("  T\\RH " + "".join(f"{int(r):>4}" for r in RHs))
    for T in Ts:
        line = f"  {T:>3}  "
        for RH in RHs:
            if C.T_wetbulb(T, RH) > T:   # impossible
                line += "   -"; continue
            vals = {d: per_kW(T, RH, d)[metric] for d in DEVS}
            best = max(vals, key=vals.get)
            line += "   ." if max(vals.values()) <= 1e-9 else \
                    f"   {'F' if best=='fan' else 'E' if best=='evap' else 'L'}"
        print(line)
    print()

print("=" * 86)
print("CROSSOVER: wet-bulb depression at which evap overtakes the fan (risk currency)")
print("=" * 86)
for T in [34, 38, 42, 46]:
    cross = None
    for RH in np.arange(95, 5, -0.5):
        vals = {d: per_kW(T, RH, d)["dRisk"] for d in DEVS}
        if max(vals, key=vals.get) != "fan" and max(vals.values()) > 0:
            cross = RH; break
    if cross is None:
        print(f"  T={T}C : fan never overtaken in this RH range"); continue
    wbd = T - C.T_wetbulb(T, cross)
    print(f"  T={T}C : evaporative overtakes the fan below RH={cross:.0f}%  "
          f"(wet-bulb depression {wbd:.1f} C)")

print()
print("=" * 86)
print("WHY: the two currencies disagree because the fan SATURATES")
print("=" * 86)
print(f"{'T':>4} {'RH':>4} | {'UTCI base':>9} {'fan':>7} {'evap':>7} {'large':>7} | band")
for T, RH in [(34, 80), (38, 60), (42, 20), (46, 12), (46, 40)]:
    row = Row(T, RH)
    out = []
    for d in ["none", "fan", "evap", "evap_big"]:
        Tc, RHc, vc, trc = S.shelter_state(row, V, S.DEVICES[d], cal)
        out.append(C.UTCI(Tc, RHc, max(vc, .5), trc))
    band = ["no stress", "moderate", "strong", "very strong", "extreme"][
        min(4, sum(out[0] > x for x in [26, 32, 38, 46]))]
    print(f"{T:>4} {RH:>4} | {out[0]:>9.1f} {out[1]:>7.1f} {out[2]:>7.1f} {out[3]:>7.1f} | {band}")
