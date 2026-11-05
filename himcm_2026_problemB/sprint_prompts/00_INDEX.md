# Parallel research sprint — 11 chats + 1 merge

Each `.txt` file is a **complete, self-contained prompt**. Open a new chat, paste the whole file, send.

## Before you start (2 minutes)
- Turn on **web search** and **code execution** in each chat. Without them, answers fall back on memory.
- **Save every conversation** (share link or export). COMAP requires prompts and outputs in the AI-use report.
- Download each chat's `.md` file into one folder.

## Run order (if money runs out, the top ones matter most)

| # | File | What it answers | Owner |
|---|---|---|---|
| 1 | `T02_deflection_modulus_optimum` | When does the air curtain fail ("breakthrough"), and what is the best curtain speed? | Physics |
| 2 | `T01_air_curtain_jet` | Jet + entrainment physics → how much warm air gets in | Physics |
| 3 | `T03_evidence_table` | Verified numbers and real regulator metrics (DOE, EU, ENERGY STAR) | Evidence |
| 4 | `T06_metric_design` | Which efficiency definition survives the limiting-case tests | Evidence |
| 5 | `T05_which_aspects_sensitivity` | Elasticity + Sobol → which aspects belong in the measure | Maths |
| 6 | `T08_jet_in_crossflow_busstop` | The bridge: the air-curtain physics applied to a bus shelter in wind | Physics |
| 7 | `T10_felt_temperature_index` | Putting "feels 3 °C" and "air 5 °C" on one scale | Maths |
| 8 | `T04_frost_defrost_optimum` | Frost ODE + optimal defrost interval (the sawtooth) | Maths |
| 9 | `T07_nested_store_system` | Store door + HVAC + season → the sign of waste | Evidence |
| 10 | `T11_rail_station_zone` | Task 2b zone model; crowd as heat source | Maths |
| 11 | `T09_occupancy_and_comparison` | Little's law + TOPSIS across the 3 systems | Evidence |
| last | `T99_MERGE_run_last` | Paste the merge prompt, then ALL returned memos → consistency check | All |

Owners: **Physics** = your aerodynamics teammates · **Maths** = modelling/coding · **Evidence** = sources + writing.
Each owner reads their chats' memos and decides what to keep.

## When the memos come back
1. Run `T99_MERGE_run_last` with every memo attached.
2. **Check every citation yourselves.** AI chats sometimes invent sources. Anything tagged
   `[ASSUMED]`, or any source you can't open, is not yet usable.
3. Add the key results to `HANDOVER_LOG.md`.
