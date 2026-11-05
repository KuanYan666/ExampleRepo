"""
T10 - felt-temperature indices on one scale.  Shared library.

Every index is written out explicitly (so the team can see the constants) and,
where pythermalcomfort (v4.8.0) has the same index, cross-checked against it.

Units: T in degC, RH in %, vapour pressure e in hPa, air speed v in m/s.
"""
import math
import sys
import warnings
import numpy as np

warnings.filterwarnings("ignore")
S = "/tmp/claude-0/-home-user-ExampleRepo/a7b0ab5c-e343-5d3f-83da-06d68f7a8990/scratchpad"
sys.path.insert(0, S + "/himcm_b")
import core as C  # noqa: E402  (team helper: wet-bulb, humidity ratio, evap cooler)

from pythermalcomfort.models import (set_tmp, utci, cooling_effect, at as ptc_at,  # noqa: E402
                                     heat_index_rothfusz, humidex as ptc_humidex,
                                     use_fans_heatwaves)

# Personal factors for a person WAITING at a bus stop (ASHRAE 55 typical values,
# as tabulated in pythermalcomfort.utilities.met_typical_tasks / clo_typical_ensembles)
MET = 1.2    # "Standing, relaxed"
CLO = 0.36   # "Walking shorts, short-sleeve shirt"
V_STILL = 0.1  # ASHRAE 55-2020 Addendum c: still-air reference 0.1 m/s


# ---------------------------------------------------------------- vapour pressure
def e_bom(T, RH):
    """Vapour pressure, hPa, exactly as on the BoM thermal-stress page."""
    return RH / 100.0 * 6.105 * math.exp(17.27 * T / (237.7 + T))


# ---------------------------------------------------------------- 1. Steadman / BoM AT
def AT_bom(T, RH, ws10):
    """BoM apparent temperature, non-radiation version.
    AT = Ta + 0.33 e - 0.70 ws - 4.00   (ws = wind at 10 m, m/s)"""
    return T + 0.33 * e_bom(T, RH) - 0.70 * ws10 - 4.00


def AT_bom_rad(T, RH, ws10, Q):
    """BoM AT with radiation: Ta + 0.348 e - 0.70 ws + 0.70 Q/(ws+10) - 4.25.
    Q = net radiation absorbed per unit body surface, W/m2."""
    return T + 0.348 * e_bom(T, RH) - 0.70 * ws10 + 0.70 * Q / (ws10 + 10.0) - 4.25


# ---------------------------------------------------------------- 2. NWS heat index
def HI_nws(T, RH):
    """NWS heat index (WPC algorithm, Rothfusz regression + adjustments). Returns degC."""
    F = T * 9 / 5 + 32
    simple = 0.5 * (F + 61.0 + (F - 68.0) * 1.2 + RH * 0.094)
    if 0.5 * (simple + F) < 80.0:
        HI = simple
    else:
        HI = (-42.379 + 2.04901523 * F + 10.14333127 * RH - 0.22475541 * F * RH
              - 0.00683783 * F * F - 0.05481717 * RH * RH + 0.00122874 * F * F * RH
              + 0.00085282 * F * RH * RH - 0.00000199 * F * F * RH * RH)
        if RH < 13 and 80 <= F <= 112:
            HI -= ((13 - RH) / 4) * math.sqrt((17 - abs(F - 95.0)) / 17)
        elif RH > 85 and 80 <= F <= 87:
            HI += ((RH - 85) / 10) * ((87 - F) / 5)
    return (HI - 32) * 5 / 9


# ---------------------------------------------------------------- 3. Humidex (ECCC)
def dewpoint(T, RH):
    """Magnus dew point, degC (same constants as BoM vapour pressure)."""
    g = math.log(RH / 100.0) + 17.27 * T / (237.7 + T)
    return 237.7 * g / (17.27 - g)


def humidex_eccc(T, RH):
    """Humidex = T + 0.5555 (e - 10), e = 6.11 exp(5417.7530 (1/273.15 - 1/Td_K)).
    Constants as in ECCC technical documentation for hourly data (273.15; older
    sources print 273.16 -- the difference is < 0.05 C)."""
    Td = dewpoint(T, RH) + 273.15
    e = 6.11 * math.exp(5417.7530 * (1 / 273.15 - 1 / Td))
    return T + 0.5555 * (e - 10.0)


# ---------------------------------------------------------------- 4. WBGT (BoM approx.)
def WBGT_bom(T, RH):
    """BoM simplified WBGT = 0.567 Ta + 0.393 e + 3.94 (assumes moderately high sun,
    light wind; sees neither the real radiation nor the real wind)."""
    return 0.567 * T + 0.393 * e_bom(T, RH) + 3.94


# ---------------------------------------------------------------- 5. UTCI
LOGLAW_1p1_TO_10 = math.log(10 / 0.01) / math.log(1.1 / 0.01)   # ~1.47


def UTCI(T, RH, v_body, tr=None):
    """UTCI. pythermalcomfort expects wind at 10 m.  A fan's speed is measured AT the
    body, so we convert body-level speed to an 'equivalent 10 m wind' with a log
    profile (roughness 0.01 m) -- an assumption, flagged in the memo -- and clip to
    the official 0.5 m/s floor."""
    tr = T if tr is None else tr
    v10 = max(0.5, v_body * LOGLAW_1p1_TO_10)
    return float(utci(tdb=T, tr=tr, v=v10, rh=RH, limit_inputs=False).utci)


# ---------------------------------------------------------------- 6. SET and CE
def SET(T, RH, v, tr=None, met=MET, clo=CLO, ce_mode=False):
    """Standard Effective Temperature.  ce_mode=True switches off the metabolic
    free-convection floor, exactly as ASHRAE 55 Appendix D / pythermalcomfort do
    when computing the cooling effect (calculate_ce=True)."""
    tr = T if tr is None else tr
    return float(set_tmp(tdb=T, tr=tr, v=max(v, V_STILL), rh=RH, met=met, clo=clo,
                         limit_inputs=False, round_output=False,
                         calculate_ce=ce_mode).set)


def CE(T, RH, v, tr=None, met=MET, clo=CLO):
    """ASHRAE 55 cooling effect (official pythermalcomfort implementation)."""
    tr = T if tr is None else tr
    return float(cooling_effect(tdb=T, tr=tr, vr=v, rh=RH, met=met, clo=clo).ce)


def CE_fine(T, RH, v, tr=None, met=MET, clo=CLO):
    """Same definition, solved by our own bisection without the 2-dp rounding,
    so we can invert it smoothly.  Checked against CE() in T10_1."""
    tr = T if tr is None else tr
    target = SET(T, RH, v, tr, met, clo, ce_mode=True)
    lo, hi = 0.0, 20.0
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        if SET(T - mid, RH, V_STILL, tr - mid, met, clo, ce_mode=True) > target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def v_for_CE(target, T, RH, tr=None, met=MET, clo=CLO, vmax=6.0):
    """Air speed at the person that makes CE = target.  NaN if not reachable by vmax."""
    if CE_fine(T, RH, vmax, tr, met, clo) < target:
        return float("nan")
    lo, hi = V_STILL, vmax
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if CE_fine(T, RH, mid, tr, met, clo) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------- 7. physiology
def t_core(T, RH, v, tr=None, met=MET, clo=CLO):
    """Core temperature from pythermalcomfort's use_fans_heatwaves (Gagge two-node)."""
    tr = T if tr is None else tr
    r = use_fans_heatwaves(tdb=T, tr=tr, v=max(v, V_STILL), rh=RH, met=met, clo=clo,
                           limit_inputs=False, round_output=False)
    return float(r.t_core), float(r.heat_strain)


# ---------------------------------------------------------------- evaporative state
def evap_state(T, RH, dT_air):
    """Air that has been evaporatively cooled by dT_air (after mixing).  Evaporation is
    (almost exactly) constant-enthalpy: the sensible heat taken out of the air comes back
    as latent heat in the added water vapour.  Returns (T_new, RH_new) or None if the
    drop is impossible (would go below the wet-bulb temperature)."""
    W = C.W_from_RH(T, RH)
    h = C.enthalpy(T, W)
    Tn = T - dT_air
    Wn = (h - 1.006 * Tn) / (2501.0 + 1.86 * Tn)
    if Wn > C.W_from_RH(Tn, 100.0) + 1e-9:
        return None
    return Tn, C.RH_from_W(Tn, Wn)


def CE_rel(T, RH, v0, v1, tr=None, met=MET, clo=CLO):
    """Generalised cooling effect: degC that must come off T and tr, at the BASELINE
    breeze v0, to feel (in SET) the same as at the fan speed v1.  With v0 = 0.1 m/s this
    is exactly the ASHRAE 55 CE."""
    tr = T if tr is None else tr
    target = SET(T, RH, v1, tr, met, clo, ce_mode=True)
    lo, hi = -10.0, 20.0
    for _ in range(45):
        mid = 0.5 * (lo + hi)
        if SET(T - mid, RH, v0, tr - mid, met, clo, ce_mode=True) > target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def v_for_CE_rel(target, T, RH, v0, tr=None, met=MET, clo=CLO, vmax=6.0):
    if CE_rel(T, RH, v0, vmax, tr, met, clo) < target:
        return float("nan")
    lo, hi = v0, vmax
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        if CE_rel(T, RH, v0, mid, tr, met, clo) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def felt_drop(T, RH, v0, tr, set_after):
    """ONE SCALE.  'Felt temperature drop' FTD (degC): how much the air AND radiant
    temperature would have to fall, at the original breeze v0 and original RH, to give
    the SET reached after the device acts.  For a fan this is exactly the ASHRAE 55
    cooling effect (when v0 = 0.1 m/s), so it is the unit in which the fan's
    '3 C cooler' claim is written.  Uses the ASHRAE CE convention (calculate_ce=True)."""
    lo, hi = -15.0, 25.0
    for _ in range(45):
        mid = 0.5 * (lo + hi)
        if SET(T - mid, RH, v0, tr - mid, ce_mode=True) > set_after:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def ftd_evap(T, RH, dT, v0, tr=None, radiant_follows=False):
    tr = T if tr is None else tr
    st = evap_state(T, RH, dT)
    if st is None:
        return float("nan")
    Tn, RHn = st
    after = SET(Tn, RHn, v0, tr - dT if radiant_follows else tr, ce_mode=True)
    return felt_drop(T, RH, v0, tr, after)


def ftd_fan(T, RH, v0, v1, tr=None):
    tr = T if tr is None else tr
    return felt_drop(T, RH, v0, tr, SET(T, RH, v1, tr, ce_mode=True))
