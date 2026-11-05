# HiMCM 2026 Problem B — extended model options, innovations, and a plan to win

Prepared 4 Nov 2026 (contest Day 1 of 14; window closes 20:00 EST 17 Nov).

**What this is.** Not a solution. An option space for every step of Problem B, with the
specific moves that separate an Outstanding paper from a competent one. Everything marked
**[VERIFIED]** I actually computed or checked against literature during this session — the code
is in `/tmp/claude-0/-home-user-ExampleRepo/a7b0ab5c-e343-5d3f-83da-06d68f7a8990/scratchpad/himcm_b/`
and runs in about 20 seconds. Everything marked **[YOUR CALL]** is deliberately left open,
because it is where your paper earns its own marks.

---

## 0. Read this first: the five findings that are your edge

I built a working model of the problem and ran it against five real summer climates. Five
results came out that I am confident almost no other team — and no unassisted AI write-up —
will have. These are your Outstanding levers. The rest of this document is about how to build
the machinery that produces them.

### Lever 1 — The problem's own table is internally consistent, and you can prove it [VERIFIED]

COMAP gives you three numbers and no data. Everyone treats them as inputs. **Treat them as
calibration targets instead.**

Fix the evaporative pad's saturation efficiency at the manufacturer-typical ε = 0.85 and fit a
*single* free parameter — the shelter's effective open area — so the mixing model reproduces
*both* evaporative claims at one design hour (43 °C, 12% RH, a real Phoenix afternoon):

```
fitted effective open area      : 10.7 m²   (physically sensible for a bus shelter)
capture fraction φ, small/large : 0.255 / 0.438
residual vs the 5 °C claim      : −0.21 °C
residual vs the 8 °C claim      : +0.21 °C
```

Two constraints, one parameter — the fit is over-determined by one, so **that ±0.21 °C residual
is a genuine validation of your physics against the only data COMAP gave you.** Judges read
hundreds of papers that assume. Yours validates, on page 4, against the problem statement
itself. This is the single highest-value hour of work in the whole contest.

### Lever 2 — The bus shelter wastes the same fraction as an open freezer, and the number matches [VERIFIED]

The fitted capture fraction says **74.5% of the small cooler's output never reaches a person**
(56.2% for the large one). Measured infiltration losses through the air curtain of open
refrigerated display cases, from five independent studies: **67–85%** (Brunel thesis 85%;
Howell & Adams 75%; Amin et al. 80%; Kettering/Navaz 70%; Brazilian studies 67–81%).

So Task 1's freezer warm-up is not an analogy you wave at — it is a *quantitative bridge*. The
open bus shelter loses cooling at the same rate as the freezer case COMAP opens the problem
with, and your model derives that independently. Put this in the Summary Sheet. It is the
single most memorable sentence available in this problem.

### Lever 3 — The fan paradox: two standard comfort indices disagree, and the medical literature breaks the tie [VERIFIED]

This is the finding I would build the paper around.

- **SET** (Standard Effective Temperature, the ASHRAE 55 basis) says the fan helps in every
  condition I tested — +1.5 to +2.8 °C equivalent.
- **UTCI** (the outdoor-bioclimatology standard) says the fan **makes things worse** in hot-dry
  air. Sign map of ΔUTCI from the fan:

| T \ RH | 10% | 20% | 30% | 40% | 50% | 60% | 70% | 80% | 90% |
|---|---|---|---|---|---|---|---|---|---|
| 32 °C | −0.2 | −0.1 | 0.0 | +0.1 | +0.2 | +0.2 | +0.3 | +0.3 | +0.4 |
| 38 °C | −0.5 | −0.3 | −0.2 | 0.0 | +0.1 | +0.2 | +0.2 | +0.2 | +0.2 |
| 44 °C | −0.6 | −0.5 | −0.3 | −0.2 | 0.0 | +0.2 | +0.3 | 0.0 | −0.9 |
| 50 °C | −0.9 | −0.8 | −0.5 | −0.2 | +0.1 | +0.2 | −0.6 | −3.6 | −11.4 |

  The fan-harmful threshold is **humidity-dependent**: 30.0 °C at 10% RH, 34.0 °C at 30% RH,
  38.8 °C at 40% RH, never in range at 50–60% RH, then harmful again above 41.5 °C at 90% RH.

- **The physiological literature adjudicates.** Jay, Morris et al. ran human trials: fans were
  beneficial in hot-humid conditions (40 °C/50% RH) but **detrimental at 47 °C/10% RH**, because
  convective heat gain outruns any extra sweat evaporation. Scientific American's summary: in
  the dry condition "almost all the heat stress indicators worsened when a fan was blowing."
  UTCI is right; SET is being used outside its domain.

- **And the public-health thresholds disagree with each other too.** CDC says no fans above
  32.2 °C. WHO says 40 °C. A 2012 Cochrane review found *no empirical evidence either way*.
  My model says both are right — for different humidities — and a single-temperature rule is
  simply the wrong shape of rule.

That gives you a real, defensible, policy-relevant recommendation no one else will make:
**the fan cut-off must be a curve in (T, RH), not a temperature.** My dry-air crossover of
~30–32 °C independently lands on CDC's 32.2 °C, which is a validation point you get for free.

> **Why this wins:** judges reward "honest strengths and weaknesses" and a model "validated
> against at least one real number." This hands you a model-selection controversy, an external
> validation, a safety finding, and a concrete policy output from one piece of analysis.

### Lever 4 — The efficiency *currency* flips the answer, not the climate [VERIFIED]

The research notes predicted the ranking would flip between dry and humid climates. It does —
but the much stronger result is that **the ranking flips depending on what you are buying.**

Bus shelter, always-on, five real summers (person-units per kWh):

| City (mean wet-bulb depression) | η_comfort: fan | evap | η_risk: fan | evap |
|---|---|---|---|---|
| Phoenix (15.8 °C) | **0.499** | 0.073 | 0.026 | **0.279** |
| Las Vegas (16.7 °C) | **0.418** | 0.074 | 0.010 | **0.267** |
| Seville (9.9 °C) | **0.328** | 0.044 | 0.041 | **0.138** |
| Houston (3.6 °C) | **0.497** | 0.035 | **0.155** | 0.042 |
| Singapore (2.6 °C) | **0.388** | 0.027 | **0.254** | 0.023 |

Per unit of **comfort**, the fan wins everywhere by 7–15×. Per unit of **heat-stress risk
removed**, the evaporative cooler wins in dry heat and loses in humid heat. The crossover sits
on the **wet-bulb depression**, somewhere between Seville (9.9 °C) and Houston (3.6 °C).

The mechanism is worth a paragraph of its own: **the fan saturates.** It can make a comfortable
person more comfortable very cheaply, but it cannot pull anyone out of the "very strong heat
stress" band — it only moves air. The evaporative cooler moves the actual air temperature, so
it is the only one of the three that can change which *danger category* a person is in.

**Design rule you can state:** buy fans for comfort; buy evaporative cooling for safety, and
only where the summer mean wet-bulb depression clears roughly 8–10 °C. **[YOUR CALL]** — pin
that threshold down properly with your own sweep; my estimate is bracketed, not resolved.

### Lever 5 — The device barely matters. The crowd and the enclosure do. [VERIFIED]

Task 3 asks you to "identify the characteristics that contribute most to efficient cooling."
That is a variance-based sensitivity analysis, and a tornado chart will not answer it properly
because it misses interactions. Sobol indices (576 model runs, 2 seconds):

**Evaporative cooler, η_comfort:**

| parameter | S1 (direct) | ST (with interactions) |
|---|---|---|
| bus headway | 0.281 | **0.462** |
| open area | 0.374 | **0.421** |
| boardings/day | 0.416 | **0.394** |
| discharge coeff. C_d | −0.021 | 0.046 |
| comfort threshold | 0.010 | 0.024 |
| **pad efficiency** | 0.000 | **0.005** |

**The thermodynamic quality of the cooler is the least important parameter in the entire
model.** What matters is how many people stand in the cooled air, how long they stand there,
and how enclosed the space is.

That conclusion writes Task 5's guidelines for you, and it closes the loop with Task 1 one more
time: the way to make an open freezer efficient was never a better compressor. **It was doors.**

---

## 1. Know what you are beating

**The median Problem B paper** will: define efficiency as °C per kW; compare 3/0.25 = 12,
5/1.2 = 4.2, 8/2.5 = 3.2; conclude the fan is most efficient; add a weighted-sum score with
invented weights; pick two cities; write the memo. It will never mention humidity limits on
evaporative cooling, never model where the cold air goes, and never notice that a "felt"
temperature and an "air" temperature are not the same quantity.

**The AI-written paper** will look much better and fail differently. It will produce fluent
prose, correct-looking LaTeX, Steadman's apparent-temperature formula, a plausible reference
list, and a confident recommendation. Its characteristic failures, all of which judges can
smell:

1. **No calibration.** It uses the given 5 °C and 8 °C as device constants in every climate,
   so its evaporative cooler still delivers 5 °C in Singapore — thermodynamically impossible
   (the maximum there is about 2.6 °C even at ε = 0.85, because the wet-bulb depression is
   only ~3 °C). **[VERIFIED]**
2. **No humidity bookkeeping.** It lowers T and silently leaves RH alone, which deletes the
   entire physical story of the problem.
3. **Formulas as decoration.** Jet-decay and air-exchange equations are stated, never solved,
   never fitted, never sensitivity-tested.
4. **Invented numbers with citation-shaped text.** Plausible references that do not say what
   the paper claims.
5. **No negative results.** Everything confirms the thesis. Real modelling produces surprises;
   its absence is the tell.

**Therefore your whole strategy is: calibrate, validate, and report at least two things that
surprised you.** Levers 1, 3 and 5 are all surprises. Lead with them.

One more structural edge: **Task 5 asks for guidelines *and* a memo *and* a blog post.** Read
the requirement again — "Propose guidelines for the use of cooling systems in your venues"
sits in the main stem of Task 5, before 5a and 5b. Most teams will deliver only the memo and
the blog and silently drop the guidelines. Judges check tasks off a list. Give the guidelines
their own numbered, headed subsection.

---

## 2. The spine: one framework that chains all five tasks

Build one object and reuse it. Every task becomes a different question asked of the same
machinery, which is what makes a paper feel designed rather than assembled.

```
                 weather (T, RH, wind, solar)
                            │
                   ┌────────▼────────┐
  device ─────────▶│  MICROCLIMATE   │  what the air in the shelter actually does
  (ε, Q, P)        │  T_z, RH_z, v,  │  ← psychrometrics + mixing + radiation
                   │  T_mrt          │
                   └────────┬────────┘
                            │
                   ┌────────▼────────┐
                   │  HUMAN RESPONSE │  SET (comfort)  +  UTCI (safety)
                   └────────┬────────┘
                            │
  occupancy ───────────────▶│         N_t from Little's law
                   ┌────────▼────────┐
                   │    SERVICE      │  comfort-hours and risk-hours delivered
                   └────────┬────────┘
                            │
                   ┌────────▼────────┐
                   │   EFFICIENCY    │  service ÷ (kWh, $, litres of water, CO₂)
                   └─────────────────┘
```

The central definition, and the sentence your Summary Sheet should contain:

> **Cooling efficiency is useful comfort and safety delivered to people, per unit of resource
> consumed** — not degrees per kilowatt, because degrees that reach nobody are waste by
> definition, and degrees delivered to someone already comfortable are nearly worthless.

Task 1 motivates it. Task 2a instantiates it on the shelter. Task 2b revises the microclimate
block. Task 3 runs it across venues and climates. Task 4 adds cost and competing objectives.
Task 5 turns it into guidelines.

---

## 3. Task 1 — Understand the problem (the freezer)

Worth 1.5–2 pages. Most teams write half a page of hand-waving. This is cheap marks.

### Option 1A — Three candidate definitions, each killed by a counterexample

The strongest rhetorical structure available. Propose and demolish:

- **D1: energy per hour.** Killed by: a freezer switched off uses zero energy and is perfectly
  "efficient" while the food spoils. Efficiency needs a *service* in the numerator.
- **D2: COP — heat removed per unit work.** Killed by: an open case with a huge air curtain
  removes *more* heat for its electricity (lots of warm ambient air to chill) and scores *better*,
  while doing the same job worse. Thermodynamic efficiency rewards waste here.
- **D3: degrees of temperature drop per kW.** Killed by: degrees where? The cold aisle floor is
  not the product. And a fan delivering "felt" degrees is not commensurable with a cooler
  delivering "air" degrees — which is exactly the trap in COMAP's own Task 2a table.

Arrive at **D4: useful service delivered ÷ resource consumed**, with an explicit *capture
fraction* φ = (cooling reaching the intended target) / (cooling produced).

### Option 1B — Quantify the freezer, don't just describe it [VERIFIED anchors]

Give φ a number for the freezer case so Task 2 inherits a calibrated concept:
infiltration through the air curtain is **67–85%** of the total cooling load across five
studies. So φ_freezer ≈ 0.15–0.33. Then in Task 2 you report φ_shelter = 0.255 and the reader
sees the bridge close.

### Option 1C — The second function: safety, not just cold

A freezer has two jobs: keep food cold *and* keep it safe (above a spoilage threshold is a
cliff, not a slope). Public cooling has exactly the same two-limb structure: comfort (smooth,
saturating) and heat-illness risk (threshold, convex). **Set up the two-currency framework
here, in Task 1, and Lever 4 pays off three tasks later as a planned consequence rather than
a surprise.** This is the structural move that makes the paper feel composed.

> **Answer the actual question.** COMAP asks "Should efficiency depend only on energy use?"
> Answer explicitly: **no** — and list what else: where the cold goes (φ), how many targets it
> reaches, whether it crosses a safety threshold, water, cost, and heat rejected to
> surroundings. Then say "we now build each of these in turn," and do.

**[YOUR CALL]** Whether to include the exergy/second-law argument. It is elegant (compare
delivered cooling to the Carnot minimum) and it impresses, but it costs half a page and risks
looking like showing off. I would include one sentence, not a section.

---

## 4. Task 2a — The bus shelter model

### Option 2A-1 — Common-currency comfort model (**recommended core**)

The problem hands you a mismatch: the fan's 3 °C is *felt*, the coolers' 5/8 °C are *air*.
Everything downstream is wrong until you fix it. Two defensible fixes:

**(i) ASHRAE 55 cooling effect — the standards-based bridge.** CE is *defined* as the number of
degrees you must subtract from both air and radiant temperature, in still air, to reach the
same SET as the elevated air speed produces. That is precisely "how many air-degrees is this
fan worth." Invert it to recover the hidden parameter:

```
to deliver CE = 3 °C the fan must produce, at the person:
   1.25 m/s  at 43 °C / 12% RH        ← the design hour
   1.47 m/s  at 38 °C / 20% RH
   2.99 m/s  at 34 °C / 70% RH
   3.15 m/s  at 32 °C / 80% RH                                    [VERIFIED]
```

**The fan's own specification is climate-dependent**: to keep its promise in humid heat it
needs ~2.5× the air speed, and fan power scales steeply with speed. The "0.25 kW for 3 °C"
claim is a dry-climate claim. Nobody else will notice this.

**(ii) Apparent temperature (Steadman/BoM).** Simpler, hand-computable, fine as a cross-check:
`AT = T_a + 0.33e − 0.70v − 4.00`, with `e = (RH/100)·6.105·exp(17.27T/(237.7+T))`.
Confirmed as the BoM non-radiation form, though note a competing radiation version exists —
state which you used. **Do not make this your primary index**: it treats wind as a linear
penalty and so can never reproduce the fan paradox.

> **Recommendation:** SET as primary (valid in still *and* moving air, handles clothing and
> metabolic rate, is the ASHRAE basis), UTCI as the safety cross-check, AT as a sanity check
> you can do by hand. Then **report that SET and UTCI disagree** — Lever 3.
>
> Note UTCI is formally defined only for wind 0.5–17 m/s, so it cannot describe still air.
> Say so. A stated validity limit is worth more than a silent one.

### Option 2A-2 — Delivered-cooling model: where does the cold actually go?

The capture fraction is the heart of the problem. Mixing of supply air with infiltrating
ambient air:

```
φ = Q_s / (Q_s + Q_inf),     Q_inf = C_d · A_open · v_wind
T_z = φ·T_supply + (1−φ)·T_ambient      and the same for humidity ratio W
```

Humidity must be mixed on **humidity ratio W**, not RH — RH is not conserved under mixing, and
getting this wrong is the commonest silent error in this kind of model.

The evaporative device itself, on a constant-wet-bulb line:
```
T_out = T_db − ε(T_db − T_wb)        W_out = W_in + ε(W_sat(T_wb) − W_in)
```

**The innovation is not the equation — it is fitting it (Lever 1).** Also: remember the
evaporative cooler *also blows air*, so it delivers air movement as well as temperature drop.
Most treatments drop this and understate the coolers.

**[YOUR CALL]** Whether to model the jet/plume decay (`ΔT(x) = ΔT₀·min(1, Kd₀/x)·e^{−ku}`)
explicitly, giving a *spatial* distribution of cooling and letting you ask "how many of the
waiting people are actually in the cooled zone?" It is more realistic and more impressive, but
it adds three uncertain constants. My view: do the well-mixed version first, get the whole
paper working end-to-end, then add the jet model *as the Task 2b revision* if time allows.

### Option 2A-3 — Occupancy: the term that turns out to dominate

```
N_t = λ_t · W = λ_t · H/2        (Little's law; random arrivals wait half a headway)
```

Simple, citable, and — per Lever 5 — the parameter that *actually controls the answer*.
Spend your modelling effort here, not on the pad.

**[YOUR CALL]** The refinement that would be genuinely novel: for long headways passengers
stop arriving randomly and start timing their arrival, so W < H/2. If you model that
(e.g. W = H/2 for H < 10 min, decaying above), you get a non-obvious result — *long-headway
stops have lower occupancy than Little's law predicts, so they are worse candidates for
cooling than they look.* That is a real operational recommendation. I have not tested it; it
is yours to find.

### Option 2A-4 — Radiation and the free-cooling baseline

```
T_mrt = [ (T_a+273.15)⁴ + R_abs/(ε_p σ) ]^{1/4} − 273.15     (Thorsson et al. form)
```

with the shelter roof removing the direct beam and cutting the sky view factor. Why it earns
its place: **shade is cooling at zero kWh, so its efficiency is formally infinite**, which
breaks any pure ratio metric and forces you to discuss the metric's limits. Vanos et al. found
misting cut UTCI by 4.4 °C while misting *plus shade* cut it by 9.7 °C — shade did more than
the device. Include a "no device, better shade" option in every comparison. It will often win,
and saying so is the mark of a team modelling the world rather than the question.

---

## 5. Task 2b — The rail-station revision

COMAP asks three explicit things: *what changed, why it was necessary, how it improved the
model.* Write them as three labelled paragraphs. Teams lose easy marks by burying this.

### Option 2B-1 — Jet → well-mixed zone (the natural structural revision)

Once there are walls and a roof, a free-jet model is the wrong idealisation; a zone heat
balance is right:

```
T_z = [ Q_s T_s + Q_inf T_o + G/(ρc_p) ] / (Q_s + Q_inf)
```

with G the internal gains from people (~100 W sensible each) and solar through openings.
**Check the limiting behaviour explicitly** — no leakage gives T_z = T_s, infinite leakage
gives T_z = T_o. Showing limit checks is a cheap, strong signal of competence.

### Option 2B-2 — The revision that actually matters: people become a heat source [recommended]

At the bus shelter, 3 people are thermally irrelevant. At a rail platform with 200 people in a
confined box, the crowd is a *kilowatt-scale heat load* — 200 × 100 W = 20 kW, which dwarfs
every device in the table. So the revision is not just "add walls":

> **In the open shelter, people are the beneficiaries of cooling. In the semi-open station,
> people are simultaneously the beneficiaries and the dominant heat load.** Cooling efficiency
> therefore becomes *non-linear in occupancy* — and at some crowd density, adding passengers
> reduces the delivered comfort per person even though it raises comfort-hours per kWh.

That is a genuine structural change, not a parameter tweak, and it gives you a crisp "why the
revision was necessary." It also sets up a lovely result: **there is an optimal crowd size for
cooling efficiency.** Find it; put it in the memo.

### Option 2B-3 — Unsteady rather than steady-state

Trains arrive in surges: the platform fills, empties, refills on an 8-minute cycle. A
first-order ODE instead of an algebraic balance:

```
ρ c_p V dT_z/dt = Q_s ρc_p (T_s − T_z) + Q_inf ρc_p (T_o − T_z) + G(t)
```

The time constant τ = V/(Q_s + Q_inf) decides whether the space can recover between trains.
**[YOUR CALL]** This is the most technically ambitious option on the table and would clearly
separate you — but only if you solve it and *use* the answer (e.g. pre-cooling before a train
arrives). Half an ODE is worse than none.

---

## 6. Task 3 — Apply and scale

The task says "at least two venues… different climates **or** different cooling systems." Do
both: it is barely more work once the pipeline exists, and it demonstrates scaling in two
independent directions.

### Option 3-1 — Real multi-climate data [VERIFIED working]

Open-Meteo's archive API gives free hourly T, RH, wet-bulb, wind, direct/diffuse radiation from
1940 for any coordinates, in one call. Summer 2025 means for five cities:

| City | mean T | mean RH | **mean wet-bulb depression** |
|---|---|---|---|
| Las Vegas | 32.8 °C | 17% | 16.7 °C |
| Phoenix | 34.9 °C | 23% | 15.8 °C |
| Seville | 29.1 °C | 43% | 9.9 °C |
| Houston | 28.1 °C | 76% | 3.6 °C |
| Singapore | 27.4 °C | 82% | 2.6 °C |

**Wet-bulb depression is the single climate variable that governs this problem** — it is the
entire physical budget available to an evaporative cooler. Make it the x-axis of your main
figure. Note the ordering it induces is *not* the ordering by temperature: Seville is the
coolest-but-one city and still has 3× Houston's evaporative headroom.

Be ready to defend one API call: my wet-bulb implementation validated against Open-Meteo's own
wet-bulb column at **RMSE 0.42 °C, max error 1.0 °C** over 400 random Phoenix hours. That
validation row belongs in your paper.

### Option 3-2 — The phase diagram (your page-1 figure)

Sweep (T, RH) and colour each cell by the winning device. Occupancy cancels when comparing
devices at the same hour, so it is a clean per-person, per-kW comparison and cheap to compute.
By comfort-per-kWh the fan wins almost the entire plane, ceding only the T ≥ 42 °C, RH ≥ 80%
corner. By risk-per-kWh the map splits along wet-bulb depression.

**One figure that answers "does your model scale?" with a yes you can see.** If you build one
graphic properly this contest, build this one.

### Option 3-3 — Sobol sensitivity, not a tornado chart

See Lever 5. `SALib` does this in ~20 lines and 2 seconds. Report S1 *and* ST and say what the
gap means (interactions). The finding — that pad efficiency is irrelevant and crowd/geometry
dominate — is both the answer to the task as literally asked and the foundation of Task 5.

**[YOUR CALL]** My Sobol ran on one representative Phoenix day with seven parameters. Widen it:
more days, more cities, and add the parameters I held fixed (ε bounds, the comfort threshold
s₀, the UTCI risk exponent). If the ranking survives, say so. If it does not, that is a finding
too — report it.

---

## 7. Task 4 — Competing objectives

### Option 4-1 — Pareto front over four axes, not a weighted sum

Weighted sums with invented weights are what everyone does, and judges discount them. A Pareto
front needs *no* weights: enumerate options (device × count × duty cycle × shade retrofit),
compute (comfort, risk removed, kWh, $), keep the non-dominated set, plot it. Then — and only
then — show how the recommended choice moves as the weight on cost sweeps 0 → 1.

```
C_year = K_cap · [r(1+r)^L]/[(1+r)^L − 1] + p_e Σ P Δt + p_w W
LCOC   = C_year / Σ N_t · (comfort delivered)        [$ per person-comfort-hour]
```

**[YOUR CALL]** Capital costs, tariffs and lifetimes. Use real retailer and utility numbers for
your chosen city and present ranges, not points.

### Option 4-2 — The water axis (the objective everyone forgets)

Evaporative coolers trade electricity for **water** — roughly 10–20 L/hour for a unit this
size. In Phoenix or Las Vegas, water is the binding constraint, not electricity. An efficiency
metric denominated only in kWh will therefore recommend exactly the wrong device in exactly the
cities where it matters most.

That is a sharp, quotable, genuinely important point, and it follows naturally from the
physics you have already built (the evaporated mass is in your humidity-ratio bookkeeping —
you get the litres essentially for free). **[YOUR CALL]** — get real water-rate and
water-stress data for your venue city.

### Option 4-3 — "Air conditioning the environment": read the title as a pun

The problem is called *Air Conditioning the Environment*. Take that literally and model the
**net heat added to the city**:

- A **fan** adds its full 0.25 kW to the environment as heat and removes nothing. It only
  redistributes comfort.
- An **evaporative cooler** converts sensible heat to latent heat. Net sensible load on the
  city falls; humidity rises.
- A **vapour-compression AC** (worth adding as a fourth, hypothetical option) rejects
  *condenser heat + compressor work* right next to the space it cools: it makes the
  surroundings measurably hotter to make one spot cooler.

> **Headline:** cooling an open space does not remove heat from the city — it concentrates
> comfort where people are and dumps the cost on everyone outside the shelter. An honest
> efficiency measure must distinguish *redistributing* heat from *removing* it.

This is the most sophisticated point available in the problem, it falls straight out of Task
1's "should efficiency depend only on energy use," and it gives the blog post its thesis.

### Option 4-4 — Resolve the two-currency conflict honestly

Do not average comfort and safety into one number. State the decision rule:

> Safety is a constraint, comfort is an objective. **Minimise energy subject to keeping UTCI
> below the "very strong heat stress" threshold for the occupied hours; maximise comfort with
> whatever budget is left.**

Lexicographic optimisation, properly motivated, and far more defensible than weights. It also
yields the hybrid recommendation: **fans as the default; evaporative cooling switched in only
above the danger threshold, and only where wet-bulb depression makes it work.**

---

## 8. Task 5 — Guidelines, memo, blog

### 5-stem: the guidelines (do not skip this)

Give it its own headed subsection with numbered, transferable rules. Mine, from the results
above — **replace with your own once you have run your own numbers**:

1. **Enclose before you cool.** Capture fraction is worth more than device efficiency
   (φ = 0.26 → 74.5% waste; raising φ beats raising ε by two orders of magnitude in ST).
2. **Cool where people dwell, not where they pass.** Occupancy and headway dominate every
   sensitivity ranking.
3. **Match the device to the wet-bulb depression.** Evaporative cooling only above roughly
   8–10 °C of depression; below that it is close to useless.
4. **Fan cut-offs must be humidity-dependent.** A single temperature threshold is the wrong
   shape of rule; CDC's 32.2 °C and WHO's 40 °C are each right only for one humidity band.
5. **Shade first.** Zero kWh, and in the literature it outperformed the device itself.
6. **Never run an empty shelter.** [VERIFIED] Switching to "occupied AND SET ≥ 30 °C" saves
   **64% of energy in Phoenix and 95% in Singapore** while retaining 50–57% of delivered
   comfort — and raises comfort-per-kWh from 0.50 to 0.79 (Phoenix) and 0.39 to 1.81
   (Singapore). Real-world hook: Doha's air-conditioned bus shelters reportedly run **24 hours
   a day, 7 days a week** with a 24 °C setpoint. That is the freezer-door-open failure at city
   scale, and it is the single most actionable recommendation in your paper.

### 5a — Memo to the COO (1–2 pages)

Structure: the ask, three findings with numbers, one recommendation with a cost and a saving,
one honest caveat. Business register, no equations, every claim quantified. The caveat matters:
a memo that admits a limitation reads as credible, and judges notice.

### 5b — Blog post

The question is literally "how much cooling are we getting for the energy we use?" Answer it
with a number in the first two sentences: **about a quarter of it reaches a person; the rest
heats the sky.** Then the freezer analogy, which is now quantitative rather than decorative.
Keep equations out entirely.

**[YOUR CALL]** Pick a real venue with real published ridership for the memo. A named stop
with real numbers beats a generic one by a wide margin.

---

## 9. Validation strategy — where most of your marks actually are

Judges reward validation more than complexity. You have five opportunities, which is unusually
many for this kind of problem:

| # | Check | Status |
|---|---|---|
| 1 | One fitted parameter reproduces both COMAP claims | ±0.21 °C **[VERIFIED]** |
| 2 | Implied waste vs. open-freezer literature | 74.5% vs 67–85% **[VERIFIED]** |
| 3 | Your wet-bulb code vs Open-Meteo's wet-bulb column | RMSE 0.42 °C **[VERIFIED]** |
| 4 | Fan harm threshold vs CDC's 32.2 °C guidance | ~30–32 °C dry **[VERIFIED]** |
| 5 | Comfort drops vs Vanos (4.4 °C misting) / Dhariwal (Abu Dhabi) | **[YOUR CALL]** |
| 6 | Zone-model limit checks (no leakage → T_s; infinite → T_o) | **[YOUR CALL]** |

Put these in a single **Model Validation** table. Few high-school papers have one at all.

---

## 10. How to split the work

### Macro — 14 days, 4 people

HiMCM 2026 runs 4–17 Nov, max four students, 25 pages plus a separate AI-use report.

| Days | Milestone | Who |
|---|---|---|
| 1 | All four read the PDF *alone*, then build a shared task checklist. Agree the efficiency definition and write 15 assumptions with a "because" each. | all |
| 1–2 | **Calibration spike (Lever 1).** Nothing else starts until the model reproduces the table. | Modeller + Coder |
| 2–4 | Task 1 written in full; Task 2a microclimate coded and running | Writer / Coder |
| 4–6 | Task 2b revision; data pulled for 4–5 cities | Modeller / Data |
| 6–8 | Task 3: phase diagram + Sobol | Coder / Data |
| 8–10 | Task 4: Pareto, water, net-heat | Modeller / Writer |
| 10–12 | Task 5: guidelines, memo, blog | Writer, reviewed by all |
| 12–13 | Figures redrawn properly; Summary Sheet written (last) and rewritten twice | all |
| 14 | Page-count surgery, reference check, AI-use report, submit **early** | all |

Hard rule: **a complete rough version of all five tasks by Day 7.** A finished 80% paper beats
an unfinished 100% one, and the contest allows partial credit by success level — judges score
what is there.

### Micro — how four people work without blocking each other

The failure mode is three people idle while one debugs. Fix it by agreeing *interfaces* on Day
1, before any code exists. The structure I used works well:

- `core.py` — pure physics, no I/O: psychrometrics, evaporative cooler, mixing, radiation,
  comfort indices. **Owner: Modeller.** Everything else imports this and nothing else.
- `scenario.py` — venues, devices, occupancy, calibration, the efficiency metrics.
  **Owner: Coder.**
- `fetch.py` → `data/{City}.csv` with a **fixed column schema agreed on Day 1**.
  **Owner: Data.** Agreeing the schema early means the Coder can write against fake CSVs
  before any real data exists.
- `analysis.py`, `phase_map.py`, `sensitivity.py` — one script per figure, each writing a PNG
  and a CSV. **Owner: whoever needs that figure.** One script per figure means two people never
  edit the same file.
- The **Writer never waits for code**: they write Task 1, the assumptions table, the
  limitations section and the blog post from Day 2, and slot numbers in later. Prose takes
  longer than people expect and is what judges actually read.

Two process rules worth enforcing: every number in the paper traces to a script that
regenerates it; and whoever computes a number is not the person who writes it up, so it gets
checked by a second pair of eyes in passing.

---

## 11. Honest risks and open questions

- **My fan-paradox thresholds are model output, not measurement.** UTCI's wind term is doing
  the work, and UTCI was built for outdoor meteorological wind, not a fan 2 m from a person.
  Jay et al. support the *direction* strongly; treat my specific crossover numbers as
  indicative and bracket them with sensitivity analysis.
- **The dry-air threshold (~30 °C at 10% RH) is lower than Jay et al.'s tested 47 °C.** The
  direction agrees, the magnitude is not independently confirmed. Say so in the paper — that
  honesty is worth more than the number.
- **ε = 0.85 is a literature assumption, not a given.** The whole Lever 1 fit moves with it.
  I tested 0.70–0.90: the implied waste ranges 67.6%–74.8% and the two independent estimates
  of the leakage parameter agree best (1.2%) at ε = 0.70. Report the range.
- **I did not model the jet/plume spatially**, so "capture fraction" is a well-mixed
  abstraction. Defensible, but a reviewer could push on it.
- **Shanghai failed to download** (API rate limit); five cities is plenty, but if you want an
  East-Asian humid case, re-run `fetch.py` — it retries with backoff now.
- **Device airflows (1.1 and 2.5 m³/s) are my assumptions** from typical portable-cooler
  specs. Get real spec sheets; the fit in Lever 1 depends on their *ratio* more than their
  absolute values.
- **Check my paraphrase against the PDF.** I read the official Problem B PDF directly this
  session, but the authority is the PDF, not this document.

---

## 12. What I left you to do

Deliberately, the things that carry the marks:

1. Choose the two venues and get **real** ridership, geometry and tariffs.
2. Pin the wet-bulb-depression crossover threshold properly (I bracketed it 3.6–9.9 °C).
3. Decide jet model vs well-mixed for Task 2b, and whether to attempt the unsteady ODE.
4. Decide whether the crowd-as-heat-source non-linearity (§5, Option 2B-2) becomes your
   headline revision. I think it should.
5. Build the figures. I produced tables; a phase diagram and a Pareto front are yours.
6. Test the arrival-timing refinement to Little's law — it may be a small original result.
7. Write the Summary Sheet last, twice.

---

## Appendix — running the code

```
cd /tmp/claude-0/-home-user-ExampleRepo/a7b0ab5c-e343-5d3f-83da-06d68f7a8990/scratchpad/himcm_b
python3 fetch.py              # weather, cached to data/ (retries on rate limit)
python3 calibration_check.py  # Lever 1 + 2: internal consistency, implied waste
python3 analysis.py           # Lever 4: five climates x three devices x two venues
python3 phase_map.py          # Lever 4: device-win map, crossover
python3 fan_paradox.py        # Lever 3: SET vs UTCI disagreement map
python3 sensitivity.py        # Lever 5: Sobol indices
```

Dependencies: `pip install pythermalcomfort SALib` (pandas/numpy already present).
`psychrolib` will not build here — `core.py` implements the psychrometrics it needed, validated
to RMSE 0.42 °C against Open-Meteo.

**Treat this code as a reference implementation to check your own against, not as something to
submit.** Rewrite it yourselves: you will understand it better, you will find my mistakes, and
the AI-use report is much easier to write honestly when the code is yours.

---

## Sources

Problem statement: 2026 HiMCM Problem B PDF (read directly this session).

Contest logistics: [COMAP HiMCM/MidMCM](https://www.comap.com/contests/himcm-midmcm)

Comfort models and standards:
- [pythermalcomfort — cooling effect source](https://pythermalcomfort.readthedocs.io/en/stable/_modules/pythermalcomfort/models/cooling_effect.html)
- [ASHRAE 55-2013 Addendum d (elevated air speed)](https://www.ashrae.org/file%20library/technical%20resources/standards%20and%20guidelines/standards%20addenda/55_2013_d_20150521.pdf)
- [ASHRAE 55 overview](https://en.wikipedia.org/wiki/ASHRAE_55)
- [Steadman apparent temperature (BoM form, quoted)](https://community.tempest.earth/t/steadman-apparent-temperature-australian-apparent-temperature/2248)
- [thermofeel — apparent temperature with radiation](https://thermofeel.readthedocs.io/en/latest/guide/apparenttemperature.html)

Fans in heat — the Lever 3 evidence base:
- [Should electric fans be used during a heat wave? (Jay et al.)](https://www.sciencedirect.com/science/article/abs/pii/S0003687014001355)
- [Electric fan use in heat waves (review)](https://www.tandfonline.com/doi/pdf/10.1080/23328940.2016.1211073)
- [Scientific American — fans in muggy vs extreme dry heat](https://www.scientificamerican.com/article/fans-may-be-okay-for-muggy-days-but-avoid-them-in-extreme-dry-heat/)
- [Electric fan effectiveness and thresholds, updated modelling](https://www.sciencedirect.com/science/article/abs/pii/S0378778825015099)
- [Electric fan use with dehydration in extreme heat and humidity (RCT)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12351413/)

Open freezer cases — the Lever 2 evidence base:
- [Kettering University — open display cases (~70%)](https://kettering.edu/news/keeping-cool)
- [Brunel thesis — infiltration ≥85% of load](https://bura.brunel.ac.uk/bitstream/2438/7456/1/FulltextThesis.pdf)
- [Amin et al. 2011 — infiltration of open refrigerated cavities (up to 80%)](https://www.aa.washington.edu/files/faculty/dabiri/pubs/A%20Comprehensive%20study%20on%20the%20effects%20of%20fluid%20dynamics%20of%20air%20curtain%20and%20geometry,%20on%20infiltration%20rate%20of%20open%20refrigerated%20cavities%202011.pdf)
- [Tracer-gas infiltration measurement (Howell & Adams, ~75%)](https://www.aa.washington.edu/files/faculty/dabiri/pubs/Tracer%20gas%20technique%20-%20A%20new%20approach%20for%20steady%20state%20infiltration%20rate%20measurement%20of%20open%20refrigerated%20display%20cases%202008.pdf)

Outdoor cooling practice:
- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- [EnergyPlus — evaporative coolers](https://bigladdersoftware.com/epx/docs/8-1/engineering-reference/page-084.html)
- [Doha AC bus shelters run 24/7](https://thepeninsulaqatar.com/article/24/08/2013/bus-stop-wait-is-not-cool)
- [Qatar Rail — 300 AC bus stops](https://qatar-tribune.com/article/197359/FIRSTPAGE/Qatar-Rail-to-set-up-300-AC-bus-stops-near-Doha-Metro-stations)
- [NUS Sol-Cool solar evaporative bus-stop cooler](https://cde.nus.edu.sg/edic/projects/innovating-for-sustainable-cities/sol-cool/)
