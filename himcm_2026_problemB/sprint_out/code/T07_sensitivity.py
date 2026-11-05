"""T07 - one-at-a-time sensitivity of the two headline results to the ASSUMED inputs.
(1) door effect on annual freezer electricity (baseline traffic vs doors sealed), remote rack
(2) freezers' net effect on the store HVAC bill, as a fraction of the freezers' own bill
    (sign tells whether escaping cold is net waste (+) or net recovered (-)).
Run: python3 T07_sensitivity.py
"""
import copy
import numpy as np
import pandas as pd
import T07_store_model as M

PRICE_E, PRICE_G = 0.13, 0.04          # [ASSUMED]
wx = {c: M.load_weather(c) for c in ["houston", "minneapolis"]}
S0, LT0, MT0 = copy.deepcopy(M.STORE), copy.deepcopy(M.LT), copy.deepcopy(M.MT)


def hvac_cost(o):
    return (o.E_AC.sum() * PRICE_E + o.gas.sum() * PRICE_G)


def metrics(c):
    w = wx[c]
    a = M.simulate(w, config="remote")
    b = M.simulate(w, config="remote", door_override=np.zeros(len(w)))
    door = 100 * (a.E_LT.sum() / b.E_LT.sum() - 1)
    door_site = 100 * (a.E_total_site.sum() / b.E_total_site.sum() - 1)
    none = M.simulate(w, config="remote", n_LT=0)
    out = dict(door_LT_pct=door, door_site_pct=door_site)
    for cfg in ["remote", "plugin"]:
        o = a if cfg == "remote" else M.simulate(w, config=cfg)
        out[f"credit_ratio_{cfg}"] = (hvac_cost(o) - hvac_cost(none)) / (o.E_LT.sum() * PRICE_E)
        # summer (Jun-Aug) and winter (Dec-Feb) sign
        for nm, mo in [("JJA", [6, 7, 8]), ("DJF", [12, 1, 2])]:
            k = o.time.dt.month.isin(mo)
            d = (o.E_AC[k].sum() - none.E_AC[k].sum()) * PRICE_E + (o.gas[k].sum() - none.gas[k].sum()) * PRICE_G
            out[f"{cfg}_{nm}_$"] = d
    return out


def setp(path, val):
    obj, key = path
    obj[key] = val
    if obj is M.LT or obj is M.MT:
        M.calibrate(obj)


def reset():
    M.STORE.clear(); M.STORE.update(copy.deepcopy(S0))
    M.LT.clear(); M.LT.update(copy.deepcopy(LT0))
    M.MT.clear(); M.MT.update(copy.deepcopy(MT0))


cases = [("baseline", []),
         ("internal gains 15 W/m2 (-40%)", [((M.STORE, "q_light"), 15e-3)]),
         ("internal gains 35 W/m2 (+40%)", [((M.STORE, "q_light"), 35e-3)]),
         ("no mechanical ventilation", [((M.STORE, "vent_area"), 0.0), ((M.STORE, "vent_person"), 0.0)]),
         ("ventilation x2", [((M.STORE, "vent_area"), 0.6e-3), ((M.STORE, "vent_person"), 7.6e-3)]),
         ("envelope leakage 0.05 ACH", [((M.STORE, "ach_env"), 0.05)]),
         ("envelope leakage 0.3 ACH", [((M.STORE, "ach_env"), 0.3)]),
         ("6 freezer cases", [((M.LT, "n"), 6)]),
         ("24 freezer cases", [((M.LT, "n"), 24)]),
         ("no fridge (MT) cases", [((M.MT, "Q_rated"), 1e-6), ((M.MT, "Q_wallrad"), 0.0), ((M.MT, "P_int"), 0.0)]),
         ("freezer COP 1.3 (Westphalen)", [((M.LT, "COP_ref"), 1.3)]),
         ("AC COP 4", [((M.STORE, "COP_AC"), 4.0)]),
         ("infiltration share 0.85", [((M.LT, "f_inf"), 0.85)]),
         ("UA x2 (poor insulation)", [((M.STORE, "UA"), 4.0)])]

rows = []
for name, changes in cases:
    reset()
    for path, val in changes:
        setp(path, val)
    for c in wx:
        r = metrics(c); r.update(case=name, city=c); rows.append(r)
reset()
# door flow per opening x0.5 and x2 (uncertainty in the ASHRAE/Yuill coefficient)
for f in [0.5, 2.0]:
    A0 = M.A_NV
    M.A_NV = A0 * f
    for c in wx:
        r = metrics(c); r.update(case=f"door air per opening x{f}", city=c); rows.append(r)
    M.A_NV = A0

D = pd.DataFrame(rows)
cols = ["case", "city", "door_LT_pct", "door_site_pct", "credit_ratio_remote", "credit_ratio_plugin",
        "remote_JJA_$", "remote_DJF_$", "plugin_JJA_$", "plugin_DJF_$"]
pd.set_option("display.width", 220)
print(D[cols].round(2).to_string(index=False))
D[cols].to_csv(M.os.path.join(M.DATA, "T07_sensitivity.csv"), index=False)
