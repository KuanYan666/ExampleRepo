# Data inventory: what we have and where to get more

Every dataset and primary source found so far, organised by the task that will use it.
All paths are relative to the scratchpad folder. **Download the whole folder before the session ends.**

## 1. Data already downloaded (ready to use)

| Data | Where | Covers | Used for |
|---|---|---|---|
| Hourly weather, summer 2025: Phoenix, Las Vegas, Houston, Singapore, Seville | `himcm_b/data/*.csv` | temp, RH, wet-bulb, wind (m/s), direct/diffuse sun | Tasks 2a, 3 |
| **Hourly weather, full year 2025: Singapore** (8,760 h) | `himcm_b/data/Singapore_2025_fullyear.csv` | year mean 26.8 °C, RH 84 %, **mean wet-bulb depression only 2.3 °C** (daytime 3.5, max 9.0); 260 daytime hours > 32 °C; wind 2.1 m/s | Task 3 home venue: evaporative cooling is nearly useless here, fans and shade are the levers |
| Hourly weather, full year 2023: Houston, Minneapolis | `sprint_out/code/data_T07/` | temp, RH | Task 1 seasonal "waste sign" |
| NYC MTA stop-level bus ridership + timetables (GTFS) | `sprint_out/dl_T09/` (`gtfs/`, `T09_occupancy_hourly.csv`, `T09_stop_summary.csv`) | 4 real stops, hourly waiting people | Task 2a occupancy, Task 3 |
| TOPSIS / Monte Carlo results | `sprint_out/dl_T09/T09_topsis_*.csv` | 3 systems × climates | Task 2a, 4 |
| Freezer case spec sheets (Hussmann F6, FWGH-L; Hill Phoenix/Tyler L6FA) | `sprint_out/dl_T04/`, `dl_T05/` | loads, defrost, airflow | Task 1 baseline |
| AHRI 1200 (rating standard text) | `sprint_out/dl_T03/ahri1200_2023.pdf` | official test conditions | Task 1 metric |
| ACEEE field studies 2000/2004/2008 (open cases, doors, night covers) | `sprint_out/dl_T03/aceee*.pdf` | measured savings | Task 1 evidence |
| Faramarzi 2000, Sarhadian 2004 (SCE display-case tests) | `sprint_out/dl_T05/` | infiltration share 78–82 % | Task 1 evidence |
| Frost/defrost papers (Cai 2008 etc.) | `sprint_out/dl_T04/` | frost growth, optimum | Task 1 sawtooth |
| ASHRAE 55 addenda, WHO heat guidance, BoM apparent temperature page | `sprint_out/dl_T10/` | comfort, fan thresholds | Task 2a felt temperature |
| CIBSE AM10 natural ventilation and related | `sprint_out/dl_T11/` | wind/stack ventilation equations | Task 2b |

## 2. Free sources to pull more data from (for Tasks 3–5)

| Need | Source | Link / how |
|---|---|---|
| Hourly weather, any city, 1940–now | Open-Meteo archive API (free, no key; rate-limited, retry slowly) | https://archive-api.open-meteo.com/v1/archive |
| Electricity prices (US, by state) | EIA Electric Power Monthly, table 5.3 | https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=epmt_5_3 |
| Hourly weather, Canada | Environment Canada | https://www.canada.ca/en/environment-climate-change/services/climate-change/canadian-centre-climate-services/display-download/technical-documentation-hourly-data.html |
| US bus ridership by stop/hour | NYC MTA (data.ny.gov) | https://data.ny.gov/d/fvdm-uavx |
| Freezer efficiency rules (US) | 10 CFR 431.66 | https://www.ecfr.gov/current/title-10/chapter-II/subchapter-D/part-431/subpart-C/subject-group-ECFR4a5fe5c7a4d8a5a/section-431.66 |
| Supermarket door/infiltration method | PNNL-20026 (Cho et al. 2010) | https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-20026.pdf |
| Display-case energy & store interaction | ORNL reports | https://info.ornl.gov/sites/publications/Files/Pub57417.pdf |
| Case-credit equations | EnergyPlus Engineering Reference, refrigeration | https://bigladdersoftware.com/epx/docs/22-1/engineering-reference/refrigeration-equipment.html |
| Heat Index formula (NWS) | NOAA | https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml |
| Real evaporative cooler specs | Portacool Jetstream 270; Big Ass Fans Cool-Space; Hessaire MC37M | https://www.portacool.com/legacy-evaporative-coolers/jetstream-series/jetstream-270-evaporative-coolers/ |

**Singapore passenger data:** LTA DataMall "Passenger Volume by Bus Stops" gives tap-in/tap-out per stop per hour (weekday/weekend, monthly files). It needs a **free API key** (register at https://datamall.lta.gov.sg/content/datamall/en/dynamic-data.html). Only recent months may be downloadable, so request a key early.

**Still missing (get these next):** a real venue's geometry and crowd counts for Task 3
(stadium concourse or Singapore MRT/bus interchange; LTA DataMall needs a free API key);
local electricity and water tariffs for the chosen venues; grid carbon intensity (Ember).

All 100 URLs cited by the research memos are listed in `all_urls.txt`.
**Open each source yourselves before citing it.**
