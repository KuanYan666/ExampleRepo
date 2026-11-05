# HiMCM 2026 Problem B: Team Handover Log

**What this is:** everything our team has worked out so far, written so someone who has
never studied physics can pick it up and carry on. If the AI session ends, this file is
the memory.

**Last updated:** 5 November 2026, 16:45 Singapore time (contest Day 2).
**Status:** research phase. Nothing has been written for the actual paper yet.

> ## ⚠️ READ THIS FIRST — corrections from the research agents (5 Nov afternoon)
>
> Nine research memos came back (`sprint_out/T03`–`T11`). They **corrected several numbers
> in Parts B–C below**. Where this box disagrees with the rest of the log, **this box wins**.
>
> | Earlier claim | Corrected | Source memo |
> |---|---|---|
> | Freezer load 2.5 kW for 2.5 m | **2.5–4.5 kW** (real Hussmann F6 scaled: ≈3.6 kW; Tyler ≈4.2 kW) | T03, T04, T05 |
> | Carnot limit 4.8 | **≈3.4–4.0**: the refrigerant boils at ≈ −27 to −35 °C, not −18 °C | T03, T05, T06 |
> | COP 1.7 | **plausible, but ≈1.36 averaged over a defrost cycle**; US rating rules assume ≈1.9, EU ≈1.3 | T03, T04 |
> | Infiltration 67–85 % of a freezer's load | **78–82 % is measured for *chilled* open cases**; no source found for open *vertical freezers* | T03 |
> | Doors save 60 % | **lab: −68–80 % load; real store: −18 % total electricity** (anti-sweat heaters eat the saving) | T03, T06 |
> | Shop door raises freezer load 8–27 % | **+0.4–1.3 % per year** (store AC dampens humidity). The door's real cost is store heating/cooling: +3–8 % | T07 |
> | Door extra load: 73 % water / 27 % heat | **≈90 % water** | T07 |
> | Net heat into shop = electricity | **only for plug-in cases**. Supermarket norm (remote rooftop condensers): each case *removes* ≈2 kW from the store | T03, T06, T07 |
> | Winter escaping cold offsets heating | **backwards for remote condensers**: it *raises* winter heating | T06, T07 |
> | Frost time constant 6 h | **8–12 h** for open low-temp cases; **optimal defrost ≈12 h** (heater-limited; energy optimum ≈18 h) | T04 |
> | Fan needs 1.25 m/s to "feel 3 °C" | **code bug**: proper ASHRAE method → **≈0.3 m/s vs still air**; vs a real breezy shelter, **no fan reaches 3 °C** (best 0.7–1.3 °C) | T10 |
> | `core.py` UTCI input | **bug**: passes air speed at the person into an input expecting wind 10 m up | T10 |
> | Bus-shelter capture 0.26/0.44 from fitting COMAP's table | **real coolers move 3–7× more air per kW than assumed**; jet physics gives 0.08/0.14 with our airflows, 0.38 for a real 1.1 kW cooler | T08 |
> | Optimal crowd size on the platform | **none**: efficiency keeps rising; devices get *overwhelmed* instead (Houston: ≈38 people for cooler B) | T11 |
> | Crowd 20 kW vs 2.5 kW device | **compared heat with electricity**; cooler C delivers 16–53 kW of cooling | T11 |
> | Occupancy changes the best system | **cannot change the per-kWh ranking**; it changes total service and the value of a presence sensor | T09 |
>
> ### Strongest new results (keep these)
> - **Efficiency measure decided (T06):** kg of food × hours at ≤ −15 °C, per kWh, with
>   three rules (score a full defrost cycle; rate at standard store conditions; zero credit
>   outside the safe band). Bus-stop version: person × °C of felt relief × hours per kWh.
> - **Which aspects belong (T05):** machine and air curtain dominate; then case temperature,
>   store climate, anti-sweat heaters. Defrost, lights, fans, insulation barely matter.
> - **Official metrics ignore** store climate, store HVAC interaction and the food (T03).
>   Open freezers are allowed ≈4.5× more energy per ft² than glass-door ones in the US.
> - **Bus-stop "breakthrough" (T08):** cooling fails when U₀·d / (U_wind·L) < 0.59 → about
>   4 m/s wind at a weather mast; 12–30 % of hot hours in Phoenix/Las Vegas/Seville. Blow
>   along the shelter's long axis: 2.2× more captured.
> - **Felt index (T10):** SET as "felt temperature drop", plus a safety check (UTCI /
>   body-core model). "Air 5 °C cooler" feels like only 1.7–2.3 °C cooler.
> - **Rail station (T11):** heat + moisture zone balance; no ODE needed (air turns over in
>   1–1.5 min); in humid Houston a recirculating evaporative cooler makes it feel *hotter*.
> - **TOPSIS (T09):** the winner depends on one value judgement, the weight on heat safety
>   (switch at 0.23–0.54). So show a Pareto front in Task 4.
>
> **Still running at 16:45:** T01 (air-curtain jet physics) and T02 (deflection modulus,
> optimal curtain speed). Their memos will appear in `sprint_out/` if they finish.
> **Data:** see `DATA_INVENTORY.md`. **All cited URLs:** `all_urls.txt`.

> **How to read this log**
> - Part A explains the contest and the problem.
> - Part B teaches the physics from zero. Read it once slowly.
> - Part C covers what we found, task by task, with every number and where it came from.
> - Part D covers how we'll build the models and the paper.
> - Part E is the practical side: files, code, how to run things, who does what.
> - Part F is the history of how we got here, including mistakes we caught.
>
> Words in **bold** the first time they appear are defined in the Glossary (Part B, §B9).
> Numbers marked **[checked]** were computed or verified in this session.
> Numbers marked **[assumed]** are typical values we picked and still need a source.

---

# PART A — The contest and the problem

## A1. The contest in one paragraph

HiMCM is COMAP's High School Mathematical Contest in Modeling. Teams pick one problem and
have **14 days**. This year that's **4 November to 17 November 2026**, with the PDF due by
**9:00 pm EST on 17 November** (the contest window closes at 8:00 pm EST). We submit **one PDF of
at most 25 pages**: summary sheet, table of contents, the solution, the memo, the blog post
and references. A separate **AI-use report** is required if we use AI. It doesn't count
toward the 25 pages, but it must contain our prompts and the AI's outputs. **No help
from anyone outside the team**: no teachers, no experts, no surveys.

How judging works (from our Model Catalog): at least two judges read each paper and place it in
Successful Participant, Honorable Mention, Meritorious, or Finalist. Finalists go to a final
panel that picks Outstanding. In 2025: 1,091 papers, 105 Finalists, 8 Outstanding.
**What the 2025 judges said decided Problem B's top papers:** "later work built on earlier
work". In other words, one model that grows, not several disconnected ones.

## A2. Our problem in plain words

**Problem B: "Air Conditioning the Environment: Modeling Energy Waste in Public Cooling."**

Some public places get cooled even though they're open to the outside air: bus stops,
train platforms, stadium walkways, outdoor café patios. A lot of the cold just blows
away. COMAP compares this to leaving the freezer door open. We're asked to build a way to
measure how well the cooling actually serves people, and to give advice.

### The five tasks

**Task 1 (Understand).** Open freezer cases in supermarkets use energy all the time.
- What aspects of a freezer case should go into a measure of cooling efficiency?
- Should efficiency depend **only** on energy use? *(This is a yes/no question. We must answer it.)*
- Justify what we include, and use it to motivate our later models.

**Task 2a (Bus stop).** A city wants to cool an open-sided bus shelter. Three options:

| System | What COMAP says it does | Power |
|---|---|---|
| A. Fan | "makes space **feel** up to 3 °C cooler" | 0.25 "kW/hr" |
| B. Evaporative cooler | "lowers **air** temperature up to 5 °C" | 1.2 "kW/hr" |
| C. Large evaporative cooler | "lowers **air** temperature up to 8 °C" | 2.5 "kW/hr" |

Build a measure of cooling efficiency for the bus stop. COMAP suggests considering the size of the cooled
area, the climate, energy use, and **how many people benefit**.

**Task 2b (Train station).** Change the model for a partly-enclosed rail-station waiting
area. We must say clearly **what changed, why, and how it made the model better.**

**Task 3 (Apply).** Use the model on at least two real venues in different climates or with different systems.
Find what makes cooling efficient.

**Task 4 (Extend).** Balance cooling, visitor experience, energy and cost.

**Task 5 (Share).** Write **guidelines** + a **1–2 page memo** to the company's Chief
Operations Officer about one venue + a **public blog post** answering "How much cooling
are we getting for the energy we use?"

### Three traps hidden in COMAP's table

1. **"kW/hr" is not a real unit.** kW is already "energy per second". We read it as the
   machine's power draw in kW. We'll say so in one polite sentence in the assumptions.
2. **The fan's number is a feeling; the coolers' numbers are thermometer readings.**
   "Feels 3 °C cooler" and "air is 5 °C cooler" are different kinds of quantity. Comparing
   3/0.25 with 5/1.2 is comparing apples and oranges. We must convert one into the other first.
3. **The column is headed "Effect on Shelter".** So the 5 °C and 8 °C are what reaches
   the shelter after the cold air has mixed with the wind, not what comes out of the
   machine. This turned out to be very useful (see C4).

## A3. The spine of our paper (decided)

This came from a teammate's question: *"When freezing food, is it apparent temperature or
actual?"* That question turned out to organise the whole paper.

| Step | What we're cooling | What it cares about | What we need to measure it |
|---|---|---|---|
| **Task 1: freezer** | food | **actual** temperature only (food doesn't sweat or feel wind) | a thermometer |
| **Task 2a: bus stop** | one person | **felt** temperature (people sweat; wind and sun matter) | temperature + humidity + wind + sun |
| **Task 2b: train station** | a crowd | felt temperature **and** the crowd's own body heat | all of the above + a headcount |
| **Task 3: venues** | the same model in other climates | does it still work? | real weather data |

**Rule we agreed:** each step adds **exactly one new ingredient**. If a step adds nothing
new, it's padding and wastes pages.

Useful one-liners that capture it:
- *A fan makes food cool down **faster**, but not colder.*
- *A fan makes a person **feel** cooler without cooling the air at all.*
- *On a platform the people become part of the problem, not just the point of it.*

Figure: `himcm_b/figs/fig7_what_changes.png`

---

# PART B — The physics, from zero

Nobody on the team needs prior thermodynamics. Read these in order; each builds on the last.

## B1. Power vs energy

- **Energy** is an amount of work or heat. Units: joules (J), or kilowatt-hours (kWh).
- **Power** is energy per second. Units: watts (W). 1 W = 1 joule every second. 1 kW = 1000 W.
- **Energy = power × time.** A 1 kW heater running for 1 hour uses 1 kWh.

So "0.25 kW" is how fast the fan uses electricity. Run it for 10 hours and it uses
0.25 × 10 = 2.5 kWh.

## B2. Temperature and the two kinds of heat

**Sensible heat** is heat that changes temperature. You can sense it with a thermometer.

> Q = m × c × ΔT
> - Q = heat (kJ)
> - m = mass (kg)
> - c = specific heat, i.e. how much heat it takes to warm 1 kg by 1 °C. Air: 1.006 kJ/(kg·°C). Water: 4.18.
> - ΔT = temperature change (°C)

**Latent heat** is heat that changes state (liquid ↔ gas, liquid ↔ ice) *without*
changing temperature. A boiling kettle stays at 100 °C while you keep heating it. All
that extra heat goes into turning water into steam.

> Q = m × L
> - L for evaporating water ≈ **2450 kJ/kg**
> - L for turning vapour straight into ice ≈ **2835 kJ/kg** (= 2501 to condense + 334 to freeze)

**The key fact:** warming 1 kg of water by 1 °C takes 4.18 kJ. Evaporating it takes about
2450 kJ, roughly **600 times more**. That's why evaporation is such a strong cooler. The
energy has to come from somewhere, so it gets pulled out of whatever is nearby.

## B3. Air carries invisible water (humidity)

Air always holds some water vapour, which you can't see. Warm air can hold much more than
cold air. The maximum roughly doubles for every 10 °C rise.

Two ways to describe it:
- **Relative humidity (RH)** is how full the air is, as a percentage of its maximum at that
  temperature. It's what weather reports give. **Trap:** cool the air and RH goes up even
  though no water was added, because the maximum dropped.
- **Humidity ratio (W)** is grams of water per kilogram of dry air. It counts actual water.
  **Always do the physics with W, not RH.** When two air streams mix, average their W,
  never their RH. In one of our test cases the right answer was 20% RH and the wrong
  method gave 28% [checked].

Surprising example [checked]: Phoenix at 43 °C and 12% RH holds 6.4 g/kg of water.
Singapore at 32 °C and 80% RH holds 24.3 g/kg, almost four times more. The hotter city is
the drier one.

## B4. Wet-bulb temperature: the limit of evaporative cooling

Wrap a wet cloth around a thermometer and blow air on it. Water evaporates and cools the
cloth, while the warm air heats it back up. It settles where the two balance. That reading is
the **wet-bulb temperature (T_wb)**: the coldest you can get by evaporating water into that air.

**Wet-bulb depression = air temperature − wet-bulb temperature.** This is the entire
"budget" for any evaporative cooler. No machine can beat it.

Average summer 2025 values [checked, from Open-Meteo hourly data]:

| City | Avg temp | Avg RH | **Cooling budget (wet-bulb depression)** |
|---|---|---|---|
| Las Vegas | 32.8 °C | 17% | **16.7 °C** |
| Phoenix | 34.9 °C | 23% | **15.8 °C** |
| Seville | 29.1 °C | 43% | **9.9 °C** |
| Houston | 28.1 °C | 76% | **3.6 °C** |
| Singapore | 27.4 °C | 82% | **2.6 °C** |

So COMAP's "up to 5 °C" evaporative claim is **physically impossible in Singapore**. The
ceiling there is 2.6 °C on an average summer hour. Figures: `figs/fig2_cooling_budget.png`,
`figs/fig3_psychrometric.png`.

## B5. How a freezer (or any air conditioner) works

A freezer **doesn't make cold. It moves heat** from inside to outside. Like bailing water
out of a leaky boat, the electricity pays for the bailing.

The loop (figure `figs/fig8_how_it_works.png`, left panel):
1. **Boil.** A special liquid (the refrigerant) boils at about −25 °C inside the case.
   Boiling needs heat, so it grabs heat from the food and air. They get cold.
2. **Squeeze.** A pump (the **compressor**) squeezes the gas. Squeezing makes it hot, hotter
   than the room. (A bike pump gets warm for the same reason.)
3. **Condense.** The hot gas flows through coils on the back (the **condenser**). Because it's
   hotter than the room, heat flows out by itself and the gas turns back into liquid.
4. **Release.** The liquid squirts through a narrow valve, expands and goes cold again. Back to step 1.

**The trick:** heat never flows from cold to hot on its own. So you squeeze the gas
until it's hotter than the room, and then the heat leaves naturally. Squeezing is what costs
electricity. The bigger the temperature "climb" (here −18 °C up to about 35 °C), the harder you
must squeeze.

## B6. Energy is conserved, and there's a speed limit

**Energy conservation (bookkeeping):**
> heat pulled out of the case + electricity used = heat dumped out the back
>
> 2.50 kW + 1.47 kW = 3.97 kW [checked for our baseline case]

Nothing disappears. The freezer relocates heat.

**COP (coefficient of performance)** = heat moved ÷ electricity used. Our baseline freezer:
2.50 ÷ 1.47 ≈ **1.7** [assumed typical value]. More heat out than electricity in isn't magic,
because it's *moving* heat, not making it.

**The physics speed limit (Carnot limit):**
> COP_max = T_cold ÷ (T_hot − T_cold), with temperatures in kelvin (°C + 273.15)
>
> = 255.15 ÷ (308.15 − 255.15) = **4.81** [checked]

A real freezer at 1.7 reaches about **35% of the best physics allows**. No engineering can
beat 4.81 for this temperature climb.

## B7. The evaporative cooler and the fan

**Evaporative cooler** = fan + wet pad + small water pump. Hot dry air blows through the
wet pad, water evaporates, and the energy needed comes out of the air, so it leaves cooler
and damper.
> Outlet temperature = T_air − ε × (T_air − T_wb)
> - ε = **saturation efficiency**, how much of the budget a real pad captures (0.7–0.9; we use 0.85)

Phoenix design hour (43 °C, 12% RH) [checked]: outlet 24.2 °C at 75% RH, an 18.8 °C drop,
using about **34 litres of water per hour**. Same machine in Singapore: a 2.6 °C drop, about
5 L/h. Same electricity, seven times less cooling.

**Deep point [checked]:** the evaporative cooler removes **no energy** from the air. Total
energy per kg of air stays about the same (59.9 → 60.6 kJ/kg). It just swaps "hot and dry"
for "cooler and damp". The heat is still there, hidden in the water vapour.

**Fan:** changes *nothing* about the air. Same temperature and humidity in and out. Your
body wraps itself in a thin layer of warm, damp air. A fan strips that layer off, so your
sweat evaporates faster, and that cools you.

**The catch:** skin is about 35 °C. If the air is hotter than that, the fan blows heat
*into* you, like a fan oven. Table [checked], heat flowing from air to skin per square
metre of skin:

| Air temp | Still air | With fan | Fan's effect |
|---|---|---|---|
| 28 °C | −28 W/m² | −66 W/m² | cools you |
| 35 °C | 0 | 0 | nothing |
| 43 °C | +32 W/m² | +76 W/m² | heats you |

(Negative = skin loses heat, which is good in heat.) Human trials (Jay, Morris et al.)
found fans **help at 40 °C / 50% RH** but **hurt at 47 °C / 10% RH**. Public-health advice
disagrees: CDC says no fans above 32.2 °C, WHO says 40 °C.

**The three machines on one ladder:**

| Machine | Does it really remove heat from the place? |
|---|---|
| Freezer / air conditioner | **Yes**, carries it elsewhere (and dumps extra heat there) |
| Evaporative cooler | **No**, swaps heat for humidity |
| Fan | **No**, moves no heat at all; works on your skin |

## B8. Time constants: how fast things respond

Every part of a system takes some time to react to a change. That's its **time constant (τ)**:
> τ = heat capacity ÷ rate of heat exchange

Rule: if something reacts **much faster** than how often our data arrives (weather data
is hourly), it's already settled, so plain algebra works. If it reacts on a **similar**
timescale, it needs a **differential equation** (an equation describing how it changes over
time). Figure: `figs/fig10_timescales.png`.

## B9. Glossary

| Term | Plain meaning |
|---|---|
| Air curtain | Thin sheet of cold air blown downward across an open freezer's front, acting as an invisible wall |
| AHP | A way to turn human judgements ("cost matters 3× more than speed") into weights |
| Capture fraction (φ) | Share of the cooling produced that actually reaches its target (food or people) |
| Carnot limit | The maximum possible COP that physics allows for a given temperature climb |
| Compressor / condenser / evaporator | The pump / the hot coils outside / the cold coils inside, in a fridge |
| COP | Heat moved ÷ electricity used |
| Deflection modulus (Dm) | A number comparing an air curtain's push against the forces trying to bend it (Hayes & Stoecker 1969) |
| Dew point | Temperature at which air becomes saturated if cooled without adding water |
| Differential equation (ODE) | An equation that says how fast something changes |
| Elasticity | % change in output for a 1% change in an input; ranks which inputs matter |
| Entrainment | A jet of air dragging surrounding air into itself as it moves |
| Felt / apparent temperature | How hot it feels to a person, combining air temp, humidity, wind, sun |
| Infiltration | Warm outside air leaking into the cold space |
| Latent heat | Heat that changes state (evaporating, freezing) without changing temperature |
| Little's law | Average number of people waiting = arrival rate × average waiting time |
| Monte Carlo | Run the model thousands of times with random inputs to see the spread of results |
| Pareto front | Set of options where you can't improve one goal without hurting another |
| Relative humidity (RH) | How full the air is with water, as % of its max at that temperature |
| Humidity ratio (W) | Actual grams of water per kg of dry air |
| Reynolds number | Tells whether airflow is smooth (laminar) or chaotic (turbulent) |
| Saturation efficiency (ε) | How much of the wet-bulb budget an evaporative pad actually achieves |
| SET / UTCI | Two scientific "feels like" temperatures; SET used by ASHRAE indoors/semi-outdoors, UTCI for outdoor heat stress |
| Sensible heat | Heat that changes temperature |
| Sobol index | Share of the output's uncertainty caused by each input (accounts for interactions) |
| Stock-and-flow | A model of a quantity (the stock) with inflows and outflows, like a bathtub |
| Time constant (τ) | How long something takes to respond to a change |
| TOPSIS | Ranks options by closeness to an imaginary "best on everything" option |
| Wet-bulb temperature | Coldest temperature reachable by evaporating water into the air |
| Wet-bulb depression | Air temp − wet-bulb temp = the evaporative cooling budget |

---

# PART C — What we found, task by task

## C1. Task 1: the supermarket freezer (our foundation, most work so far)

### C1.1 Where the freezer's energy goes [checked]

Baseline: a 2.5 m open vertical freezer case, case air −18 °C, shop 24 °C / 55% RH,
total cooling load 2.5 kW [assumed typical], COP 1.7 [assumed typical].

| Where the heat comes from | kW | Share |
|---|---|---|
| Warm air falling in: cooling it down (sensible) | 1.15 | 46% |
| Warm air falling in: freezing out its water (latent, becomes frost) | 0.73 | 29% |
| Conduction through the insulated walls | 0.15 | 6% |
| Radiation through the opening | 0.15 | 6% |
| Lights, fans, defrost heaters | 0.33 | 13% |
| **Total** | **2.50** | |

**The open front ("infiltration") is 75% of the load.** The literature says 67–85%
(Howell & Adams 1991 ~75%; Amin et al. 2011 up to 80%; Kettering University ~70%; a Brunel
thesis ≥85%). We haven't yet read all of these ourselves, so **verify before citing**.

Per kilogram of shop air that falls in [checked]: 42.3 kJ to cool it, 26.7 kJ to freeze its
water out. **Almost 40% of the open-front cost is water, not temperature.**

Figure: `figs/fig6_freezer.png`

### C1.2 The two ways to save energy [checked]

| Lever | What it means | Saving | Limit |
|---|---|---|---|
| Better machine | raise COP from 1.7 to 2.0 | 15% | capped by physics at 4.81 |
| Stop the leak | fit doors, cutting infiltration by 80% | **60%** | no physics cap |

**Task 1 thesis:** improving the machine is capped by physics. Removing the load that
should never have existed isn't capped at all.

### C1.3 The shop door affects the freezer [checked]

The freezer never touches outdoor air, but the shop's front door lets humid air in. That
raises the shop's humidity, which raises the freezer's frost load:

| Shop air | Load per kg of air falling in | vs dry winter store |
|---|---|---|
| Dry winter store 24 °C / 45% | 63.6 kJ | — |
| Baseline 24 °C / 55% | 69.0 kJ | +8% |
| Busy doors, summer 24 °C / 65% | 74.3 kJ | +17% |
| Hot day, doors open 26 °C / 65% | 80.8 kJ | **+27%** |

When the door opens (outdoor 32 °C / 60%), the extra freezer load comes **73% from
moisture and only 27% from temperature** [checked]. Per unit change, +1 g/kg of shop humidity
adds 4.1% to the load, while +1 °C adds only 1.5%.

**Big idea:** the system is **three boxes inside each other** (outdoors → shop → freezer
case), and every wall leaks. The bus stop has the same structure (outdoors → shelter →
person). Figure: `figs/fig9_nested.png`

### C1.4 Is the escaping cold really "waste"? [checked]

Energy bookkeeping: the case takes 2.50 kW out of the aisle air and the condenser dumps
3.97 kW. If the condenser is inside the shop, the **net heat added to the shop = +1.47 kW,
exactly the electricity used**. Nothing else is possible.

- **Summer:** the shop's air conditioning must remove that heat. That's real waste (about
  0.49 kW of extra electricity at an AC COP of 3).
- **Winter:** it offsets the shop's heating. **The "waste" is recovered.**
- **Bus shelter:** the escaping cold goes to the sky. Always lost.

So **waste has a sign**, and it depends on the season and on where you draw the box.
Bonus twist: frozen-food aisles are known to feel uncomfortably cold to shoppers, so there
the escaping cold has *negative* value. For a bus shelter, cold spilling onto a crowded
pavement might have *positive* value for pedestrians. We need to decide who counts.

### C1.5 Which parts need differential equations? [checked]

| Part | Time constant | What to do |
|---|---|---|
| One door opening | 8 s | too fast, so replace with an average rate |
| Air inside the case | 54 s | already settled, so use algebra |
| Shop air | 30 min | borderline |
| **The food itself** | **67 min** | **differential equation** (and it's the service) |
| **Frost on the coil** | **6 h** | **differential equation** (efficiency rises and falls in a sawtooth) |

So the freezer model is a **hybrid**: mostly algebra, with two differential equations (food
temperature, frost mass). Our weather data is hourly, so simulating every second would be
fake precision.

### C1.6 The full answer to "What aspects should be considered?"

Organised as three questions, which we'll reuse for every later task:

**Q1. What's on top (the service delivered)?**
- Temperature held *(obvious)*
- Amount of product *(obvious)*
- Food kept **safe and sellable**, not just cold. Spoilage is a cliff, not a slope.
- **Stocking level:** a half-empty case costs nearly the same as a full one.
- **Freezer burn:** drying the air also dries the food. The same process is both a cost and a harm.
- **Night blinds:** no customers at night, but the food still has to stay safe. So
  service ≠ people present. This is where the freezer differs from the bus stop, and
  pointing out where our own analogy breaks earns marks.

**Q2. What's on the bottom (the resources used)?**
- Electricity *(obvious)*
- **Defrost energy**, plus the heat defrost dumps *into* the case (you pay twice)
- **The case's own fans and lights sit inside the cold box**, so all their electricity
  becomes extra load
- **The shop's air conditioning** that must remove the condenser heat. The freezer's true
  bill isn't on the freezer's meter.

**Q3. Where's the boundary?**
- The case opening *(obvious)*
- **The shop's front door** (+27%)
- **Position in the aisle** (near the entrance vs in the middle)
- **Season**, which flips the sign of waste
- **Customers' arms** reaching in and breaking the air curtain. The load depends on
  shopper behaviour, the freezer's version of ridership.

Plus two about **time**:
- **Efficiency is a sawtooth:** frost builds, performance drops, defrost, repeat.
- **The freezer is a battery:** frozen food can coast for about an hour, so the compressor could run
  when electricity is cheap or clean. (A bus shelter has no thermal mass, which is a finding in itself.
  Idea: a chilled bench or phase-change material.)

### C1.7 Ways to measure efficiency (still to choose)

| # | Type | Example | Strength | Weakness |
|---|---|---|---|---|
| 1 | Ratio | person-degrees per kWh | simple, standard | breaks when energy = 0 (e.g. shade: divides by zero) |
| 2 | Difference | value of service − price × energy | can compare against "do nothing" | needs a price on comfort |
| 3 | Benchmark | actual ÷ ideal (e.g. same case with doors) | 0–1, easy to read | must define "ideal" |
| 4 | **Marginal** | extra service from the next kWh | answers "should it be on right now?" | needs a smooth model |
| 5 | Capture fraction | 26% reached a person | shows where the cold goes | ignores how much it helped |
| 6 | Worst-off person | the person at the back is still at 41 °C | safety-focused | ignores everyone else |
| 7 | Binding resource | per litre of water in Phoenix | right resource for the place | changes by location |

The AI's suggestion: **capture fraction for diagnosing** (what's wrong) + **marginal for
operating** (what to do). **Not decided yet.**

### C1.8 Air-curtain aerodynamics (our physics teammates' focus)

The open front is sealed only by a thin downward jet of cold air. Two documented models:
- **Jet entrainment theory** (Morton, Taylor & Turner 1956): a moving jet drags surrounding
  air into itself. The warm shop air it drags in is the infiltration.
- **Hayes & Stoecker deflection modulus (1969)**: a number comparing the curtain's push
  against the buoyancy (density difference) trying to bend it. One source puts the stable
  range for open vertical cases at about 0.12–0.25 [not yet verified]. Below a critical push,
  **"breakthrough"** happens: the curtain fails and lets in **more** warm air than having no
  curtain at all.

Promising idea: infiltration vs curtain speed should be **U-shaped**. Too slow and it breaks
through; too fast and it drags in more warm air and the fan costs more. So there should be an
**optimal curtain speed**. Research agents T01 and T02 are working on this now (see E3).

## C2. Task 2a: bus stop (early exploration, NOT final)

These results came from early exploratory code. Treat them as promising leads, not settled
answers.

**C2.1 Fitting COMAP's own table [checked].** We took pad efficiency 0.85 (typical) and a
hot dry design hour (43 °C, 12% RH), and fitted **one** unknown: the shelter's effective open
area. Result: 10.7 m², which reproduces **both** the 5 °C and the 8 °C claims within ±0.21 °C.
Two targets and one free parameter means the fit is a genuine test, not just curve-fitting.
- Implied **capture fraction:** 0.26 (small cooler), 0.44 (large cooler)
- So about **74% / 56% of the cooling is lost** to the open air
- That 74% sits inside the freezer literature's 67–85%. **The bus shelter wastes cold at the same
  rate as an open freezer.**
- Caveat: tested ε from 0.70 to 0.90. The waste ranges 67.6%–74.8%. Device airflows
  (1.1 and 2.5 m³/s) are assumed; we need real spec sheets.

**C2.2 Fan's hidden requirement [checked].** For the fan to really make you feel 3 °C
cooler (using the ASHRAE 55 "cooling effect" method), it must blow about **1.25 m/s** at you in
dry heat, but about **3 m/s** in humid heat. Its claim is effectively a dry-climate claim.

**C2.3 Which system wins depends on what you're buying [exploratory].** Per unit of
**comfort**, the fan wins almost everywhere (it's cheap). Per unit of **heat danger removed**,
evaporative coolers win in dry cities (Phoenix, Las Vegas, Seville) and the fan wins in
humid ones (Houston, Singapore).

**C2.4 Two "feels like" scales disagree about fans [exploratory].** SET says the fan
always helps. UTCI says it **hurts** in hot dry air (above about 30–34 °C when RH is below 30%),
matching the human-trial evidence. The safe limit for fans looks like a **curve in
temperature and humidity**, not one temperature.

**C2.5 Smart switching [exploratory].** Running the cooler only when someone is waiting
**and** it's hot saved 64% of energy in Phoenix and 95% in Singapore, while keeping roughly half
the comfort. Real-world hook: Doha's air-conditioned bus shelters were reported in 2013 to
run 24 hours a day.

**C2.6 What matters most [exploratory].** A global sensitivity analysis (Sobol) on the
bus-stop model found the **pad's efficiency barely matters** (total index about 0.005).
**Bus frequency, number of riders and how open the shelter is** dominate. Enclose before you
cool, and cool where people actually wait.

## C3. Task 2b: train station (planned)

The new ingredient: **people become a heat source.** Three people give off about 0.3 kW
(negligible). 200 people give off about **20 kW**, eight times the biggest cooler in the table.
Expected result: efficiency stops growing with crowd size and may peak at some crowd
level, which the bus-stop model can't show. Research agent T11 is working on this.

## C4. Tasks 3–5 (planned outline only)

- **Task 3:** run the same model on two venues in contrasting climates (dry-hot vs
  humid-hot). Hourly weather from Open-Meteo (free). Use sensitivity analysis to say what
  drives efficiency.
- **Task 4:** list options (device, number of units, hours, shade), compute comfort,
  safety, energy, water, cost, and show a **Pareto front** instead of a weighted sum. Consider
  "safety first, then comfort": keep people out of dangerous heat, then maximise comfort
  with what's left.
- **Task 5:** numbered **guidelines** (easy to forget; COMAP asks for them separately
  from the memo and blog), a memo with numbers and one honest caveat, and a blog post answering
  "how much cooling do we get for our energy?" in its first two sentences.

---

# PART D — Models and how the paper fits together

## D1. Rule for choosing models (from our Model Catalog)

Pick models by the **verb** in each task, never because a model looks impressive.
Judges punish "model forcing".
- "measure / define / evaluate" → **Layer 1 (Measure)**
- "predict / explain / how will it change" → **Layer 2 (Explain / Simulate)**
- "recommend / design / allocate" → **Layer 3 (Decide)**

## D2. Which models fit where

| Task | Model | Why it fits | Why others don't |
|---|---|---|---|
| 1 | **Stock-and-flow energy balance** | the freezer is a bathtub of heat with inflows and an outflow | — |
| 1 | **Elasticity + Sobol sensitivity** | Task 1 asks us to *justify which quantities* to include. An aspect with near-zero elasticity doesn't belong | AHP / TOPSIS / entropy need **many items to rank**; there's only **one** freezer |
| 1 | **Hayes & Stoecker deflection modulus** (from literature) | the standard air-curtain model | — |
| 1 | **Frost differential equation + optimal defrost interval** | frost is slow (6 h), so it needs a differential equation; the best defrost interval is a classic optimisation | — |
| 2a | **Psychrometrics + mixing (capture fraction)** | where the cold goes | — |
| 2a | **Felt-temperature index** (SET / UTCI / apparent temperature) | converts "feels 3 °C" and "air 5 °C" to one scale | — |
| 2a | **Queueing / Little's law** | how many people are waiting | — |
| 2a | **Composite index or TOPSIS** | now there ARE 3 items to compare | — |
| 2a | **Jet-in-crossflow** (from literature) | cooler blowing into wind, the same physics as the air curtain | — |
| 2b | **Well-mixed zone heat + moisture balance** | walls and roof make the station act like one box | — |
| 3 | **Monte Carlo + Sobol** | what drives efficiency across venues | — |
| 4 | **Pareto front / ε-constraint** | competing goals; the catalog warns a weighted sum hides the trade-off | — |

## D3. The chain (one model that grows)

```
Task 1   freezer:  energy balance + air curtain + frost  →  defines capture fraction φ and "service"
            ↓ same φ idea, target becomes a person
Task 2a  bus stop: weather → device → mixing (φ) → felt temperature → people (Little's law) → efficiency
            ↓ add walls + crowd heat
Task 2b  station:  zone heat & moisture balance with people as heat source
            ↓ same model, new weather
Task 3   venues:   hourly weather, two climates; sensitivity → what drives efficiency
            ↓ add cost, water, safety
Task 4   trade-offs: Pareto front
            ↓
Task 5   guidelines, memo, blog
```

## D4. Validation checks we already have or plan

| # | Check | Status |
|---|---|---|
| 1 | One fitted parameter reproduces both of COMAP's evaporative claims | ±0.21 °C [checked] |
| 2 | Implied bus-shelter waste vs freezer literature | 74% vs 67–85% [checked] |
| 3 | Our wet-bulb code vs Open-Meteo's own wet-bulb data | error 0.42 °C on average (RMSE) [checked] |
| 4 | Energy balance closes (sensible removed = latent added in the cooler) | within 1% [checked] |
| 5 | Limiting cases (no leakage → zone = supply; huge leakage → zone = outdoor) | planned |
| 6 | Compare comfort drops with published field studies (Vanos et al. 2022 Phoenix misting) | planned |

---

# PART E — Practical: files, code, people

## E1. Where everything is

All files are in the AI's scratchpad folder:
`/tmp/claude-0/-home-user-ExampleRepo/a7b0ab5c-e343-5d3f-83da-06d68f7a8990/scratchpad/`

| Path | What's there |
|---|---|
| `HANDOVER_LOG.md` | this file |
| `himcm_b/` | all our code |
| `himcm_b/data/` | hourly summer-2025 weather for 5 cities |
| `himcm_b/figs/` | all figures (fig1–fig10) |
| `sprint_prompts/` | the 11 research briefs + merge brief |
| `sprint_out/` | the research agents' memos, code and figures (being filled now) |
| `HiMCM_Tasks1and2.md`, `HiMCM_2026_ProblemB_physics_primer.md`, `HiMCM_2026_ProblemB_model_options.md` | earlier documents (the physics primer is a good second read) |

**Warning:** this folder lives on a cloud machine that will be deleted when the session ends.
**Download everything before then.**

## E2. Code: what each file does and how to run it

You need Python 3. Install the libraries once:
```
pip install numpy pandas scipy matplotlib pythermalcomfort SALib
```
Then, from inside the `himcm_b` folder, run any script with `python3 <name>.py`.

| File | What it does | Main output |
|---|---|---|
| `core.py` | the physics toolbox: humidity, wet-bulb, evaporative cooler, mixing, radiation, SET/UTCI comfort | used by everything else |
| `fetch.py` | downloads hourly weather from Open-Meteo (retries if rate-limited) | `data/*.csv` |
| `freezer.py` | Task 1 energy balance, Carnot limit, load breakdown, two levers | printed tables |
| `nested.py` | shop-door effect, net heat into the shop | printed tables |
| `timescales.py` | time constants; heat vs water in door effect | printed tables |
| `calibration_check.py` | fits COMAP's table with one parameter | printed tables |
| `scenario.py` | bus-shelter + station scenarios, occupancy, metrics | used by analysis |
| `analysis.py` | 3 devices × 5 cities × 2 venues | `results.csv` |
| `phase_map.py` | which device wins at each temperature/humidity | printed map |
| `fan_paradox.py` | SET vs UTCI disagreement on fans | printed map |
| `sensitivity.py` | Sobol sensitivity for the bus stop | printed table |
| `lesson_numbers.py` | regenerates every worked number in the physics primer | printed |
| `figures.py`, `fig_*.py` | make the figures | `figs/*.png` |

**Before submitting, rewrite the code in your own words.** You'll understand it, you'll
catch mistakes, and the AI-use report stays honest.

## E3. Research sprint (running now)

Eleven AI research agents are running in parallel, each on one question. Each writes a memo to
`sprint_out/Txx_*.md`.

| ID | Question | Feeds | Status |
|---|---|---|---|
| T01 | Air-curtain jet physics: how much warm air gets in? | Task 1 | running |
| T02 | Deflection modulus, breakthrough, optimal curtain speed | Task 1 | running |
| T03 | Verified evidence table + official metrics (US DOE, EU, ENERGY STAR) | Task 1 | running |
| T04 | Frost differential equation + optimal defrost interval | Task 1 | running |
| T05 | Elasticity/Sobol: which aspects belong in the measure | Task 1 | running |
| T06 | Stress-testing efficiency definitions | Task 1 → all | running |
| T07 | Shop as a nested system, seasons, "case credits" | Task 1 | running |
| T08 | Jet-in-crossflow: air-curtain physics → bus shelter | Task 2a | running |
| T09 | Occupancy (Little's law, timed arrivals) + TOPSIS comparison | Task 2a | running |
| T10 | Choosing the felt-temperature index; fan safety | Task 2a | running |
| T11 | Rail-station zone model; crowd as heat source | Task 2b | running |

## E4. Who does what (suggested)

| Person | Owns | Reads memos |
|---|---|---|
| Physics teammate(s) | air curtain, jets, frost; checks every equation | T01, T02, T04, T08 |
| Maths / coding | models, sensitivity, figures | T05, T09, T10, T11 |
| Evidence / writing | sources, definitions, assumptions table, memo + blog | T03, T06, T07 |

Each person reads their memos, checks every source opens and says what the memo claims,
and writes a half-page "what we keep" note.

---

# PART F — History of this session (for the AI-use report too)

1. **4 Nov (Day 1).** Read the official Problem B PDF and a research-options document. The AI
   built a working model: weather download, psychrometrics, comfort indices, scenarios.
2. **Found and fixed a calibration bug.** At first the 5 °C claim was used as the *device's*
   efficiency and then mixed again, double-counting the loss. Fixed by fixing pad efficiency
   at 0.85 and fitting the shelter's open area instead (C2.1).
3. **Replaced a step-function safety score** with a smooth one. The step version gave a
   noisy checkerboard ranking.
4. Produced a long options report and a physics primer. **Feedback: too much, too fast, too
   much jargon.** Narrowed to Tasks 1 and 2 with figures.
5. **5 Nov (Day 2).** Team decided to go **one step at a time, starting with the freezer**.
   Teammate's question "apparent or actual temperature for food?" became the **spine of the
   paper** (A3).
6. Explained the physics from zero (Part B). Built the freezer energy figure, the
   "what changes" figure and the "how the machines work" figure. Fixed a figure that wrongly said
   evaporative cooling moves air "down-left" on the chart (it moves up-left: cooler and wetter).
7. Teammate asked **"do we consider the supermarket's own door?"** That led to the nested-boxes
   result (+27%) and the "waste has a sign" result.
8. Teammate asked **"would differential equations describe it best?"** That led to the
   time-constant analysis: only food and frost need them, and moisture matters more than
   temperature.
9. Read the team's **Model Catalog**. Concluded that Layer-1 ranking tools don't fit Task 1 (only one
   freezer); use energy balance + elasticity instead. Found the Hayes & Stoecker air-curtain
   model.
10. Physics teammates said the key is **aerodynamics**. Launched 11 research agents (E3).

**For the AI-use report:** keep this log, all prompts and all memos. The catalog lists
"gaps in the AI log" as a red flag.

---

# PART G — Open decisions and cautions

## G1. Decisions still open

- [ ] Main efficiency definition (C1.7). AI suggests capture fraction + marginal.
- [ ] One "currency" (comfort) or two (comfort + safety)?
- [ ] Which felt-temperature index (waiting on T10)
- [ ] Which two venues for Task 3
- [ ] Include the frost sawtooth in the model, or only mention it?
- [ ] Who counts as a beneficiary (only people in the shelter, or passers-by too)?

## G2. Cautions: things not yet verified

- Every literature number (67–85%, Dm 0.12–0.25, fan trial results, CDC/WHO thresholds)
  must be **opened and read by us** before citing.
- Case load 2.5 kW, COP 1.7, cooler airflows 1.1 / 2.5 m³/s are **assumed** typical values.
- UTCI is only valid for wind between 0.5 and 17 m/s.
- All Task 2 results so far are exploratory.
- AI research agents can invent sources. **Treat any source you can't open as unusable.**

## G3. Next steps

1. Collect the 11 memos; merge them; check contradictions (the AI does this next).
2. Decide the efficiency definition.
3. Write Task 1 in our own words.
4. Move to the bus stop.
