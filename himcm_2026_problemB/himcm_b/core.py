"""
HiMCM 2026 Problem B - core physics + comfort engine.

Everything here is deliberately written as small, independently testable
functions so a 4-person team can own different blocks without merge pain.

Units: T in degC, RH in %, pressure in Pa, air speed in m/s, power in kW.
"""
import math
import numpy as np

SIGMA = 5.670374419e-8
P_ATM = 101325.0

# ---------------------------------------------------------------- psychrometrics
def p_ws(T):
    """Saturation vapour pressure over water, Pa. ASHRAE Fundamentals Ch.1 (Hyland-Wexler)."""
    Tk = T + 273.15
    c = (-5.8002206e3, 1.3914993, -4.8640239e-2, 4.1764768e-5, -1.4452093e-8, 6.5459673)
    return math.exp(c[0] / Tk + c[1] + c[2] * Tk + c[3] * Tk**2 + c[4] * Tk**3 + c[5] * math.log(Tk))


def W_from_RH(T, RH, p=P_ATM):
    """Humidity ratio, kg water / kg dry air."""
    pw = (RH / 100.0) * p_ws(T)
    return 0.621945 * pw / (p - pw)


def RH_from_W(T, W, p=P_ATM):
    pw = p * W / (0.621945 + W)
    return min(100.0, 100.0 * pw / p_ws(T))


def enthalpy(T, W):
    """Moist air enthalpy, kJ/kg dry air."""
    return 1.006 * T + W * (2501.0 + 1.86 * T)


def T_wetbulb(T, RH, p=P_ATM):
    """Thermodynamic wet-bulb by bisection on the adiabatic saturation equation."""
    W = W_from_RH(T, RH, p)
    lo, hi = -50.0, T
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        Ws = W_from_RH(mid, 100.0, p)
        # ASHRAE adiabatic saturation relation
        Wstar = ((2501.0 - 2.326 * mid) * Ws - 1.006 * (T - mid)) / (2501.0 + 1.86 * T - 4.186 * mid)
        if Wstar > W:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------- devices
def evaporative_cooler(T, RH, eps, p=P_ATM):
    """Direct evaporative cooler. Constant wet-bulb line, saturation efficiency eps.

    Returns (T_out, RH_out, W_out). This is the EnergyPlus / ASHRAE direct-stage model.
    The humidity RISE is the half most teams drop, and it is what kills the device
    in humid climates.
    """
    Twb = T_wetbulb(T, RH, p)
    T_out = T - eps * (T - Twb)
    W_in = W_from_RH(T, RH, p)
    W_sat = W_from_RH(Twb, 100.0, p)
    W_out = W_in + eps * (W_sat - W_in)
    return T_out, RH_from_W(T_out, W_out, p), W_out


def eps_from_claimed_drop(drop_C, T_design, RH_design, p=P_ATM):
    """Inverse-calibrate saturation efficiency from the problem's 'up to X degC' claim.

    'Up to' = best case = the driest hour the device will plausibly see.
    """
    Twb = T_wetbulb(T_design, RH_design, p)
    wbd = T_design - Twb
    return min(1.0, drop_C / wbd) if wbd > 0 else 1.0


def mix(T1, W1, T2, W2, phi):
    """Mass-weighted mixing of supply (1) and ambient (2). phi = capture fraction."""
    T = phi * T1 + (1 - phi) * T2
    W = phi * W1 + (1 - phi) * W2
    return T, W


def capture_fraction(Q_supply, A_open, v_wind, C_d=0.6, v_floor=0.5):
    """phi = Q_s / (Q_s + Q_inf), with wind-driven infiltration through the openings.

    Q in m3/s, A_open in m2. v_floor keeps buoyancy/turbulence exchange alive in calm air.
    """
    Q_inf = C_d * A_open * max(v_wind, v_floor)
    return Q_supply / (Q_supply + Q_inf)


# ---------------------------------------------------------------- radiation
def mrt_outdoor(T_a, S_dir, S_dif, sol_alt_deg, svf=1.0, shaded=False,
                alpha_sw=0.7, eps_p=0.97, albedo=0.2, f_p=0.22):
    """Mean radiant temperature for a standing person (Thorsson et al. 2007 form).

    shaded=True removes the direct beam (what a shelter roof actually does).
    svf = sky view factor of the shelter.
    """
    S_dir_eff = 0.0 if shaded else S_dir
    sa = max(math.radians(sol_alt_deg), 0.0)
    # beam flux on a standing person's projected area
    beam = S_dir_eff * f_p / max(math.sin(sa), 0.1) if sol_alt_deg > 3 else 0.0
    diffuse = 0.5 * svf * S_dif
    reflected = 0.5 * albedo * (S_dir_eff + S_dif)
    R_abs = alpha_sw * (beam + diffuse + reflected)
    Tk = T_a + 273.15
    return (Tk**4 + R_abs / (eps_p * SIGMA))**0.25 - 273.15


# ---------------------------------------------------------------- comfort
from pythermalcomfort.models import set_tmp, utci


def SET(T, RH, v, tr=None, met=1.1, clo=0.35):
    """Standard Effective Temperature. Primary index: valid in still AND moving air,
    handles the humidity penalty of evaporative cooling and the sweat-evaporation
    gain of a fan on one scale. met=1.1 (standing, waiting), clo=0.35 (summer).
    """
    tr = T if tr is None else tr
    return float(set_tmp(tdb=T, tr=tr, v=max(v, 0.1), rh=RH, met=met, clo=clo,
                         limit_inputs=False).set)


def UTCI(T, RH, v, tr=None):
    """UTCI cross-check. NOTE: officially valid only for 0.5 <= v10 <= 17 m/s."""
    tr = T if tr is None else tr
    return float(utci(tdb=T, tr=tr, v=max(v, 0.5), rh=RH, limit_inputs=False).utci)


def cooling_effect_set(T, RH, v_still, v_fan, tr=None, met=1.1, clo=0.35):
    """ASHRAE 55 cooling effect: degC that must come off BOTH T and tr at still air
    to match the SET achieved at elevated air speed. This is the official bridge
    between 'feels 3 degC cooler' (fan) and 'air is 5 degC cooler' (evap)."""
    tr = T if tr is None else tr
    target = SET(T, RH, v_fan, tr, met, clo)
    lo, hi = 0.0, 15.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if SET(T - mid, RH, v_still, tr - mid, met, clo) > target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def v_fan_from_claimed_CE(CE_target, T, RH, v_still=0.3, tr=None):
    """Inverse-calibrate the fan's delivered air speed from 'feels up to 3 degC cooler'."""
    lo, hi = v_still, 6.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if cooling_effect_set(T, RH, v_still, mid, tr) < CE_target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------- service / utility
def dissatisfied_fraction(set_C, s0=30.0, k=0.45):
    """Share of waiting people in thermal discomfort, logistic in SET.
    Saturating: cooling 44->42 degC buys almost nothing, 30->28 degC buys a lot.
    Calibrate s0,k against outdoor comfort surveys; sensitivity-test both."""
    return 1.0 / (1.0 + math.exp(-k * (set_C - s0)))


def heat_risk(utci_C, u0=26.0, scale=100.0):
    """Smooth convex UTCI heat-stress weight (safety limb, not comfort limb).

    Convex, so a degree removed at UTCI 46 counts far more than one at UTCI 28 --
    which is the whole point of a SAFETY currency as opposed to a comfort currency.
    A step function on the UTCI bands looks natural but makes the ranking unstable
    (a device only scores when it happens to cross a band edge); we use the smooth
    form and sensitivity-test u0.  Calibrated so UTCI 38 ('strong heat stress') = 1.44.
    """
    return max(0.0, utci_C - u0) ** 2 / scale
