"""Assemble one self-contained prompt file per parallel chat."""
import pathlib

HERE = pathlib.Path(__file__).parent

SHARED = """=== SHARED CONTEXT (identical in every chat — read fully before starting) ===

We are a 3-student high-school team in HiMCM 2026 (COMAP's High School Mathematical Contest in Modeling), Problem B: "Air Conditioning the Environment: Modeling Energy Waste in Public Cooling". Contest window 4–17 Nov 2026. 25-page limit. AI use is allowed but must be fully documented; no help from people outside the team.

THE PROBLEM'S TASKS (close paraphrase):
1. Understand the Problem. Open freezer cases in grocery stores continuously use energy to remove heat from food and the surrounding air. What aspects of a freezer case should be considered when measuring cooling efficiency? Should efficiency depend only on energy use? Justify the quantities to include. Use this to motivate the models below.
2a. A city wants to cool an open-sided bus stop shelter. Options: A. Fan — "makes space feel up to 3 °C cooler", 0.25 "kW/hr". B. Evaporative cooler — "lowers air temperature up to 5 °C", 1.2 "kW/hr". C. Large evaporative cooler — "lowers air temperature up to 8 °C", 2.5 "kW/hr". Develop a measure of cooling efficiency (consider size of cooled area, climate conditions, energy use, number of people benefiting).
2b. Revise the model for a semi-open rail-station waiting area; explain what changed, why it was necessary, and how it improved the model.
3. Apply to at least two venues in different climates or with different systems; identify the characteristics that contribute most to efficient cooling.
4. Balance cooling performance, visitor experience, energy use and cost.
5. Guidelines + a 1–2 page memo to the Chief Operations Officer + a public blog post.
Notes: "kW/hr" is not a valid unit; we read it as electrical power in kW. The fan's figure is a FELT temperature; the coolers' figures are AIR temperatures.

TEAM DECISIONS SO FAR:
- Structure follows the problem: freezer -> bus stop -> rail station -> venues. Each step must add exactly ONE new ingredient.
- Spine of the paper: what you are cooling changes, so the measure must change. Freezer: food, only ACTUAL temperature matters. Bus stop: a person, FELT temperature matters. Rail station: a crowd; felt temperature AND the crowd itself is a big heat source.
- Task 1 (freezer) is our foundation. Our physics teammates believe the key physics is AERODYNAMICS: an open case is "sealed" only by an air curtain (a thin downward jet of cold air), and most of the energy is lost through it.
- Working definition: efficiency = useful service delivered / resources consumed. "Capture fraction" phi = share of the cooling produced that actually reaches its target.

OUR PRELIMINARY NUMBERS (our own estimates, NOT verified — check them and correct them if wrong):
- Typical 2.5 m open vertical low-temperature (freezer) case: refrigeration load ~2.5 kW; case air ~ -18 °C; store air 24 °C / 55% RH; COP ~1.7; Carnot limit for -18 °C evaporating -> 35 °C condensing ~4.8.
- Literature: infiltration through the air curtain ~67–85% of total case load (Howell & Adams 1991 ~75%; Amin et al. 2011 up to 80%; Kettering University/Navaz ~70%; a Brunel University thesis >=85%).
- Per kg of store air entering the case: sensible ~42 kJ, latent (water condensing + freezing) ~27 kJ -> ~39% of the infiltration load is moisture.
- Store front-door traffic raises store humidity; we estimate this raises case load by 8–27%, and ~73% of that extra is moisture, ~27% temperature.
- Net heat a case adds to the store = its electricity use (energy conservation). In winter the escaping cold offsets store heating ("waste" partly recovered); a bus shelter's escaping cold is always lost.
- Time constants: one door opening ~8 s, case air ~1 min, store air ~30 min, product ~1 h, coil frost ~6 h. With hourly weather data, only product temperature and frost need differential equations.
- Bus shelter: fitting ONE parameter to COMAP's table (pad saturation efficiency 0.85, design hour 43 °C / 12% RH) implies capture fraction ~0.26 (1.2 kW cooler) and ~0.44 (2.5 kW cooler), i.e. ~74% / 56% of the cooling lost; residual +/-0.21 °C on both claims.

MODEL TOOLKIT WE PREFER (from our catalog): composite index, AHP, entropy weights, TOPSIS, regression, curve fitting, ODEs / stock-and-flow, Monte Carlo, queueing (Little's law), linear/integer programming, multi-objective optimisation / Pareto front, dynamic programming. Checks: sensitivity (elasticity E = (dy/dp)(p/y), tornado chart, Monte Carlo / Sobol), validation (units check, limiting cases, back-test, compare with a published figure). Well-documented physics/engineering models from the literature are equally welcome. Judges punish "model forcing": every model must answer the task's verb.

HOW TO WORK AND WRITE:
- Write for a smart 16-year-old who has NOT studied thermodynamics or fluid mechanics. For every concept: plain words first, then the equation, then define EVERY symbol WITH UNITS, then one sentence of intuition ("this means...").
- Give a worked numerical example for every equation.
- Do real research (use web search). Cite every number and equation: author, year, title, link, and page/equation/table if possible. Tag each number [VERIFIED: source] or [ASSUMED: reason]. Never invent a source or a value; if you cannot find something, say so plainly.
- If you can run Python, run it and include the code, its output and figures (clear labels, units on axes). If you cannot run code, give complete runnable code.
- Be creative: we want precise, non-obvious, defensible insights that other teams would not think of. No speculation dressed up as fact.
- Do NOT write the competition paper. Produce a research/modelling memo the team will learn from and then rewrite in their own words.
- END WITH: (a) 3–5 key findings with numbers; (b) what is verified vs assumed; (c) decisions our team must make; (d) exactly how this feeds the rest of the paper; (e) weaknesses and open questions.
- Deliver everything as ONE downloadable Markdown file named after your task ID (e.g. T01_air_curtain.md), plus code/figures if produced.

=== END OF SHARED CONTEXT ===
"""

TASKS = {
"T01_air_curtain_jet": """YOUR TASK (T01) — Air-curtain aerodynamics: the freezer's invisible wall.

1. Explain what an air curtain is and how it "seals" an open vertical freezer case. Include a labelled diagram: discharge grille at the top, return grille at the bottom, warm store air on one side, cold case air on the other.
2. Model the curtain with documented turbulent-jet theory: a plane (2-D) jet discharged downward, nozzle width b (~2–5 cm), discharge speed U0 (~0.5–1.5 m/s), opening height H (~1.2–1.8 m). Use the entrainment hypothesis (Morton, Taylor & Turner 1956) and standard plane-jet results (e.g. Rajaratnam 1976 "Turbulent Jets"; Pope 2000 "Turbulent Flows") for centre-line velocity decay, spreading rate and entrainment rate. Compute how much warm store air the jet entrains on the store side over the height H: that is the infiltration.
3. Check the flow regime: Reynolds number Re = U0*b/nu. Is a real air curtain fully turbulent, or only transitional? What changes in the model if it is not fully turbulent? (A precision point other teams will miss.)
4. Add buoyancy: the curtain and case interior are cold and dense, the store is warm. Explain the pressure difference across the opening (stack effect) that pushes the curtain outward, and define the relevant dimensionless number(s) (densimetric Froude / Richardson / Archimedes number) in plain words.
5. Compute infiltration mass flow and infiltration load for a baseline 2.5 m case and compare with the literature (~67–85% of a ~2.5 kW load). Does the physics reproduce it? If not, why not?
6. Figures: (i) velocity and temperature profiles across the curtain at several heights; (ii) infiltration vs U0 and vs b.
7. State what carries over to an outdoor bus shelter, where a cooler blows a jet of cool air into wind.""",

"T02_deflection_modulus_optimum": """YOUR TASK (T02) — The deflection modulus, "breakthrough", and the optimal curtain speed.

1. Find the Hayes & Stoecker air-curtain theory (Hayes 1968; Hayes & Stoecker 1969, ASHRAE Transactions) and later uses for refrigerated display cases (e.g. Field & Loth; Navaz et al.; Amin et al. 2009–2012; Gaspar et al.). Give the exact definition of the deflection modulus Dm, the minimum value for a stable curtain, the recommended safety factor, and the reported range for open vertical cases (one source says ~0.12–0.25 — verify). Explain "breakthrough": the curtain fails and infiltration becomes worse than having no curtain.
2. Build the U-shaped curve of infiltration vs discharge velocity: too slow -> buoyancy breaks through; too fast -> the jet entrains more warm air. Use documented data or correlations (e.g. infiltration vs Reynolds number or vs Dm from published experiments).
3. Turn it into a decision (optimisation): total energy = refrigeration electricity for the infiltration load (load / COP) + fan electrical power + the fan's own heat that the case must then remove. Fan power rises roughly with U0^3 — state and justify. Find the optimal U0 (or Dm). Show sensitivity to store temperature and humidity.
4. Figures: infiltration vs U0 with the stable and breakthrough regions marked; total energy vs U0 with the optimum marked.
5. Explain how the same "jet momentum vs disturbing force" idea applies to a cooler blowing into a bus shelter in a crosswind.""",

"T03_evidence_table": """YOUR TASK (T03) — A verified evidence table on open refrigerated display cases (especially low-temperature/freezer cases) that our paper can cite.

Find, with exact source and page/figure/table where possible:
- infiltration share of total case load (several independent studies; note the test conditions);
- typical refrigeration load per metre of case; air-curtain discharge velocity, nozzle width, opening height;
- case temperatures and typical COP for low-temperature vs medium-temperature supermarket refrigeration;
- share of case energy from lights, evaporator fans, anti-sweat heaters and defrost;
- effect of store temperature and relative humidity on case load (ASHRAE Refrigeration Handbook; test standards ASHRAE 72 / ISO 23953 — which store conditions are used in testing, and why);
- measured savings from (a) fitting glass doors to open cases, (b) night covers/blinds, (c) improved air curtains;
- official efficiency metrics actually used by regulators/industry, e.g. US DOE commercial refrigeration equipment standards (daily energy consumption per total display area, 10 CFR 431.66), ENERGY STAR, EU ecodesign / energy label for refrigerated display cabinets (Energy Efficiency Index). Explain exactly what each metric divides by what, and what it ignores;
- the "case credit" concept (refrigerated cases cooling the store; refrigeration–HVAC interaction).

Output: a table (quantity, value, unit, conditions, source with link, exact quote/location, confidence), then a short note on where sources contradict each other. Do not invent anything. Prefer primary sources.""",

"T04_frost_defrost_optimum": """YOUR TASK (T04) — Frost on the coil, and the optimal defrost interval.

1. Explain in plain words why moisture from store air turns into frost on the evaporator coil, and why frost hurts performance (insulates the coil, blocks airflow).
2. Build a stock-and-flow / ODE model: frost mass m_f(t) grows with the moisture brought in by infiltration (air mass flow x humidity-ratio difference); frost reduces coil conductance and/or airflow, so capacity or COP degrades over time. Use documented frost-growth / frost-density correlations where possible (cite them).
3. Each defrost costs energy: electric heater power x time, plus re-cooling the heat added to the case, plus product temperature rise.
4. Choose the defrost interval T that minimises the average energy per hour = (defrost energy + extra energy lost to frost during [0, T]) / T. This is a renewal-reward / economic-replacement problem: derive the optimality condition (marginal loss rate equals average cost rate), explain it in plain words, and compute T*.
5. Show how T* and energy change with store humidity (link: opening the store's front door makes the store more humid).
6. Figures: frost mass and efficiency vs time over several cycles (a sawtooth); average energy vs T with the optimum marked.
7. Explain what this means for the claim "cooling efficiency is a sawtooth, not a single number".""",

"T05_which_aspects_sensitivity": """YOUR TASK (T05) — Decide, with numbers, which aspects of a freezer case belong in a measure of cooling efficiency.

1. Build a transparent energy-balance model of a baseline 2.5 m open vertical freezer case: case load = infiltration (sensible + latent) + conduction through walls + radiation through the opening + lights + evaporator fans + anti-sweat heaters + defrost + product loading. Electricity = refrigeration load / COP + direct electrical loads; optionally the extra store HVAC energy. Use cited typical values and give a plausible range for every parameter.
2. Compute the elasticity E = (dy/dp)(p/y) of (a) electricity per day and (b) electricity per unit of "service" (e.g. kg of product kept frozen, or m^2 of display area) with respect to every parameter. Produce a tornado chart.
3. Run a global sensitivity analysis (Monte Carlo + Sobol indices, e.g. Python SALib) over the ranges. Report first-order and total indices and explain the difference simply.
4. Propose an inclusion rule (e.g. an aspect enters the efficiency measure if its total Sobol index or elasticity exceeds a stated threshold) and justify it. List which aspects survive and which do not, and say how this answers COMAP's question "What aspects of a freezer case should be considered when measuring cooling efficiency?"
5. Flag any parameter where the answer depends strongly on assumptions.""",

"T06_metric_design": """YOUR TASK (T06) — Design and stress-test candidate definitions of "cooling efficiency" for an open freezer case, and answer "Should efficiency depend only on energy use?"

Test these candidates (add others you find): (1) energy per day; (2) COP = heat removed / electricity; (3) second-law efficiency = COP / Carnot COP; (4) energy per display area per day (as in US DOE standards — verify); (5) service-based: kg of product held in its safe temperature band x hours, per kWh; (6) capture / "delivery" fraction = cooling that ends up on the product / cooling produced; (7) benchmark = energy of an ideal reference case (e.g. the same case with doors) / actual energy; (8) marginal efficiency = extra service per extra kWh; (9) net benefit = value of service - price x resources; (10) multi-resource versions (electricity, refrigerant leakage as CO2e, cost).

For each: formula with units; a worked number for a baseline case (~2.5 kW load, COP ~1.7, ~75% infiltration — check and correct these); and LIMITING-CASE tests: switched off; empty case; doors fitted; night cover on; winter vs summer store; very humid store; a more powerful air-curtain fan. Show which definitions give absurd answers (e.g. does COP reward infiltration because more heat is removed per kWh? Test it).

Recommend one primary measure (+ at most one secondary), explain why in plain words, and show how the same measure carries over to a bus shelter where the "product" is a waiting person.""",

"T07_nested_store_system": """YOUR TASK (T07) — The supermarket as a NESTED system: outdoors -> store -> freezer case.

1. Store-level model: an hourly heat AND moisture balance of the store air, including entrance-door infiltration driven by customer traffic (use documented door-infiltration methods, e.g. ASHRAE Fundamentals on doors/vestibules, or published supermarket studies), HVAC, people, and the refrigerated cases.
2. Couple it to the freezer case: case load depends on store temperature and humidity (sensible + latent). Find documented "case credit" / refrigeration–HVAC interaction results.
3. Run a full year with hourly weather for two contrasting climates (e.g. one hot-humid city and one cold city) using the free Open-Meteo archive API (https://archive-api.open-meteo.com/v1/archive). Compare condenser heat rejected inside vs outside the store, and decide when escaping cold is waste (summer: store AC must remove it) and when it is recovered (winter: offsets heating).
4. Quantify: how much does front-door traffic change annual freezer energy? In which months is the waste most wasteful? What is the net effect on total store energy?
5. Figures: monthly freezer energy and store HVAC interaction for both climates; freezer energy vs door openings per hour.
6. Explain what "where you draw the system boundary" means, and why it matters for a bus shelter (cold air spilling onto a pavement full of pedestrians: waste, or service we forgot to count?).""",

"T08_jet_in_crossflow_busstop": """YOUR TASK (T08) — Carry the air-curtain aerodynamics from the freezer to an open-sided bus shelter.

1. A cooler or fan discharges a jet of air into the shelter while wind blows across it. Use documented jet-in-crossflow results (trajectory correlations in terms of the jet-to-crossflow momentum ratio, e.g. Pratte & Baines 1967; Margason 1993 review) and free-jet decay (no wind) to estimate where the cooled air goes and how much stays in the waiting zone.
2. Define a capture fraction phi(wind speed, jet speed, outlet size, distance to people) and compute it for realistic numbers.
3. Compare with our calibration: reading COMAP's table as shelter-average effects implies phi ~0.26 (1.2 kW cooler) and ~0.44 (2.5 kW cooler) at a calm, hot, dry design hour (43 °C, 12% RH, pad efficiency 0.85). Find real spec sheets for portable evaporative coolers (airflow m^3/h, outlet size, power, water use) and check whether jet physics gives similar phi.
4. Plot phi vs wind speed; find the wind speed at which the cooler becomes nearly useless; identify the bus-stop analogue of air-curtain "breakthrough".
5. Recommend shelter design changes that raise phi (orientation to prevailing wind, side panels, outlet direction), with numbers.""",

"T09_occupancy_and_comparison": """YOUR TASK (T09) — The "number of people benefiting" part of the bus-stop model, and a fair way to compare the three systems.

1. Occupancy via queueing / Little's law L = lambda*W. With random passenger arrivals the mean wait is about half the headway, but at long headways passengers time their arrivals. Find the documented headway threshold where arrivals stop being random (e.g. O'Flaherty & Mangan 1970; Bowman & Turnquist 1981; later studies) and build W(headway). Get realistic hourly lambda from published ridership data for at least one real stop or a transit agency's stop-level data.
2. Define people-weighted service = sum over hours of N_t x (cooling felt) x dt, and show how occupancy changes which system is "most efficient".
3. Compare A/B/C with a multi-criteria method from our catalog (composite index or TOPSIS), using criteria such as felt cooling, energy, water use, cost and safety. Get weights two ways (AHP with stated judgement; entropy) and test robustness (weights +/-20%, Monte Carlo).
4. Explain clearly where multi-criteria methods are appropriate here and where they would be "model forcing".""",

"T10_felt_temperature_index": """YOUR TASK (T10) — Put the fan's "feels up to 3 °C cooler" and the coolers' "lowers air temperature up to 5/8 °C" on ONE scale.

1. Explain why these are different quantities: a fan changes air speed at the skin, not air temperature; evaporative coolers lower air temperature but raise humidity.
2. Compare candidate indices: Steadman apparent temperature (Australian Bureau of Meteorology form), NWS Heat Index, Humidex, WBGT, UTCI, SET and the ASHRAE 55 "cooling effect" of elevated air speed. For each: inputs, validity range, and whether it can "see" air speed, humidity and radiation. Use the Python package pythermalcomfort where possible.
3. Invert the ASHRAE 55 cooling effect to find what air speed at the person the fan must deliver for the "3 °C" claim to be true, in dry heat vs humid heat.
4. Show that an evaporative cooler's felt benefit is smaller than its air-temperature drop (because humidity rises) and quantify it.
5. Investigate fans in extreme heat: physiology evidence (e.g. Jay, Morris et al. on electric fans in heat waves) and public-health thresholds (e.g. CDC vs WHO guidance). When does a fan stop helping or start harming? Do UTCI and SET agree?
6. Recommend one index for our model, with a clear justification and its limits.""",

"T11_rail_station_zone": """YOUR TASK (T11) — Revise the bus-shelter model for a semi-open rail-station waiting area (Task 2b).

1. Model the waiting area as a well-mixed zone with heat AND moisture balances: cooling-device supply air; outdoor air exchange through openings driven by wind and by buoyancy (stack effect), using documented natural-ventilation equations (cite, e.g. CIBSE AM10 or ASHRAE Fundamentals); solar gains; heat and moisture from people (ASHRAE sensible/latent gains per standing person — verify values); trains arriving in surges.
2. Check limiting cases: no openings -> zone reaches the supply temperature; huge openings -> zone equals outdoor conditions.
3. Show that at high crowd density people become the dominant heat load (e.g. 200 people vs a 2.5 kW device). Find the crowd size at which cooling efficiency (people-weighted cooling per kWh) peaks, or at which the device is overwhelmed.
4. Decide whether a time-dependent model (ODE) is needed by comparing the zone's time constant with the train headway.
5. Write the three required answers explicitly: what changed from the bus-stop model, why the change was necessary, and how it improved the model's usefulness or accuracy.""",
}

MERGE = """You will receive several research memos (T01–T11) written by separate AI chats for our HiMCM 2026 Problem B team. They share the context below.

YOUR TASK (MERGE):
1. Build one consistency table: every key number that appears in more than one memo, with each memo's value. Flag contradictions and say which value is better supported, and why.
2. List every source cited, de-duplicated, and mark any that look unverifiable or possibly invented.
3. Draw the dependency chain: which memo's outputs feed which model, from Task 1 through Task 2b.
4. Propose the single connected model for Tasks 1 -> 2a -> 2b (one model that grows by one ingredient per step), naming which pieces from which memo it uses and which it drops (and why).
5. List the 10 most valuable non-obvious findings across all memos, each with its number and source memo.
6. List open questions that need a team decision.
Write plainly for a 16-year-old without thermodynamics background.

""" + SHARED

order = ["T02_deflection_modulus_optimum", "T01_air_curtain_jet", "T03_evidence_table",
         "T06_metric_design", "T05_which_aspects_sensitivity", "T08_jet_in_crossflow_busstop",
         "T10_felt_temperature_index", "T04_frost_defrost_optimum", "T07_nested_store_system",
         "T11_rail_station_zone", "T09_occupancy_and_comparison"]
assert set(order) == set(TASKS)

for name, body in TASKS.items():
    (HERE / f"{name}.txt").write_text(SHARED + "\n" + body + "\n")
(HERE / "T99_MERGE_run_last.txt").write_text(MERGE)
print("wrote", len(TASKS) + 1, "prompt files")
for i, n in enumerate(order, 1):
    print(f"{i:2d}. {n}  ({len((HERE / (n + '.txt')).read_text()):,} chars)")
