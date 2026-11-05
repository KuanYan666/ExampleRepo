"""Validate the integral jet model: (1) free-jet decay, (2) fit beta to Pratte & Baines."""
import numpy as np, sys
sys.path.insert(0, '.')
import T08_jetmodel as J
from scipy.optimize import minimize_scalar

# (1) free jet, no wind, no buoyancy: top-hat speed U = M/Q; Gaussian centreline = 2*U_tophat
jet = J.integrate_jet(1.0, 0.4, 0.0, (0,1,0), (0,0,0), (1,0,0), ds=0.01, s_max=8)
s = jet['pos'][:,0]
for x in [2,4,8]:
    i = np.argmin(abs(s-x*0.4*5))
for xd in [5,10,20]:
    i = np.argmin(abs(s-xd*0.4))
    print(f"free jet x/d={xd}: Uc/U0 model={2*jet['speed'][i]/jet['U0']:.3f}  5.8 d/x={5.8/xd:.3f}  Q/Q0={jet['Q'][i]:.2f}")

# (2) fit beta so trajectory matches PB z/(rd)=2.05 (x/rd)^0.28 for x/rd in [0.3, 10]
def traj_err(beta, rs=(4,6,10,15)):
    err=[]
    for r in rs:
        d=0.1; U0=r*1.0
        Q0=U0*np.pi*d*d/4
        jet=J.integrate_jet(Q0,d,1.0,(1,0,0),(0,0,0),(0,1,0),beta=beta,ds=d/40,s_max=12*r*d)
        x=jet['pos'][:,0]/(r*d); z=jet['pos'][:,1]/(r*d)
        m=(x>0.3)&(x<10)
        if m.sum()<5: return 1e3
        zpb=2.05*x[m]**0.28
        err.append(np.mean((np.log(z[m])-np.log(zpb))**2))
    return np.mean(err)
res=minimize_scalar(traj_err,bounds=(0.05,1.5),method='bounded')
print("best beta = %.3f  rms log error = %.3f"%(res.x,np.sqrt(res.fun)))
b=res.x
# power-law fit of the model trajectory -> compare with Margason band A 1.2-2.6, B .28-.34
for r in (4,10,15):
    d=0.1;Q0=r*np.pi*d*d/4
    jet=J.integrate_jet(Q0,d,1.0,(1,0,0),(0,0,0),(0,1,0),beta=b,ds=d/40,s_max=12*r*d)
    x=jet['pos'][:,0]/(r*d); z=jet['pos'][:,1]/(r*d); m=(x>0.3)&(x<10)
    B,lnA=np.polyfit(np.log(x[m]),np.log(z[m]),1)
    print(f"r={r}: model fits z/rd = {np.exp(lnA):.2f} (x/rd)^{B:.3f}")
