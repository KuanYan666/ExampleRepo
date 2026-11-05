"""
T04 - Frost on the freezer-case coil and the optimal defrost interval.

Model in one breath
-------------------
  frost stock    dm_f/dt = beta * m_inf * (W_store - W_case)          [kg/h]
  frost -> blockage b = m_f / m_cap  -> airflow V(b) (fan meets coil)  [-]
         -> frost layer thickness delta -> extra conduction resistance
  airflow + UA -> evaporating temperature T_e needed to keep the same load Q
  T_e -> COP (fixed fraction of Carnot) -> compressor power P(m_f)
  penalty power  dP(t) = P(m_f(t)) - P(0)
  each defrost   E_def = heater energy + electricity to re-cool what the heater warmed
  renewal-reward g(T) = [E_def(T) + int_0^T dP dt] / (T + t_down(T))   -> minimise over T

Units: kW, kJ, kWh, h, degC, kg.  Everything tagged ASSUMED / VERIFIED in the memo.
Run:  python3 T04_frost_model.py      (writes figures to ../figs and numbers to stdout)
"""
import os, sys
import numpy as np
from scipy.integrate import solve_ivp, cumulative_trapezoid
from scipy.optimize import brentq

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(S, "himcm_b"))
import core as C  # team psychrometrics (humidity ratio)

FIG = os.path.join(HERE, "..", "figs")
os.makedirs(FIG, exist_ok=True)

CP, H_SUB, H_IF, C_ICE = 1.006, 2835.0, 334.0, 2.05   # kJ/kgK, kJ/kg, kJ/kg, kJ/kgK

BASE = dict(
    T_store=24.0, RH_store=55.0,      # team base case (store aisle)
    T_case=-18.0, RH_case=90.0,       # team base case (air inside case = air entering coil)
    Q_total=2.5, infil_share=0.75,    # team: 2.5 kW case, 75% infiltration
    beta=1.0,                         # share of infiltrated water that ends up on the coil
    COP0=1.7, T_cond=35.0,            # team COP at clean coil; condensing temp
    approach=6.0,                     # T_case - T_evap, clean coil (Tyler L6FA: -10F air / -20F suction = 5.6 K)
    dT_air=4.0,                       # air temperature drop across clean coil
    V0_frac=0.70,                     # clean operating flow / fan free-delivery flow
    r_c=0.50,                         # coil share of clean-system pressure drop
    n_h=0.6,                          # air-side h ~ flow^0.6
    A_coil=30.0, gap=6.2e-3,          # air-side area m2, fin gap m (4 fins/inch minus fin thickness)
    airflow_end=620.0 / 720.0,        # Tyler L6FA primary air: 620 fpm before vs 720 fpm after defrost
    T_cal=12.0,                       # ...measured at end of a 12 h cycle (2 defrosts/day) at 75F/55%RH
    P_h=5.4,                          # kW heater (Tyler L6FA 8 ft: 15.0 A, 208 V 3-phase)
    C_coil=25.0,                      # kJ/K coil metal heat capacity
    eta_d=0.40,                       # share of heater energy that reaches coil + frost
    psi=0.30,                         # share of the stray defrost heat that escapes to the store
    T_term=12.8,                      # 55F termination (Tyler L6FA)
    t_drip=10.0 / 60.0,               # h, drip / run-off time (Hillphoenix 8-10 min)
    failsafe=40.0 / 60.0,             # h, Tyler L6FA 40 min electric defrost time
)


class Case:
    """All derived quantities for one parameter set."""

    def __init__(self, **kw):
        p = dict(BASE); p.update(kw); self.p = p
        self.W_c = C.W_from_RH(p["T_case"], p["RH_case"])
        # infiltration mass flow fixed by the air curtain (aerodynamics), computed at the team base case
        W_b = C.W_from_RH(p["T_store"], 55.0) if "W_base" not in kw else kw["W_base"]
        dh_b = CP * (p["T_store"] - p["T_case"]) + (W_b - self.W_c) * H_SUB
        self.m_inf = p["Q_total"] * p["infil_share"] / dh_b            # kg/s
        self.Q_other = p["Q_total"] * (1 - p["infil_share"])           # kW
        # clean coil design (fixed hardware, sized at base load)
        self.mdot0 = p["Q_total"] / (CP * p["dT_air"])                 # kg/s air through coil
        eps0 = p["dT_air"] / p["approach"]
        self.NTU0 = -np.log(1 - eps0)
        self.UA0 = self.NTU0 * self.mdot0 * CP                         # kW/K
        Te0 = p["T_case"] - p["approach"]
        self.eta2 = p["COP0"] / self.carnot(Te0)                       # second-law efficiency
        # fan-system normalisation
        x0 = p["V0_frac"] ** 2
        self.dp0 = x0 / (1 - x0)
        self.x0 = x0
        self.set_store(p["RH_store"], p["T_store"])
        self.calibrate()

    # ---------- store state ----------
    def set_store(self, RH, T=None):
        T = self.p["T_store"] if T is None else T
        self.W_s = C.W_from_RH(T, RH)
        dh = CP * (T - self.p["T_case"]) + (self.W_s - self.W_c) * H_SUB
        self.Q = self.Q_other + self.m_inf * dh                         # kW load at this humidity
        self.rate = self.p["beta"] * self.m_inf * (self.W_s - self.W_c) * 3600.0   # kg/h frost
        return self

    def carnot(self, Te):
        return (Te + 273.15) / (self.p["T_cond"] - Te)

    # ---------- frost -> airflow, UA, T_e, power ----------
    def flow_ratio(self, sigma):
        x = self.dp0 / (self.dp0 + (1 - self.p["r_c"]) + self.p["r_c"] / sigma ** 2)
        return np.sqrt(x / self.x0)

    def calibrate(self):
        """m_cap: frost mass that would fill the fin gaps. Chosen so that airflow is
        down to 620/720 after T_cal hours at the manufacturer's rating (75F/55%RH)."""
        target = self.p["airflow_end"]
        sig = brentq(lambda s: self.flow_ratio(s) - target, 0.05, 1.0)
        W_rate = C.W_from_RH(23.9, 55.0)
        rate_rating = self.p["beta"] * self.m_inf * (W_rate - self.W_c) * 3600.0
        self.m_cap = rate_rating * self.p["T_cal"] / (1 - sig)
        self.rho_f = self.m_cap / (self.p["A_coil"] * self.p["gap"] / 2)        # implied frost density
        r = self.rho_f
        self.k_f = 0.024248 + 0.731e-3 * r + 0.1183e-5 * r ** 2                   # Yonko & Sepsy (1967)

    def state(self, m):
        """Return airflow ratio, UA ratio, T_e, COP, power for frost mass m (array ok)."""
        p = self.p
        b = np.clip(np.asarray(m, float) / self.m_cap, 0, 0.95)
        sigma = 1 - b
        fr = self.flow_ratio(sigma)
        mdot = self.mdot0 * fr
        delta = b * p["gap"] / 2                                       # m frost thickness
        R_air = (1 / self.UA0) * fr ** (-p["n_h"])                     # K/kW
        R_fr = delta / (self.k_f * p["A_coil"]) * 1000.0               # K/kW
        UA = 1 / (R_air + R_fr)
        eps = 1 - np.exp(-UA / (mdot * CP))
        Te = p["T_case"] - self.Q / (eps * mdot * CP)
        cop = self.eta2 * self.carnot(Te)
        P = self.Q / cop
        return dict(flow=fr, UA=UA / self.UA0, Te=Te, cop=cop, P=P, b=b)

    def dP(self, m):
        return self.state(m)["P"] - self.state(0.0)["P"]

    # ---------- one defrost ----------
    def defrost(self, m, Te_end):
        p = self.p
        E_coil = p["C_coil"] * (p["T_term"] - Te_end)                  # kJ
        E_frost = m * (C_ICE * (0 - Te_end) + H_IF)                    # kJ
        E_h = (E_coil + E_frost) / p["eta_d"]                          # kJ heater
        stray = (1 - p["eta_d"]) * E_h
        recool = (E_coil + (1 - p["psi"]) * stray) / p["COP0"]         # kJ electricity
        t_h = E_h / p["P_h"] / 3600.0                                  # h
        return dict(E_h=E_h / 3600, E_recool=recool / 3600, E=(E_h + recool) / 3600,
                    t_h=t_h, t_down=t_h + p["t_drip"], E_frost=E_frost / 3600, E_coil=E_coil / 3600)

    # ---------- renewal-reward ----------
    def curve(self, T=np.linspace(0.5, 48, 951)):
        m = self.rate * T
        st = self.state(m)
        dP = st["P"] - self.state(0.0)["P"]
        # integral of dP from 0 to T
        tt = np.concatenate([[0], T]); dd = np.concatenate([[0], dP])
        I = cumulative_trapezoid(dd, tt, initial=0)[1:]
        d = self.defrost(m, st["Te"])
        num = d["E"] + I
        g = num / (T + d["t_down"])                                    # kW average penalty
        marg = np.gradient(num, T) / np.gradient(T + d["t_down"], T)   # marginal cost rate
        return dict(T=T, m=m, dP=dP, I=I, g=g, marg=marg, d=d, st=st)

    def optimum(self, **kw):
        c = self.curve(**kw)
        i = int(np.argmin(c["g"]))
        return c["T"][i], c["g"][i], c, i


def daily(case, T):
    """kWh/day split at a given interval T (h)."""
    m = case.rate * T
    st = case.state(m)
    d = case.defrost(m, st["Te"])
    tt = np.linspace(0, T, 400)
    I = np.trapezoid(case.dP(case.rate * tt), tt)
    n = 24.0 / (T + d["t_down"])
    p = case.p
    per_kJ = 1 / p["eta_d"] + (1 - p["eta_d"]) * (1 - p["psi"]) / (p["eta_d"] * p["COP0"])   # kWh_e per kWh_th
    melt = n * d["E_frost"] * per_kJ                       # scales with frost mass: unavoidable per kg of water
    return dict(n=n, melt=melt, overhead=n * d["E"] - melt,
                degr=n * I, total=n * (d["E"] + I), t_h=d["t_h"], m=m,
                base=24 * case.state(0.0)["P"])


if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    BLUE, ORANGE, AQUA, VIOLET, RED = "#2a78d6", "#eb6834", "#1baf7a", "#6250d6", "#e34948"
    INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                         "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True,
                         "grid.color": GRID, "grid.linewidth": 0.7, "axes.spines.top": False,
                         "axes.spines.right": False, "lines.linewidth": 2})

    cs = Case()
    print("=" * 74); print("T04 BASE CASE (store 24 C / 55 %RH, case -18 C)"); print("=" * 74)
    print(f"W_store {cs.W_s*1000:.2f} g/kg, W_case {cs.W_c*1000:.3f} g/kg, m_inf {cs.m_inf:.4f} kg/s")
    print(f"frost growth rate      : {cs.rate:.3f} kg/h = {cs.rate*24:.1f} kg/day")
    print(f"clean coil: air {cs.mdot0:.3f} kg/s, UA0 {cs.UA0:.3f} kW/K, NTU0 {cs.NTU0:.2f}, "
          f"eta_II {cs.eta2:.3f}, Carnot(Te0) {cs.carnot(-24):.2f}")
    print(f"calibrated m_cap {cs.m_cap:.1f} kg -> implied frost density {cs.rho_f:.0f} kg/m3, "
          f"k_f {cs.k_f:.3f} W/mK")
    s0 = cs.state(0.0)
    print(f"clean: Te {s0['Te']:.2f} C, COP {s0['cop']:.3f}, P {s0['P']:.3f} kW")
    for h in (4, 8, 12, 16, 20, 24):
        s = cs.state(cs.rate * h)
        print(f"  t={h:2d} h  m_f={cs.rate*h:5.1f} kg  airflow {100*s['flow']:5.1f}%  UA {100*s['UA']:5.1f}%"
              f"  Te {s['Te']:6.2f} C  COP {s['cop']:.3f}  dP {1000*(s['P']-s0['P']):6.1f} W")
    Ts, gs, c, i = cs.optimum()
    d = c["d"]
    print(f"\nOPTIMUM T* = {Ts:.2f} h  ({24/(Ts+d['t_down'][i]):.2f} defrosts/day), "
          f"average penalty {1000*gs:.0f} W")
    print(f"  at T*: frost {c['m'][i]:.1f} kg, heater {d['E_h'][i]:.2f} kWh, recool {d['E_recool'][i]:.2f} kWh, "
          f"heater on {60*d['t_h'][i]:.0f} min, degradation integral {c['I'][i]:.2f} kWh, dP(T*) {1000*c['dP'][i]:.0f} W")
    print(f"  marginal rate at T* {1000*c['marg'][i]:.0f} W vs average {1000*gs:.0f} W (should match)")
    lo = c["T"][c["g"] <= 1.02 * gs]
    print(f"  flat bottom: within +2% of optimum for T in [{lo.min():.1f}, {lo.max():.1f}] h")
    for Tfix in (6, 8, 12, Ts, 24):
        dd = daily(cs, Tfix)
        print(f"  T={Tfix:5.2f} h: {dd['n']:.2f}/day melt {dd['melt']:.2f}  overhead {dd['overhead']:.2f}  "
              f"degr {dd['degr']:.2f}  TOTAL penalty {dd['total']:.2f} kWh/day  (heater {60*dd['t_h']:.0f} min,"
              f" frost {dd['m']:.1f} kg)  base compressor {dd['base']:.1f}")

    # fail-safe constraint: heater must clear the frost within the maker's time limit
    T_max = c["T"][np.where(d["t_h"] <= cs.p["failsafe"])[0].max()]
    jm = np.argmin(abs(c["T"] - T_max))
    print(f"  heater time limit {60*cs.p['failsafe']:.0f} min reached at T = {T_max:.1f} h "
          f"-> constrained optimum {min(Ts, T_max):.1f} h, penalty {1000*c['g'][jm]:.0f} W "
          f"(+{100*(c['g'][jm]/gs-1):.1f}% vs unconstrained)")

    # cost per kg of water: freeze it on (compressor) + melt it off (heater + re-cool)
    per_kJ = 1 / cs.p["eta_d"] + (1 - cs.p["eta_d"]) * (1 - cs.p["psi"]) / (cs.p["eta_d"] * cs.p["COP0"])
    e_on = H_SUB / cs.p["COP0"] / 3600; e_off = (H_IF + C_ICE * 25) * per_kJ / 3600
    e_fix = cs.p["C_coil"] * (cs.p["T_term"] + 25) * (per_kJ + 1 / cs.p["COP0"]) / 3600
    print(f"  per kg of water: compressor {e_on:.3f} kWh to freeze on, defrost {e_off:.3f} kWh to melt off "
          f"(+{100*e_off/e_on:.0f}%); fixed overhead per defrost K = {e_fix:.2f} kWh")
    for Tq in (6.0, 12.0, Ts):
        dq = cs.defrost(cs.rate * Tq, cs.state(cs.rate * Tq)["Te"]); tq = np.linspace(0, Tq, 300)
        Iq = np.trapezoid(cs.dP(cs.rate * tq), tq); totq = Tq + dq["t_down"]
        print(f"  effective COP incl. defrost at T={Tq:.1f} h: {cs.Q*totq/(s0['P']*totq + dq['E'] + Iq):.3f}")

    # sawtooth swing and effective COP
    s_end = cs.state(cs.rate * Ts)
    tot = Ts + d["t_down"][i]
    E_cyc = s0["P"] * tot + d["E"][i] + c["I"][i]
    cop_eff = cs.Q * tot / E_cyc
    print(f"\nSAWTOOTH: COP {s0['cop']:.3f} (clean) -> {s_end['cop']:.3f} at T* "
          f"({100*(1-s_end['cop']/s0['cop']):.1f}% drop); airflow -> {100*s_end['flow']:.0f}%")
    print(f"  cycle-average effective COP incl. defrost = {cop_eff:.3f} "
          f"({100*(1-cop_eff/s0['cop']):.1f}% below clean-coil COP)")

    # ------------------------------------------------------------- FIG 1 sawtooth (ODE, product temp)
    tau_p, T_peak, tau_air = 67 / 60, -2.0, 10 / 60       # h, C, h  (team product tau; ASSUMED defrost air)
    t_cycle = Ts + d["t_down"][i]; th = d["t_h"][i]; tdn = d["t_down"][i]
    ncyc = 3

    def case_air(t):
        tc = t % t_cycle
        if tc < Ts:
            # recovering after previous defrost (exponential pull-down)
            prev_peak = cs.p["T_case"] + (T_peak - cs.p["T_case"]) * (1 - np.exp(-tdn / tau_air))
            return cs.p["T_case"] + (prev_peak - cs.p["T_case"]) * np.exp(-tc / tau_air) if t >= t_cycle else cs.p["T_case"]
        return cs.p["T_case"] + (T_peak - cs.p["T_case"]) * (1 - np.exp(-(tc - Ts) / tau_air))

    def rhs(t, y):
        m, Tp = y
        tc = t % t_cycle
        dm = cs.rate if tc < Ts else 0.0
        return [dm, (case_air(t) - Tp) / tau_p]

    # integrate piecewise, resetting frost at each defrost end
    tt_all, m_all, Tp_all = [], [], []
    y = [0.0, -18.0]
    for k in range(ncyc):
        t0 = k * t_cycle
        sol = solve_ivp(rhs, (t0, t0 + Ts), y, max_step=0.02, rtol=1e-8)
        tt_all.append(sol.t); m_all.append(sol.y[0]); Tp_all.append(sol.y[1])
        y = [sol.y[0, -1], sol.y[1, -1]]
        # defrost: frost melts linearly over heater time
        sol2 = solve_ivp(lambda t, yy: [-y[0] / th if (t - t0 - Ts) < th else 0.0,
                                         (case_air(t) - yy[1]) / tau_p],
                         (t0 + Ts, t0 + t_cycle), y, max_step=0.01, rtol=1e-8)
        tt_all.append(sol2.t); m_all.append(np.maximum(sol2.y[0], 0)); Tp_all.append(sol2.y[1])
        y = [0.0, sol2.y[1, -1]]
    tt = np.concatenate(tt_all); mm = np.concatenate(m_all); Tp = np.concatenate(Tp_all)
    in_def = (tt % t_cycle) >= Ts - 1e-9
    stt = cs.state(np.where(in_def, 0, mm))
    cop_t = np.where(in_def, 0.0, stt["cop"])
    print(f"  product temperature peak during defrost: {Tp.max():.1f} C (rise {Tp.max()+18:.1f} K)")

    def product_rise(t_down):
        f = lambda t, y: [(cs.p["T_case"] + (T_peak - cs.p["T_case"]) * (1 - np.exp(-t / tau_air)) - y[0]) / tau_p]
        return solve_ivp(f, (0, t_down), [cs.p["T_case"]], rtol=1e-8).y[0, -1] - cs.p["T_case"]
    print("  interval -> heater minutes, food rise per defrost (indicator)")
    for Tq in (6, 8, 12, 18, 24):
        dq = cs.defrost(cs.rate * Tq, cs.state(cs.rate * Tq)["Te"])
        print(f"    T={Tq:2d} h: heater {60*dq['t_h']:4.0f} min, food +{product_rise(dq['t_down']):.1f} K, "
              f"{24/(Tq+dq['t_down']):.2f} events/day")

    fig, ax = plt.subplots(3, 1, figsize=(9, 8.2), sharex=True)
    ax[0].plot(tt, mm, color=BLUE)
    ax[0].set_ylabel("Frost on coil (kg)")
    ax[0].set_title("Three defrost cycles at the optimal interval (store 24 °C, 55 % RH)", loc="left",
                    fontsize=11, color=INK)
    ax[1].plot(tt, cop_t, color=ORANGE, label="instantaneous COP")
    ax[1].axhline(cop_eff, color=INK2, ls="--", lw=1.3)
    ax[1].text(0.2, cop_eff - 0.17, f"cycle average incl. defrost = {cop_eff:.2f}", color=INK2, fontsize=9)
    ax[1].text(0.2, s0["cop"] + 0.06, f"clean coil = {s0['cop']:.2f}", color=INK2, fontsize=9)
    ax[1].set_ylim(-0.1, 2.05)
    ax[1].set_ylabel("COP (heat removed\nper unit electricity)")
    for k in range(ncyc):
        a = k * t_cycle + Ts
        for axx in ax:
            axx.axvspan(a, a + tdn, color=RED, alpha=0.10, lw=0)
    ax[1].text(Ts + tdn + 0.6, 0.35, "defrost: heater on,\nno cooling", ha="left", fontsize=8, color=RED)
    ax[2].plot(tt, Tp, color=AQUA)
    ax[2].set_ylabel("Food temperature (°C)")
    ax[2].set_xlabel("Time (hours)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "T04_sawtooth.png"), dpi=150); plt.close(fig)

    # zoom on the slow decline of COP between defrosts
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    hh = np.linspace(0, 30, 301)
    stz = cs.state(cs.rate * hh)
    ax[0].plot(hh, 100 * stz["flow"], color=BLUE, label="airflow through coil")
    ax[0].plot(hh, 100 * stz["UA"], color=AQUA, label="coil conductance UA")
    ax[0].plot(hh, 100 * stz["cop"] / s0["cop"], color=ORANGE, label="COP")
    ax[0].axvline(cs.p["T_cal"], color=INK2, lw=1, ls=":")
    ax[0].plot([cs.p["T_cal"]], [100 * cs.p["airflow_end"]], "o", color=INK, ms=7)
    ax[0].annotate("calibration point:\nTyler L6FA 620/720 fpm", (cs.p["T_cal"], 100 * cs.p["airflow_end"]),
                   xytext=(1.0, 52), fontsize=8, color=INK2, arrowprops=dict(arrowstyle="-", color=INK2))
    ax[0].set_xlabel("Hours since last defrost"); ax[0].set_ylabel("% of clean-coil value")
    ax[0].legend(fontsize=8, loc="lower left", frameon=False)
    ax[0].set_title("What frost does to the coil", loc="left", fontsize=11)
    ax[1].plot(hh, 1000 * (stz["P"] - s0["P"]), color=VIOLET)
    ax[1].set_xlabel("Hours since last defrost"); ax[1].set_ylabel("Extra compressor power (W)")
    ax[1].set_title("The penalty grows faster and faster", loc="left", fontsize=11)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "T04_degradation.png"), dpi=150); plt.close(fig)

    # ------------------------------------------------------------- FIG 2 average cost vs T
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    sel = c["T"] <= 30
    ax.plot(c["T"][sel], 1000 * c["g"][sel], color=BLUE, label="average penalty g(T)  (cost per hour of whole cycle)")
    ax.plot(c["T"][sel], 1000 * c["marg"][sel], color=ORANGE, label="marginal penalty  (cost of running one more hour)")
    ax.plot([Ts], [1000 * gs], "o", color=INK, ms=8, zorder=5)
    ax.annotate(f"optimum T* = {Ts:.1f} h\n(lines cross here)\n{1000*gs:.0f} W average", (Ts, 1000 * gs),
                xytext=(Ts + 2.5, 170), fontsize=9, arrowprops=dict(arrowstyle="-", color=INK2))
    ax.axvspan(8, 12, color=GRID, alpha=0.6, lw=0)
    ax.text(10, 30, "maker's\nschedule\n2-3/day", ha="center", fontsize=8, color=INK2)
    ax.set_ylim(0, 900)
    ax.axvline(T_max, color=RED, lw=1.2, ls="--")
    ax.text(T_max - 0.3, 860, "heater needs > 40 min\n(maker's limit) beyond here →", ha="right", va="top", fontsize=8, color=RED)
    ax.set_xlabel("Defrost interval T (hours of cooling between defrosts)")
    ax.set_ylabel("Penalty power (W)")
    ax.set_title("Defrost too often: heater overhead dominates.  Too rarely: frost penalty explodes.",
                 loc="left", fontsize=10.5)
    ax.legend(fontsize=8.5, frameon=False, loc="center right")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "T04_optimum.png"), dpi=150); plt.close(fig)

    # ------------------------------------------------------------- FIG 3 humidity sweep
    RHs = np.arange(30, 71, 2.5)
    rows = []
    for RH in RHs:
        cc = Case(RH_store=RH)
        T_, g_, cv, j = cc.optimum()
        dd = daily(cc, T_); d6 = daily(cc, 6.0); d8 = daily(cc, 8.0); d12 = daily(cc, 12.0)
        Tc_ = cv["T"][np.where(cv["d"]["t_h"] <= cc.p["failsafe"])[0].max()]
        rows.append((RH, cc.rate, T_, 1000 * g_, cv["m"][j], dd["total"], dd["melt"], dd["overhead"], dd["degr"],
                     d6["total"], d8["total"], d12["total"], 60 * dd["t_h"], dd["base"], min(T_, Tc_),
                     daily(cc, min(T_, Tc_))["total"]))
    R = np.array(rows)
    print("\nHUMIDITY SWEEP (24 C store)")
    print(" RH%  frost kg/h   T*h  defr/day  m* kg  pen kWh/d (melt/ovh/degr)   6h-timer  8h  12h  heater-min  base kWh/d")
    for r in R:
        print(f" {r[0]:4.1f}  {r[1]:6.3f}  {r[2]:6.2f}  {24/(r[2]+r[12]/60+1/6):5.2f}  {r[4]:6.1f}   "
              f"{r[5]:5.2f} ({r[6]:.2f}/{r[7]:.2f}/{r[8]:.2f})   {r[9]:5.2f} {r[10]:5.2f} {r[11]:5.2f}   {r[12]:5.0f}   {r[13]:.1f}")
    print(" RH%  constrained T (heater <= 40 min)  penalty kWh/day")
    for r in R[::2]:
        print(f" {r[0]:4.1f}   T_c = {r[14]:5.2f} h   {r[15]:.2f} kWh/day  (unconstrained {r[5]:.2f})")
    # season mismatch: timer tuned for humid summer (65%) used in dry winter (30%)
    cw = Case(RH_store=30.0); Ts65 = Case(RH_store=65.0).optimum()[0]
    for lab, Tq in [("summer-optimal timer", Ts65), ("worst-case 6 h timer", 6.0)]:
        print(f"  winter (30% RH) with {lab} T={Tq:.1f} h: {daily(cw, Tq)['total']:.2f} kWh/day vs optimum "
              f"{daily(cw, Case(RH_store=30.0).optimum()[0])['total']:.2f}")
    ok = R[:, 0] >= 35
    slope = np.polyfit(np.log(R[ok, 1]), np.log(R[ok, 2]), 1)[0]
    slope_m = np.polyfit(np.log(R[ok, 1]), np.log(R[ok, 4]), 1)[0]
    print(f"log-log slope: T* ~ (frost rate)^{slope:.2f};  optimal frost mass m* ~ (frost rate)^{slope_m:.2f}")

    fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.2))
    ax[0].plot(R[:, 0], R[:, 2], color=BLUE, marker="o", ms=4, label="energy optimum T*")
    ax[0].plot(R[:, 0], R[:, 14], color=ORANGE, marker="s", ms=4, label="T* capped by 40-min heater limit")
    ax[0].legend(fontsize=8, frameon=False, loc="upper right")
    ax[0].set_xlabel("Store relative humidity at 24 °C (%)")
    ax[0].set_ylabel("Optimal defrost interval T* (h)")
    ax[0].set_title("Wetter store → defrost sooner", loc="left", fontsize=11)
    for RHm in (40, 55, 65):
        j = np.argmin(abs(R[:, 0] - RHm))
        ax[0].annotate(f"{R[j,2]:.1f} h", (R[j, 0], R[j, 2]), xytext=(4, 6), textcoords="offset points", fontsize=8.5)
    w = 1.6
    ax[1].bar(R[:, 0], R[:, 6], width=w, color=BLUE, label="melting the frost (fixed by humidity)")
    ax[1].bar(R[:, 0], R[:, 7], bottom=R[:, 6], width=w, color=AQUA, label="per-defrost overhead (coil warm-up)")
    ax[1].bar(R[:, 0], R[:, 8], bottom=R[:, 6] + R[:, 7], width=w, color=ORANGE, label="frosted-coil penalty")
    ax[1].plot(R[:, 0], R[:, 9], color=INK2, ls="--", lw=1.5, label="fixed 6 h timer (total)")
    ax[1].set_xlabel("Store relative humidity at 24 °C (%)")
    ax[1].set_ylabel("Frost-related electricity (kWh/day)")
    ax[1].set_title("Daily frost cost at the optimum", loc="left", fontsize=11)
    ax[1].legend(fontsize=8, frameon=False, loc="upper left")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "T04_humidity.png"), dpi=150); plt.close(fig)

    # ------------------------------------------------------------- FIG 4: varying store humidity, timer vs demand
    # store is open 08-22 (doors bring in humid air: RH 60%), closed at night (RH 40%) -- ASSUMED profile
    def RH_t(t):
        h = t % 24
        return 60.0 if 8 <= h < 22 else 40.0
    cv = Case()
    W_open, W_closed = C.W_from_RH(24, 60), C.W_from_RH(24, 40)

    def simulate(rule, param, days=60):
        """rule='timer' (param=T hours) or 'demand' (param=frost mass kg). Returns penalty kWh/day."""
        t, m, E, n = 0.0, 0.0, 0.0, 0
        dt = 2 / 60
        Pclean = {RH: Case(RH_store=RH).state(0.0)["P"] for RH in (40.0, 60.0)}
        cases = {RH: Case(RH_store=RH) for RH in (40.0, 60.0)}
        since = 0.0
        while t < 24 * days:
            RH = RH_t(t); cc = cases[RH]
            m += cc.rate * dt
            E += (cc.state(m)["P"] - Pclean[RH]) * dt
            t += dt; since += dt
            fire = (since >= param) if rule == "timer" else (m >= param)
            if fire:
                st = cc.state(m); dd = cc.defrost(m, st["Te"])
                E += dd["E"]; t += dd["t_down"]; m = 0.0; since = 0.0; n += 1
        return E / days, n / days
    Tb, _, cb, jb = Case(RH_store=50).optimum()
    m_star = cb["m"][jb]
    res = {}
    for lab, rule, par in [("timer 6 h", "timer", 6.0), ("timer 8 h", "timer", 8.0), ("timer 12 h", "timer", 12.0),
                           (f"timer T*={Tb:.1f} h", "timer", Tb), (f"demand m*={m_star:.1f} kg", "demand", m_star)]:
        res[lab] = simulate(rule, par)
        print(f"  day/night humidity: {lab:22s} penalty {res[lab][0]:.2f} kWh/day, {res[lab][1]:.2f} defrosts/day")
    # brute-force best demand threshold
    best = min(((simulate("demand", mm_)[0], mm_) for mm_ in np.arange(8, 32.1, 2.0)))
    print(f"  best demand threshold {best[1]:.1f} kg -> {best[0]:.2f} kWh/day")

    # ------------------------------------------------------------- tornado
    base_T, base_g, _, _ = Case().optimum()
    tests = [("eta_d", 0.30, 0.50, "defrost efficiency η_d"), ("psi", 0.0, 0.6, "heat escaping to store ψ"),
             ("C_coil", 15.0, 40.0, "coil heat capacity (kJ/K)"), ("T_cal", 8.0, 16.0, "calibration hour"),
             ("airflow_end", 0.80, 0.92, "airflow left at calibration"), ("r_c", 0.3, 0.7, "coil share of pressure drop"),
             ("V0_frac", 0.6, 0.8, "fan operating point"), ("A_coil", 20.0, 45.0, "coil area (m²)"),
             ("COP0", 1.4, 2.0, "clean COP"), ("approach", 5.0, 8.0, "coil approach (K)"),
             ("beta", 0.7, 1.0, "share of water reaching coil β")]
    tor = []
    for k, lo_, hi_, lab in tests:
        a = Case(**{k: lo_}).optimum()[0]; b = Case(**{k: hi_}).optimum()[0]
        tor.append((lab, a, b, lo_, hi_))
    tor.sort(key=lambda r: abs(r[2] - r[1]))
    print("\nTORNADO on T* (base %.2f h)" % base_T)
    for r in tor:
        print(f"  {r[0]:32s} {r[3]:>6} -> {r[1]:6.2f} h   {r[4]:>6} -> {r[2]:6.2f} h")
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    for y_, r in enumerate(tor):
        lo_v, hi_v = r[1], r[2]
        ax.barh(y_, lo_v - base_T, left=base_T, color=BLUE, height=0.6)
        ax.barh(y_, hi_v - base_T, left=base_T, color=ORANGE, height=0.6)
        ax.text(min(lo_v, hi_v) - 0.15, y_, f"{r[3] if lo_v < hi_v else r[4]}", ha="right", va="center", fontsize=7.5, color=INK2)
        ax.text(max(lo_v, hi_v) + 0.15, y_, f"{r[4] if lo_v < hi_v else r[3]}", ha="left", va="center", fontsize=7.5, color=INK2)
    ax.set_yticks(range(len(tor))); ax.set_yticklabels([r[0] for r in tor], fontsize=8.5)
    ax.axvline(base_T, color=INK, lw=1)
    ax.set_xlabel("Optimal defrost interval T* (h)")
    ax.set_title(f"Which assumptions move T*? (base {base_T:.1f} h; blue = low value, orange = high value)",
                 loc="left", fontsize=10.5)
    xs = [v for r in tor for v in r[1:3]]
    ax.set_xlim(min(xs) - 1.5, max(xs) + 1.5)
    ax.grid(axis="y", visible=False)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "T04_tornado.png"), dpi=150); plt.close(fig)

    # ------------------------------------------------------------- Monte Carlo on T* at 3 humidities
    rng = np.random.default_rng(4)
    N = 400
    out = {40: [], 55: [], 65: []}
    for _ in range(N):
        kw = {k: rng.uniform(lo_, hi_) for k, lo_, hi_, _l in tests}
        for RH in out:
            out[RH].append(Case(RH_store=RH, **kw).optimum()[0])
    print("\nMONTE CARLO (uniform over tornado ranges, N=%d)" % N)
    for RH, v in out.items():
        v = np.array(v)
        print(f"  RH {RH}%: T* median {np.median(v):.1f} h, 5-95% [{np.percentile(v,5):.1f}, {np.percentile(v,95):.1f}] h")
    ratio = np.array(out[40]) / np.array(out[65])
    print(f"  ratio T*(40%)/T*(65%): median {np.median(ratio):.2f}, 5-95% [{np.percentile(ratio,5):.2f}, {np.percentile(ratio,95):.2f}]")
