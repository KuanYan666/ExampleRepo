"""T11 - runs every number quoted in T11_rail_station_zone.md. Output -> T11_out/ (csv + txt)."""
import json, math, pathlib
import numpy as np
import pandas as pd
from scipy.optimize import brentq
import T11_zone_model as M
import core as C
import scenario as SC

OUT = pathlib.Path(__file__).parent / "T11_out"
OUT.mkdir(exist_ok=True)
LOG = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.append(s)


WX = {c: M.weather_point(c) for c in ("Phoenix", "Houston")}
for c, w in WX.items():
    say(f"[weather] {c} median 13-17h summer-2025:", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in w.items()})

# ------------------------------------------------------------------ 0. nested bus-stop check
SC.DEVICES["evap_nm"] = dict(SC.DEVICES["evap"], P=0.0)
SC.DEVICES["big_nm"] = dict(SC.DEVICES["evap_big"], P=0.0)
wd = dict(To=43.0, RH=12.0, U10=0.5, Idir=0, Idif=0, GHI=0, alt=60)
say("\n[0] Nested check: zone model in bus-stop configuration, 43 C / 12 %, no people, no sun")
for d, claim in (("evap_nm", 5), ("big_nm", 8), ("evap", 5), ("evap_big", 8)):
    r = M.solve_zone(wd, 0, d, z=M.BUS, sun=False, people=False)
    say(f"   {d:9s} delivered dT = {43 - r['Tz']:.2f} C (COMAP claim {claim}), phi = {r['phi']:.3f}")

# ------------------------------------------------------------------ 1. limiting cases
say("\n[1] Limiting cases (Phoenix weather, adiabatic roof, no sun, no people, large cooler, motor heat OFF and ON)")
rows = []
for A in np.logspace(-3, 4, 36):
    z = dict(M.ZONE, A_open=A)
    for d in ("big_nm", "evap_big"):
        r = M.solve_zone(WX["Phoenix"], 0, d, z=dict(z, U_roof=0.0), sun=False, people=False)
        rows.append(dict(A_open=A, dev=d, Tz=r["Tz"], Qn=r["Qn"], phi=r["phi"]))
    for N in (200,):
        r = M.solve_zone(WX["Phoenix"], N, "evap_big", z=z, sun=True)
        rows.append(dict(A_open=A, dev=f"evap_big_N{N}_sun", Tz=r["Tz"], Qn=r["Qn"], phi=r["phi"]))
        r = M.solve_zone(WX["Houston"], N, "evap_big", z=z, sun=True)
        rows.append(dict(A_open=A, dev=f"HOU_evap_big_N{N}_sun", Tz=r["Tz"], Qn=r["Qn"], phi=r["phi"]))
lim = pd.DataFrame(rows)
lim.to_csv(OUT / "limits.csv", index=False)
Ts, _, _ = C.evaporative_cooler(WX["Phoenix"]["To"], WX["Phoenix"]["RH"], 0.85)
for d in ("big_nm", "evap_big"):
    s = lim[lim.dev == d]
    say(f"   {d:9s} A=0.001 m2 -> Tz = {s.Tz.iloc[0]:.2f} C ; A=10^4 m2 -> Tz = {s.Tz.iloc[-1]:.2f} C")
say(f"   supply temperature Ts = {Ts:.2f} C; outdoor To = {WX['Phoenix']['To']:.2f} C; "
    f"motor offset P/(rho cp Qs) = {2500/(1.2*1006*2.5):.2f} C")

# ------------------------------------------------------------------ 2. heat budget vs crowd
say("\n[2] Heat & moisture budget, large cooler mode O (kW). ASHRAE-fixed = 75 W sens / 55 W lat per person")
bud = []
for c, w in WX.items():
    for N in (0, 50, 100, 200, 400, 600):
        r = M.solve_zone(w, N, "evap_big")
        b = M.solve_zone(w, N, "none")
        bud.append(dict(city=c, N=N, people_sens=r["G_people_s"] / 1e3, people_lat=r["G_people_l"] / 1e3,
                        roof=r["G_roof"] / 1e3, motor=r["P"] / 1e3, cool_cap=r["cool_cap"] / 1e3,
                        s_pp=r["s"], l_pp=r["l"], Tz=r["Tz"], RHz=r["RHz"], SET=r["SET"],
                        Tz_none=b["Tz"], RH_none=b["RHz"], SET_none=b["SET"], phi=r["phi"],
                        Qn=r["Qn"], tau=r["tau_s"], ashrae_sens=0.075 * N, ashrae_lat=0.055 * N))
bud = pd.DataFrame(bud)
bud.to_csv(OUT / "budget.csv", index=False)
say(bud.round(2).to_string())

# ------------------------------------------------------------------ 3. efficiency vs crowd
say("\n[3] Efficiency vs crowd size")
Ns = np.array([0, 10, 25, 50, 75, 100, 150, 200, 250, 300, 400, 500, 600])
eff = []
for c, w in WX.items():
    base = {N: M.solve_zone(w, N, "none") for N in Ns}
    for d in ("fan", "evap", "evap_big"):
        for mode in (("O", "R") if d != "fan" else ("O",)):
            for N in Ns:
                r = M.solve_zone(w, N, d, mode=mode)
                b = base[N]
                dS = b["SET"] - r["SET"]
                dD = C.dissatisfied_fraction(b["SET"]) - C.dissatisfied_fraction(r["SET"])
                eff.append(dict(city=c, dev=d, mode=mode, N=N, SET_dev=r["SET"], SET_base=b["SET"],
                                dSET=dS, dD=dD, Tz=r["Tz"], RHz=r["RHz"], Tz_base=b["Tz"],
                                P=SC.DEVICES[d]["P"], ok=r["ok"]))
eff = pd.DataFrame(eff)
eff["eta_deg"] = eff.N * eff.dSET / eff.P              # person.degC.h per kWh
eff["eta_D"] = eff.N * eff.dD / eff.P                  # person-comfort-h per kWh
d0 = eff[eff.N == 0][["city", "dev", "mode", "dSET", "dD"]].rename(columns={"dSET": "dSET0", "dD": "dD0"})
eff = eff.merge(d0, on=["city", "dev", "mode"])
eff["eta_deg_old"] = eff.N * eff.dSET0 / eff.P          # bus-stop logic: people don't change the zone
eff["eta_D_old"] = eff.N * eff.dD0 / eff.P
eff.to_csv(OUT / "efficiency.csv", index=False)
say(eff[["city", "dev", "mode", "N", "Tz", "RHz", "SET_base", "SET_dev", "dSET", "dD", "eta_deg", "eta_deg_old", "eta_D", "ok"]].round(3).to_string())

# fine search for peaks & overwhelm
say("\n[3b] Peaks and overwhelm points")
summary = []
for c, w in WX.items():
    set_empty = M.solve_zone(w, 0, "none")["SET"]
    for d in ("fan", "evap", "evap_big"):
        for mode in (("O", "R") if d != "fan" else ("O",)):
            P = SC.DEVICES[d]["P"]
            f = lambda N: M.solve_zone(w, N, d, mode=mode)["SET"] - set_empty
            try:
                N_ow = brentq(f, 0.0, 3000.0, xtol=1.0) if f(0) < 0 < f(3000) else (0.0 if f(0) >= 0 else float("inf"))
            except Exception:
                N_ow = float("nan")
            g = lambda N: -(N * (M.solve_zone(w, N, "none")["SET"] - M.solve_zone(w, N, d, mode=mode)["SET"]) / P)
            grid = np.linspace(0, 1500, 61)
            vals = np.array([-g(N) for N in grid])
            k = int(np.argmax(vals))
            h = lambda N: N * (C.dissatisfied_fraction(M.solve_zone(w, N, "none")["SET"])
                               - C.dissatisfied_fraction(M.solve_zone(w, N, d, mode=mode)["SET"])) / P
            valsD = np.array([h(N) for N in grid])
            kD = int(np.argmax(valsD))
            summary.append(dict(city=c, dev=d, mode=mode, SET_empty_nodevice=set_empty, N_overwhelm=N_ow,
                                N_peak_deg=grid[k], eta_deg_peak=vals[k], peak_at_edge=(k == len(grid) - 1),
                                N_peak_D=grid[kD], eta_D_peak=valsD[kD]))
            say(f"   {c:8s} {d:8s} mode {mode}: SET(empty, no device) = {set_empty:.2f}; "
                f"N_overwhelm(felt) = {N_ow:.0f}; deg-currency peak at N = {grid[k]:.0f}"
                f"{' (edge of grid: no interior peak)' if k == len(grid)-1 else ''}; comfort-currency peak at N = {grid[kD]:.0f}")
summ = pd.DataFrame(summary)
summ.to_csv(OUT / "peaks.csv", index=False)

# closed-form overwhelm (air temperature)
say("\n[3c] Closed-form crowd at which the cooled zone's AIR is back to outdoor temperature (mode O)")
for c, w in WX.items():
    for d in ("evap", "evap_big"):
        N_air, s, cap, Qr = M.overwhelm_N_air(w, d)
        say(f"   {c:8s} {d:8s}: cooling capacity {cap/1e3:.1f} kW, roof {Qr/1e3:.1f} kW, motor {SC.DEVICES[d]['P']:.1f} kW, "
            f"sensible per person at T_out {s:.0f} W -> N_air = {N_air:.0f} "
            f"{'(negative s: crowd never overwhelms air temperature)' if s < 0 else ''}")
        s_ash = 75.0
        say(f"            with ASHRAE fixed 75 W: N_air = {(cap - Qr - SC.DEVICES[d]['P']*1e3)/s_ash:.0f}")

# ------------------------------------------------------------------ 4. ventilation vs evaporation decomposition
say("\n[4] How much of the large cooler's benefit is just its outdoor airflow? (mode O, pad dry eps=0)")
for c, w in WX.items():
    for N in (0, 200, 400):
        b = M.solve_zone(w, N, "none")["SET"]
        full = M.solve_zone(w, N, "evap_big")["SET"]
        dry = M.solve_zone(w, N, "evap_big", eps=0.0)["SET"]
        say(f"   {c:8s} N={N:3d}: dSET full = {b-full:.2f}, airflow-only = {b-dry:.2f} -> ventilation share {100*(b-dry)/(b-full):.0f}%")

# ------------------------------------------------------------------ 5. time constant and surges
say("\n[5] Train surges: ODE vs quasi-steady (large cooler, mode O)")
surge = []
for c, w in WX.items():
    for Nm in (100, 200):
        for Hm in (3, 8, 15):
            t, T, W, N, r0 = M.simulate_surge(w, Nm, Hm, "evap_big")
            H = Hm * 60
            last = t >= t[-1] - 2 * H                      # last two cycles (periodic state)
            # quasi-steady: zone instantly at steady state for N(t)
            Nq = np.linspace(0, 2 * Nm, 13)
            Tq = np.array([M.solve_zone(w, n, "evap_big")["Tz"] for n in Nq])
            Sq = np.array([M.solve_zone(w, n, "evap_big")["SET"] for n in Nq])
            T_qs = np.interp(N, Nq, Tq)
            S_qs = np.interp(N, Nq, Sq)
            # SET along the ODE trajectory, with air speed and radiant temperature recomputed at each point
            S_ode = np.array([M.feel(w, Ti, Wi) for Ti, Wi in zip(T[last][::6], W[last][::6])])
            Nl = N[last][::6]
            pw = lambda x, n: float(np.sum(x * n) / np.sum(n))
            rec = dict(city=c, N_mean=Nm, headway=Hm, tau_s=r0["tau_s"],
                       T_ode_min=T[last].min(), T_ode_max=T[last].max(),
                       T_qs_min=T_qs[last].min(), T_qs_max=T_qs[last].max(),
                       T_steady_mean=r0["Tz"], SET_steady_mean=r0["SET"],
                       SETpw_ode=pw(S_ode, Nl), SETpw_qs=pw(S_qs[last][::6], Nl),
                       SET_at_4over3=float(np.interp(4 / 3 * Nm, Nq, Sq)))
            surge.append(rec)
            if c == "Houston" and Nm == 200 and Hm == 8:
                pd.DataFrame(dict(t=t, T=T, W=W, N=N, T_qs=T_qs)).to_csv(OUT / "surge_trace.csv", index=False)
            say("   " + ", ".join(f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}" for k, v in rec.items()))
pd.DataFrame(surge).to_csv(OUT / "surge.csv", index=False)

# ------------------------------------------------------------------ 6. sensitivity (one-at-a-time)
say("\n[6] One-at-a-time sensitivity of dSET at N=200 (large cooler, mode O)")
base_z = M.ZONE
tests = [("C_w single-sided wind coeff", "C_w", 0.01, 0.05),
         ("Cd discharge coeff", "Cd", 0.5, 0.65),
         ("Opening area A_open (m2)", "A_open", 20.0, 80.0),
         ("Wind reduction factor", "wind_factor", 0.4, 1.0),
         ("Roof alpha/h_o (light->dark)", "aho", 0.013, 0.052),
         ("Roof U (insulated->bare)", "U_roof", 0.5, 7.0),
         ("Metabolic rate (met)", "met", 1.0, 1.4),
         ("Ceiling view factor", "F_ceil", 0.1, 0.3)]
sens = []
for c, w in WX.items():
    def dS(z, N=200):
        return M.solve_zone(w, N, "none", z=z)["SET"] - M.solve_zone(w, N, "evap_big", z=z)["SET"]
    y0 = dS(base_z)
    for lab, key, lo, hi in tests:
        ylo = dS(dict(base_z, **{key: lo}))
        yhi = dS(dict(base_z, **{key: hi}))
        p0 = base_z[key]
        el = ((yhi - ylo) / (hi - lo)) * (p0 / y0)
        sens.append(dict(city=c, param=lab, lo=lo, hi=hi, y_lo=ylo, y_hi=yhi, y0=y0, elasticity=el))
    # cooler airflow +-30 %
    for fac in (0.7, 1.3):
        SC.DEVICES["tmp"] = dict(SC.DEVICES["evap_big"], Q=2.5 * fac)
    SC.DEVICES["lo"] = dict(SC.DEVICES["evap_big"], Q=1.75)
    SC.DEVICES["hi"] = dict(SC.DEVICES["evap_big"], Q=3.25)
    ylo = M.solve_zone(w, 200, "none")["SET"] - M.solve_zone(w, 200, "lo")["SET"]
    yhi = M.solve_zone(w, 200, "none")["SET"] - M.solve_zone(w, 200, "hi")["SET"]
    sens.append(dict(city=c, param="Cooler airflow Qs (m3/s)", lo=1.75, hi=3.25, y_lo=ylo, y_hi=yhi, y0=y0,
                     elasticity=((yhi - ylo) / 1.5) * (2.5 / y0)))
    cal_lo = dict(M.CAL, eps_evap=0.70); cal_hi = dict(M.CAL, eps_evap=0.90)
    ylo = M.solve_zone(w, 200, "none")["SET"] - M.solve_zone(w, 200, "evap_big", cal=cal_lo)["SET"]
    yhi = M.solve_zone(w, 200, "none")["SET"] - M.solve_zone(w, 200, "evap_big", cal=cal_hi)["SET"]
    sens.append(dict(city=c, param="Pad efficiency eps", lo=0.7, hi=0.9, y_lo=ylo, y_hi=yhi, y0=y0,
                     elasticity=((yhi - ylo) / 0.2) * (0.85 / y0)))
sens = pd.DataFrame(sens)
sens.to_csv(OUT / "sensitivity.csv", index=False)
say(sens.round(3).to_string())

# ------------------------------------------------------------------ 7. cross-ventilated variant
say("\n[7] Same station but open at both ends (cross-ventilated) vs single-sided, N=200, large cooler")
for c, w in WX.items():
    for kind in ("single", "cross"):
        z = dict(M.ZONE, kind=kind)
        r = M.solve_zone(w, 200, "evap_big", z=z); b = M.solve_zone(w, 200, "none", z=z)
        say(f"   {c:8s} {kind:6s}: Qn = {r['Qn']:.2f} m3/s, phi = {r['phi']:.2f}, tau = {r['tau_s']:.0f} s, dSET = {b['SET']-r['SET']:.2f}")

# ------------------------------------------------------------------ 8. body heat split check vs table
say("\n[8] Per-person split from the two-node model (v=0.2, RH 50 %, tr=T, met 1.1, clo 0.35)")
for T in (24, 26, 28, 30, 32, 34, 36, 38, 40, 42):
    s, l = M.body(T, T, 0.2, 50)
    say(f"   T={T:2d} C: sensible {s:6.1f} W, latent {l:6.1f} W, total {s+l:6.1f} W")

(OUT / "T11_log.txt").write_text("\n".join(LOG))
