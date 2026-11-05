"""T08 sensitivity: how robust are calm phi and the 'useless' wind speed?"""
import sys, os, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import T08_jetmodel as J
dT0 = 18.75; PU = 1 / dT0
Ua = np.r_[0, np.linspace(0.25, 6, 24)]
def useless_speed(Q, d, **kw):
    y = np.array([J.phi_device(Q, d, u, 270, "end-fire", dT0, **kw) for u in Ua])
    for i in range(1, len(Ua)):
        if y[i-1] >= PU > y[i]:
            return y[0], Ua[i-1] + (PU-y[i-1])*(Ua[i]-Ua[i-1])/(y[i]-y[i-1])
    return y[0], (np.nan if y[0] < PU else np.inf)
B = (1.10, math.sqrt(4*1.10/(math.pi*8)))
print("base teamB: calm phi %.3f, useless at Ua %.2f" % useless_speed(*B))
for beta in (0.1, 0.3, 0.45):
    print(f"beta={beta}: calm %.3f useless Ua %.2f" % useless_speed(*B, beta=beta))
for zhi in (1.5, 2.1):
    sh = dict(J.SHELTER); sh["z_hi"] = zhi
    print(f"zone top {zhi} m: calm %.3f useless Ua %.2f" % useless_speed(*B, sh=sh))
for Lx, Ly in ((4.0, 2.0), (8.0, 2.0)):
    sh = dict(J.SHELTER); sh["Lx"] = Lx; sh["Ly"] = Ly
    J.LAYOUTS["end-fire"] = dict(x0=(0.0, Ly/2, 1.0), jet=(1, 0, 0))
    print(f"shelter {Lx}x{Ly} m: calm %.3f useless Ua %.2f" % useless_speed(*B, sh=sh))
J.LAYOUTS["end-fire"] = dict(x0=(0.0, 1.5, 1.0), jet=(1, 0, 0))
for dT in (8.0, 25.0):
    print(f"outlet drop {dT} C (buoyancy only): calm phi %.3f" % J.phi_device(1.10, B[1], 0, 270, "end-fire", dT))
for U0 in (4.0, 12.0):
    d = math.sqrt(4*1.10/(math.pi*U0))
    print(f"same 1.10 m3/s through U0={U0} (d={d:.2f}): calm %.3f useless Ua %.2f" % useless_speed(1.10, d))
