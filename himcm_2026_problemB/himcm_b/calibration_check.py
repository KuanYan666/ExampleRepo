"""
THE KEY RESULT: can one capture-fraction parameter reproduce BOTH evaporative
claims in the problem table at once? If yes, the table is internally consistent
with open-system mixing physics, and the implied waste fraction can be compared
with the open-freezer-case literature (67-85% of load lost through the air curtain).
"""
import numpy as np, core as C

EPS_REAL = 0.85          # real direct evaporative pad, manufacturer range 0.70-0.90
Q = {"evap": 1.10, "evap_big": 2.50}     # m3/s supply airflow
CLAIM = {"evap": 5.0, "evap_big": 8.0}   # degC "effect on shelter"


def implied_K(design=(43.0, 12.0), eps=EPS_REAL):
    """K = infiltration airflow (m3/s). phi = Q/(Q+K); delivered = phi*eps*wbd."""
    Td, RHd = design
    wbd = Td - C.T_wetbulb(Td, RHd)
    outlet_drop = eps * wbd
    out = {}
    for k, q in Q.items():
        phi_needed = CLAIM[k] / outlet_drop
        if phi_needed >= 1:
            out[k] = (phi_needed, float("nan")); continue
        out[k] = (phi_needed, q * (1 - phi_needed) / phi_needed)
    return wbd, outlet_drop, out


print("=" * 74)
print("INTERNAL-CONSISTENCY TEST OF THE PROBLEM'S OWN TABLE")
print("=" * 74)
for design in [(43, 12), (41, 15), (45, 10), (38, 20)]:
    wbd, outlet, out = implied_K(design)
    ks = [v[1] for v in out.values()]
    spread = abs(ks[0] - ks[1]) / np.mean(ks) * 100
    print(f"\ndesign {design[0]}C/{design[1]}%RH   wet-bulb depression {wbd:5.2f}C   "
          f"outlet drop {outlet:5.2f}C")
    for k, (phi, K) in out.items():
        print(f"   {k:9s} Q={Q[k]:.2f} m3/s  -> capture phi={phi:.3f} "
              f"({100*(1-phi):4.1f}% of the cooling lost)   implied K={K:.2f} m3/s")
    print(f"   two independent estimates of K disagree by {spread:.1f}%")

print("\n" + "=" * 74)
print("SENSITIVITY OF THE CONCLUSION TO THE ASSUMED PAD EFFICIENCY")
print("=" * 74)
for eps in (0.70, 0.75, 0.80, 0.85, 0.90):
    wbd, outlet, out = implied_K((43, 12), eps)
    ks = [v[1] for v in out.values()]
    phis = [v[0] for v in out.values()]
    print(f"  eps={eps:.2f}  waste = {100*(1-phis[0]):4.1f}% (small) / "
          f"{100*(1-phis[1]):4.1f}% (large)   K = {ks[0]:.2f} / {ks[1]:.2f} m3/s "
          f"(spread {abs(ks[0]-ks[1])/np.mean(ks)*100:4.1f}%)")

print("\n" + "=" * 74)
print("WHAT THE FAN CLAIM IMPLIES (ASHRAE 55 cooling effect, inverted)")
print("=" * 74)
import scenario as S
for design in [(43, 12), (38, 20), (34, 70), (32, 80)]:
    v = C.v_fan_from_claimed_CE(3.0, design[0], design[1])
    print(f"  to 'feel 3C cooler' at {design[0]}C/{design[1]}%RH the fan must deliver "
          f"{v:.2f} m/s at the person")
