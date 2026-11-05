"""T10 part 1: what can each index 'see'?  + constant checks + city design hours."""
import numpy as np
import pandas as pd
from T10_lib import *  # noqa

print("=" * 78)
print("A. CHECK OUR HAND-CODED INDICES AGAINST pythermalcomfort")
print("=" * 78)
for T, RH, v in [(25, 30, 0.1), (35, 40, 1.0), (40, 15, 2.0), (33, 70, 0.5)]:
    a1, a2 = AT_bom(T, RH, v), float(ptc_at(tdb=T, rh=RH, v=v, round_output=False).at)
    h1 = HI_nws(T, RH)
    h2 = float(heat_index_rothfusz(tdb=T, rh=RH, round_output=False, limit_inputs=False).hi)
    x1 = humidex_eccc(T, RH)
    x2 = float(ptc_humidex(tdb=T, rh=RH, model="masterson", round_output=False).humidex)
    print(f"T={T} RH={RH} v={v}:  AT ours {a1:6.2f} ptc {a2:6.2f} | HI ours {h1:6.2f} "
          f"ptc {h2:6.2f} | Humidex ours {x1:6.2f} ptc {x2:6.2f}")
print("pythermalcomfort docstring example at(25,30,0.1) = 24.1 ->",
      round(AT_bom(25, 30, 0.1), 1))
for T, RH, v in [(25, 50, 0.3), (30, 50, 1.0), (40, 15, 1.0)]:
    print(f"CE official {CE(T, RH, v):.2f}  vs our unrounded solver {CE_fine(T, RH, v):.3f}"
          f"   (T={T}, RH={RH}, v={v})")

print("\n" + "=" * 78)
print("B. CAN THE INDEX SEE IT?  change of index (degC) from a reference hour")
print("   reference: T=35 C, RH=40 %, v=0.5 m/s at the body, tr=T (shade)")
print("=" * 78)
T0, RH0, v0 = 35.0, 40.0, 0.5
fns = {
    "BoM AT (no rad.)": lambda T, RH, v, tr: AT_bom(T, RH, v * LOGLAW_1p1_TO_10),
    "BoM AT (rad.)*":   lambda T, RH, v, tr: AT_bom_rad(T, RH, v * LOGLAW_1p1_TO_10,
                                                        0.97 * 5.67e-8 * ((tr + 273.15) ** 4 - (T + 273.15) ** 4)),
    "NWS Heat Index":   lambda T, RH, v, tr: HI_nws(T, RH),
    "Humidex":          lambda T, RH, v, tr: humidex_eccc(T, RH),
    "WBGT (BoM approx)": lambda T, RH, v, tr: WBGT_bom(T, RH),
    "UTCI":             lambda T, RH, v, tr: UTCI(T, RH, v, tr),
    "SET":              lambda T, RH, v, tr: SET(T, RH, v, tr),
}
rows = []
for name, f in fns.items():
    base = f(T0, RH0, v0, T0)
    rows.append(dict(index=name, base=base,
                     d_air_plus1=f(T0 + 1, RH0, v0, T0 + 1) - base,
                     d_fan_0p5_to_2=f(T0, RH0, 2.0, T0) - base,
                     d_RH_40_to_60=f(T0, 60, v0, T0) - base,
                     d_tr_plus10=f(T0, RH0, v0, T0 + 10) - base))
tab = pd.DataFrame(rows).set_index("index").round(2)
print(tab.to_string())
print("* radiation version: Q approximated as the extra long-wave gain eps*sigma*(tr^4-T^4);"
      " a crude stand-in, only to show the term exists.")
tab.to_csv(S + "/sprint_out/code/T10_1_sensitivity_table.csv")

print("\n" + "=" * 78)
print("C. WORKED EXAMPLE: the same hour through every index")
print("=" * 78)
for T, RH, v in [(43, 12, 0.5), (34, 60, 0.5)]:
    print(f"T={T} C, RH={RH} %, v={v} m/s:  AT={AT_bom(T, RH, v * LOGLAW_1p1_TO_10):.1f}  "
          f"HI={HI_nws(T, RH):.1f}  Humidex={humidex_eccc(T, RH):.1f}  "
          f"WBGT~{WBGT_bom(T, RH):.1f}  UTCI={UTCI(T, RH, v):.1f}  SET={SET(T, RH, v):.1f}"
          f"   e={e_bom(T, RH):.1f} hPa  Twb={C.T_wetbulb(T, RH):.1f}")

print("\n" + "=" * 78)
print("D. CITY 'TYPICAL HOT AFTERNOON' (median of the daily-max-temperature hours, Jun-Sep 2025)")
print("=" * 78)
design = {}
for city in ["Phoenix", "LasVegas", "Seville", "Houston", "Singapore"]:
    d = pd.read_csv(S + f"/himcm_b/data/{city}.csv", parse_dates=["time"])
    idx = d.groupby(d.time.dt.date).temperature_2m.idxmax()
    pk = d.loc[idx]
    T, RH = pk.temperature_2m.median(), pk.relative_humidity_2m.median()
    p90 = pk.temperature_2m.quantile(0.9)
    design[city] = (T, RH)
    print(f"{city:10s} median peak {T:5.1f} C at {RH:4.0f} % RH  (wet-bulb {C.T_wetbulb(T, RH):4.1f} C,"
          f" depression {T - C.T_wetbulb(T, RH):4.1f} C)   90th-pct peak {p90:4.1f} C")
pd.DataFrame(design, index=["T", "RH"]).T.to_csv(S + "/sprint_out/code/T10_design_hours.csv")
