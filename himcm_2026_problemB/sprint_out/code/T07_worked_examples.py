"""T07 - worked numbers for the memo (one hour in each climate, monthly COP vs load split)."""
import numpy as np
import T07_store_model as M
for c, ts in [("houston", "2023-07-20 17:00"), ("minneapolis", "2023-01-18 17:00")]:
    w = M.load_weather(c)
    o = M.simulate(w); b = M.simulate(w, door_override=np.zeros(len(w)))
    i = int(np.where(o.time == np.datetime64(ts))[0][0])
    r, rb = o.iloc[i], b.iloc[i]
    print(f"--- {c} {ts}")
    print(f"outdoor {r.T_o:.1f} C, RH {r.RH_o:.0f} %, W {r.W_o*1000:.2f} g/kg | door openings {r.N:.0f}/h, door air {r.q_door:.2f} m3/s = {r.q_door*1.2:.2f} kg/s")
    print(f"store  {r.T_i:.1f} C, RH {r.RH_i:.1f} %, W {r.W_i*1000:.2f} g/kg (doors sealed: {rb.T_i:.1f} C, RH {rb.RH_i:.1f} %, W {rb.W_i*1000:.2f})")
    print(f"one case load {r.Q_LT_case:.3f} kW (sens-from-store {r.Q_LT_sens:.3f}, latent {r.Q_LT_lat:.3f}); sealed {rb.Q_LT_case:.3f} kW -> {100*(r.Q_LT_case/rb.Q_LT_case-1):+.1f} %")
    print(f"COP_LT {r.cop_LT:.2f}; lineup electricity {r.E_LT:.2f} kW (sealed {rb.E_LT:.2f}); mode {r['mode']}; AC sens {r.Q_cool_s:.1f} kW lat {r.Q_cool_lat:.1f} kW; heat {r.Q_heat:.1f} kW")
    print(f"door sensible load = m cp dT = {r.q_door*1.2*1.006*(r.T_o-r.T_i):.1f} kW ; door latent load = m h_fg dW = {r.q_door*1.2*2501*(r.W_o-r.W_i):.1f} kW")
    print(f"freezer lineup credit to store: {r.credit_LT:.1f} kW (sensible {r.credit_LT_sens:.1f})")
    g = o.groupby(o.time.dt.month).agg(cop=("cop_LT", "mean"), load=("Q_LT_case", "mean"), E=("E_LT", "sum"))
    print("monthly mean COP:", " ".join(f"{x:.2f}" for x in g.cop))
    print("monthly mean case load kW:", " ".join(f"{x:.2f}" for x in g.load))
    print(f"store RH range (hourly): {o.RH_i.min():.0f}-{o.RH_i.max():.0f} %, hours above 55 %: {(o.RH_i>55).sum()}, above 60 %: {(o.RH_i>60).sum()}")
    print(f"annual mean case load {o.Q_LT_case.mean():.2f} kW vs rated 2.50 kW")

# ---- monthly HVAC penalty (+) / saving (-) caused by the freezers, as a fraction of the freezers' own
# electricity bill, and the freezers' energy seen at the case boundary vs the store boundary
for c in ["houston", "minneapolis"]:
    w = M.load_weather(c); none = M.simulate(w, n_LT=0)
    for cfg in ["remote", "plugin", "reclaim"]:
        o = M.simulate(w, config=cfg)
        g = o.groupby(o.time.dt.month); n = none.groupby(none.time.dt.month)
        d = (g.E_AC.sum() - n.E_AC.sum()) * 0.13 + (g.gas.sum() - n.gas.sum()) * 0.04
        r = d / (g.E_LT.sum() * 0.13)
        store_b = (o.E_LT.sum() + o.E_AC.sum() - none.E_AC.sum() + o.gas.sum() - none.gas.sum()) / 1e3
        print(c, cfg, "ratio by month:", " ".join(f"{x:+.2f}" for x in r),
              f"| case-boundary {o.E_LT.sum()/1e3:.1f} MWh, store-boundary {store_b:.1f} MWh (site)")
