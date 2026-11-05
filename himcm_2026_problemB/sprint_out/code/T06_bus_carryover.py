"""
T06 - carry the recommended freezer measure over to the bus shelter.

Freezer:  eta = (kg of product x hours held in the safe band) / kWh
Shelter:  eta = (person x hours x degC of felt-temperature relief that reaches the person) / kWh

Felt temperature = SET (Standard Effective Temperature, pythermalcomfort), as in core.py.
Capture fractions (0.26 small cooler, 0.44 large cooler) and the fan air speed are the
team's one-parameter fit to COMAP's table (calibration_check.py); NOT independently verified.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "himcm_b"))
import core as C
from pythermalcomfort.models import set_tmp


def SET(T, RH, v, tr=None, met=1.1, clo=0.35):
    """Same as core.SET but WITHOUT pythermalcomfort's default rounding to 0.1 C
    (core.SET rounds, which makes small differences jump in 0.1 C steps)."""
    tr = T if tr is None else tr
    return float(set_tmp(tdb=T, tr=tr, v=max(v, 0.1), rh=RH, met=met, clo=clo,
                         limit_inputs=False, round_output=False).set)


def cooling_effect(T, RH, v_still, v_fan):
    target = SET(T, RH, v_fan)
    lo, hi = 0.0, 15.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if SET(T - mid, RH, v_still, T - mid) > target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def v_fan_from_CE(ce, T, RH, v_still):
    lo, hi = v_still, 6.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if cooling_effect(T, RH, v_still, mid) < ce:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)

EPS = 0.85                       # pad saturation efficiency [team assumption, manuf. range 0.70-0.90]
PHI = {"Evap 1.2 kW": 0.26, "Evap 2.5 kW": 0.44}   # team fit to COMAP table
POWER = {"Fan 0.25 kW": 0.25, "Evap 1.2 kW": 1.2, "Evap 2.5 kW": 2.5}   # COMAP table, read as kW
V_STILL = 0.3                    # m/s still-air reference in a shelter [ASSUMED]
V_FAN = v_fan_from_CE(3.0, 43.0, 12.0, V_STILL)   # calibrated on the design hour

CLIMATES = {"Dry design hour 43 C / 12 % RH": (43.0, 12.0),
            "Humid hour 34 C / 60 % RH": (34.0, 60.0)}


def equivalent_relief(T, RH, set_after):
    """degC that air AND radiant temperature would have to fall, in still air, to give set_after.
    Same definition as ASHRAE 55 'cooling effect', so it is on COMAP's 'feels X C cooler' scale."""
    lo, hi = 0.0, 20.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if SET(T - mid, RH, V_STILL, T - mid) > set_after:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def relief(device, T, RH, tr_cooled=False):
    """degC of SET reduction delivered to a person standing in the shelter (radiant temp = air temp before)."""
    base = SET(T, RH, V_STILL, tr=T)
    if device.startswith("Fan"):
        after = SET(T, RH, V_FAN, tr=T)
        return base - after, equivalent_relief(T, RH, after)
    T_o, RH_o, W_o = C.evaporative_cooler(T, RH, EPS)
    W_a = C.W_from_RH(T, RH)
    Tm, Wm = C.mix(T_o, W_o, T, W_a, PHI[device])
    RHm = C.RH_from_W(Tm, Wm)
    after = SET(Tm, RHm, V_STILL, tr=(Tm if tr_cooled else T))   # default: cooler does not cool surfaces [ASSUMED]
    return base - after, equivalent_relief(T, RH, after)


def table(n_people=1):
    rows = []
    for cname, (T, RH) in CLIMATES.items():
        for d, P in POWER.items():
            dset, eq = relief(d, T, RH)
            rows.append(dict(climate=cname, device=d, P_kW=P, dSET=dset, relief=eq,
                             eta=n_people * eq / P))   # person.degC.h per kWh
    return rows


if __name__ == "__main__":
    print(f"fan air speed implied by 'feels 3 C cooler' at 43 C/12 %: {V_FAN:.2f} m/s")
    for row in table():
        print(f"{row['climate']:32s} {row['device']:12s} P={row['P_kW']:4.2f} kW  "
              f"dSET={row['dSET']:5.2f} C  felt relief={row['relief']:5.2f} C   eta = {row['eta']:5.2f} person.C.h per kWh (per person served)")
    print("sensitivity: if the cooled air also cooled the shelter surfaces (tr = mixed air T):")
    for cname, (T, RH) in CLIMATES.items():
        for d in PHI:
            print(f"   {cname:32s} {d}: felt relief {relief(d, T, RH, tr_cooled=True)[1]:.2f} C")
