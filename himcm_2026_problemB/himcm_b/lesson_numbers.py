"""Generate and check every worked number used in the physics lesson."""
import core as C

P = 101325.0
CP = 1.006          # kJ/kg.K  dry air
HFG = 2450.0        # kJ/kg    latent heat of vaporisation near 20-40 C


def rho(T):          # ideal gas, dry-air approximation
    return P / (287.05 * (T + 273.15))


print("=" * 72); print("PART 1  AIR PROPERTIES"); print("=" * 72)
for T in (20, 30, 40, 43):
    print(f"  T={T:>2}C   density {rho(T):.3f} kg/m3   rho*cp = {rho(T)*CP:.3f} kJ/(m3.K)")

print("\n  Energy to cool one bus shelter of air (15 m2 x 2.5 m = 37.5 m3) by 1 C:")
V = 37.5
print(f"    {V*rho(40)*CP:.1f} kJ  = {V*rho(40)*CP/3600:.4f} kWh   (a tiny amount!)")
print("  ...which is why the ENERGY is not in the air, it is in the CONTINUOUS replacement.")

print("\n" + "=" * 72); print("PART 3  PSYCHROMETRIC TABLE (check these by hand on a chart)"); print("=" * 72)
print(f"  {'T':>4} {'RH':>4} | {'p_ws':>8} {'p_w':>8} | {'W':>8} | {'T_wb':>6} {'WBD':>6} | {'T_dew':>6}")
print(f"  {'C':>4} {'%':>4} | {'kPa':>8} {'kPa':>8} | {'g/kg':>8} | {'C':>6} {'C':>6} | {'C':>6}")
cases = [(43, 12), (40, 25), (35, 40), (32, 80), (34, 70), (28, 90), (20, 50)]
for T, RH in cases:
    pws = C.p_ws(T) / 1000
    pw = pws * RH / 100
    W = C.W_from_RH(T, RH) * 1000
    wb = C.T_wetbulb(T, RH)
    # dew point: temperature at which p_ws = p_w
    lo, hi = -60.0, T
    for _ in range(60):
        m = (lo + hi) / 2
        if C.p_ws(m) / 1000 < pw: lo = m
        else: hi = m
    print(f"  {T:>4} {RH:>4} | {pws:>8.3f} {pw:>8.3f} | {W:>8.2f} | {wb:>6.1f} {T-wb:>6.1f} | {(lo+hi)/2:>6.1f}")

print("\n" + "=" * 72); print("PART 4  THE EVAPORATIVE COOLER, WORKED"); print("=" * 72)
Q = 1.10            # m3/s
eps = 0.85
for (T, RH, name) in [(43, 12, "Phoenix design"), (32, 80, "Singapore")]:
    Tout, RHout, Wout = C.evaporative_cooler(T, RH, eps)
    wb = C.T_wetbulb(T, RH)
    mdot = Q * rho(T)
    drop = T - Tout
    Qsens = mdot * CP * drop                        # kW of sensible cooling
    dW = Wout - C.W_from_RH(T, RH)
    water = mdot * dW * 3600                        # kg/h of water evaporated
    print(f"\n  {name}: T={T}C RH={RH}%")
    print(f"    wet-bulb {wb:.1f}C -> wet-bulb depression {T-wb:.1f}C  <-- the WHOLE budget")
    print(f"    outlet air: {Tout:.1f}C at {RHout:.0f}% RH   (drop {drop:.1f}C)")
    print(f"    mass flow {mdot:.2f} kg/s")
    print(f"    sensible cooling delivered    : {Qsens:.1f} kW")
    print(f"    electrical power drawn        : 1.2 kW   -> ratio {Qsens/1.2:.1f}x")
    print(f"    water evaporated              : {water:.1f} kg/h = {water:.0f} L/h")
    print(f"    latent heat check: {water/3600*HFG:.1f} kW  (should match sensible {Qsens:.1f} kW)")

print("\n" + "=" * 72); print("PART 5  THE HUMAN SIGN FLIP"); print("=" * 72)
print("  Skin ~35C. Convective heat flow from AIR to SKIN, per m2, at 1.25 m/s:")
print("  h_c ~ 8.3*v^0.6 = %.1f W/(m2.K)" % (8.3 * 1.25 ** 0.6))
hc_still, hc_fan = 8.3 * 0.3 ** 0.6, 8.3 * 1.25 ** 0.6
for Ta in (28, 32, 35, 38, 43, 47):
    q_still = hc_still * (Ta - 35)
    q_fan = hc_fan * (Ta - 35)
    tag = "skin LOSES heat (good)" if Ta < 35 else ("neutral" if Ta == 35 else "skin GAINS heat (bad)")
    print(f"    Ta={Ta:>2}C: still {q_still:+6.1f} W/m2   fan {q_fan:+6.1f} W/m2   "
          f"fan changes it by {q_fan-q_still:+6.1f}  <- {tag}")

print("\n" + "=" * 72); print("PART 7  MIXING AND CAPTURE FRACTION"); print("=" * 72)
T, RH, phi = 43, 12, 0.255
Ts, RHs, Ws = C.evaporative_cooler(T, RH, eps)
Wa = C.W_from_RH(T, RH)
Tz, Wz = C.mix(Ts, Ws, T, Wa, phi)
print(f"  ambient {T}C/{RH}%RH  (W={Wa*1000:.2f} g/kg)")
print(f"  supply  {Ts:.1f}C/{RHs:.0f}%RH  (W={Ws*1000:.2f} g/kg)")
print(f"  phi = {phi}  ->  shelter {Tz:.1f}C / {C.RH_from_W(Tz,Wz):.0f}%RH")
print(f"  DELIVERED drop = {T-Tz:.1f} C   (vs {T-Ts:.1f} C at the outlet)")
print(f"  => {100*(1-phi):.0f}% of the cooling went to the atmosphere")
print("\n  THE RH TRAP -- mixing on RH instead of W gives the WRONG answer:")
wrong_RH = phi * RHs + (1 - phi) * RH
print(f"    mixing RH linearly: {wrong_RH:.0f}%    correct answer: {C.RH_from_W(Tz,Wz):.0f}%")
