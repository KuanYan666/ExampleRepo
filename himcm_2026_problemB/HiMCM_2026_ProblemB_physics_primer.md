# The physics you need for HiMCM Problem B — from zero

A teaching document, not a reference card. It assumes you know what energy and temperature are
and nothing else. Every number in it I computed and checked this session; you can regenerate
them all with `python3 lesson_numbers.py`.

Work through it with a pencil. The exercises are not decoration — the moment you can do them
unaided is the moment you can defend your model to a judge.

**Contents**

1. Power vs energy (and the mistake in COMAP's own table)
2. Sensible and latent heat — the one idea the whole problem turns on
3. Moist air: humidity, properly
4. The wet-bulb temperature and why it is your entire budget
5. The three devices, physically
6. The human body as a heat engine — and why fans can hurt you
7. Radiation, and why shade is free
8. Where the cold goes: mass conservation and mixing
9. A full worked hour, by hand
10. Self-check problems, with answers

---

## 1. Power vs energy, and the mistake in the problem

**Energy** is a quantity — joules (J), or kilowatt-hours (kWh). **Power** is energy per unit
time — watts (W), or kilowatts (kW). 1 W = 1 J/s.

```
energy = power × time          1 kWh = 1 kW × 1 hour = 3,600,000 J
```

COMAP's table says the fan uses "0.25 kW/hr". **That unit does not exist.** kW is already a
rate; "kW per hour" would be an acceleration of energy use. They mean the fan *draws 0.25 kW*,
so running it for an hour costs 0.25 kWh.

Say this once, politely, in your assumptions: *"We read the Energy Use column as electrical
power draw in kW; the stated unit kW/hr is dimensionally inconsistent with energy use."* It
costs one sentence and signals immediately that you check units. Judges notice.

> **Habit to build now:** write units on every line of algebra. Most modelling errors in this
> problem are unit errors wearing a disguise.

---

## 2. Sensible and latent heat — the one idea the whole problem turns on

### 2.1 Sensible heat: heat you can feel on a thermometer

Add energy to something, its temperature rises:

```
Q = m · c · ΔT
```

- `Q` = energy (kJ), `m` = mass (kg), `ΔT` = temperature change (K or °C — the *size* of a
  degree is the same in both, so differences are interchangeable)
- `c` = **specific heat capacity**, the energy to warm 1 kg by 1 °C.
  For air, `c_p ≈ 1.006 kJ/(kg·K)`. For water, about 4.18 — water is ~4× harder to warm.

Air is light. At 40 °C its density is about **1.127 kg/m³**, so:

```
ρ·c_p ≈ 1.13 kJ per cubic metre per degree
```

**Worked example.** A bus shelter 15 m² × 2.5 m high holds 37.5 m³ of air. To cool all of it by
1 °C:

```
Q = 37.5 m³ × 1.13 kJ/(m³·K) × 1 K = 42.5 kJ = 0.012 kWh
```

That is *nothing* — about one second of a 1.2 kW cooler. **So why does cooling a bus shelter
cost anything at all?**

Because in an open shelter you are not cooling the air once. The wind replaces it continuously,
and you are cooling a *river* of air that flows straight back out to the desert. Hold onto
this: **the cost of open-air cooling is not in the air, it is in the replacement rate.** That
single sentence is most of Problem B.

### 2.2 Latent heat: heat that changes state without changing temperature

Boil a kettle. Once the water reaches 100 °C, you keep adding energy and the temperature
*stops rising* — the energy goes into tearing liquid water apart into vapour instead. That
energy is **latent heat** (Latin *latere*, to lie hidden).

```
Q = m · h_fg          h_fg ≈ 2450 kJ/kg for water at ordinary temperatures
```

Compare: warming 1 kg of water by 1 °C takes 4.18 kJ. **Evaporating** that same 1 kg takes
2450 kJ — nearly **600 times more**. Evaporation is an enormously powerful energy sink, and
that is exactly why it cools things.

### 2.3 Why evaporation cools

When water evaporates, the molecules that escape are the fastest ones. The ones left behind
have a lower average speed — and average molecular speed *is* temperature. So the remaining
liquid, and anything touching it, gets colder. The 2450 kJ/kg comes out of whatever is nearby.

That is why sweating works. It is also, exactly, how an evaporative cooler works.

> **Exercise 2A.** You evaporate 1 litre (1 kg) of water into a stream of air. How much heat is
> absorbed? If that heat all comes from air flowing at 1.2 kg/s, for how long could you cool
> that air stream by 10 °C? *(Answers at the end.)*

---

## 3. Moist air: humidity, properly

### 3.1 What humidity actually is

Air is a mixture of gases, and water vapour is one of them. Each gas contributes part of the
total pressure — its **partial pressure**. Humidity is just "how much of the air's pressure is
water vapour."

Total atmospheric pressure is about 101.3 kPa. Water vapour's share is typically 1–4 kPa.

### 3.2 Saturation: air has a limit

At a given temperature, there is a maximum partial pressure water vapour can reach, called the
**saturation vapour pressure** `p_ws(T)`. Push past it and water condenses out — dew, fog,
cloud.

**The crucial fact: `p_ws` rises steeply with temperature.** Roughly it doubles every 10–11 °C:

| T (°C) | 20 | 30 | 35 | 40 | 43 |
|---|---|---|---|---|---|
| `p_ws` (kPa) | 2.34 | 4.24 | 5.63 | 7.38 | 8.65 |

Warm air can hold far more water than cold air. This one curve explains dew on grass, why your
glasses fog, and why hot climates can be so much more humid than cold ones.

### 3.3 Relative humidity — useful, and a trap

```
RH = p_w / p_ws(T) × 100%
```

RH is the *percentage of the limit you are using*. It is intuitive, it is what weather reports
give, and **it is dangerous in a model**, because it depends on temperature. Cool a parcel of
air without adding any water and its RH rises — not because water was added, but because the
limit fell.

### 3.4 Humidity ratio — the honest variable

```
W = mass of water vapour / mass of dry air        (kg/kg, usually quoted in g/kg)

W = 0.621945 · p_w / (p − p_w)
```

`W` counts actual water. It does **not** change when you merely heat or cool the air. This is
the variable you must do physics with.

> **The single most common silent error in this problem** is mixing two air streams by
> averaging their RH. You will see in §8 that it gives 28% where the true answer is 20%.
> **Mix on `W`. Convert to RH only at the very end, for reporting.**

### 3.5 Dew point

Cool air (holding `W` fixed) until it saturates. That temperature is the **dew point**. It is a
direct measure of absolute moisture content — two parcels with the same dew point hold the same
water, whatever their temperatures.

### 3.6 Your reference table

Computed and checked this session. Learn to reproduce a row of it on a psychrometric chart.

| T (°C) | RH (%) | `p_ws` (kPa) | `p_w` (kPa) | `W` (g/kg) | `T_wb` (°C) | **WBD** (°C) | dew pt (°C) |
|---|---|---|---|---|---|---|---|
| 43 | 12 | 8.649 | 1.038 | 6.44 | 20.9 | **22.1** | 7.5 |
| 40 | 25 | 7.383 | 1.846 | 11.54 | 23.6 | **16.4** | 16.2 |
| 35 | 40 | 5.628 | 2.251 | 14.13 | 23.9 | **11.1** | 19.4 |
| 34 | 70 | 5.324 | 3.727 | 23.75 | 29.1 | **4.9** | 27.7 |
| 32 | 80 | 4.759 | 3.807 | 24.28 | 29.0 | **3.0** | 28.1 |
| 28 | 90 | 3.782 | 3.404 | 21.62 | 26.6 | **1.4** | 26.2 |

Look at the `W` column. Phoenix at a blistering 43 °C holds **6.4 g/kg** of water. Singapore at
a much milder 32 °C holds **24.3 g/kg** — nearly four times as much. The hotter city is the
drier one. That inversion is the physical story of your whole paper.

---

## 4. The wet-bulb temperature — your entire cooling budget

### 4.1 What it is

Wrap a wet cloth around a thermometer bulb and blow air over it. Two things happen at once:

- water evaporates from the cloth, **cooling** it (latent heat, §2.2)
- the air, being warmer than the now-cold cloth, **warms** it (sensible heat)

The thermometer settles where these exactly balance. That equilibrium is the **wet-bulb
temperature `T_wb`** — the coldest temperature you can reach by evaporating water into that
air, and nothing more.

The ordinary air temperature is called the **dry-bulb temperature `T_db`** to distinguish it.

### 4.2 Wet-bulb depression: the budget

```
WBD = T_db − T_wb
```

**This is the single most important number in Problem B.** It is the total evaporative cooling
available, a hard thermodynamic ceiling. No evaporative cooler, however expensive, can beat it.

```
Phoenix,   43 °C / 12% RH  →  WBD = 22.1 °C     a huge budget
Houston,   34 °C / 70% RH  →  WBD =  4.9 °C     a small one
Singapore, 32 °C / 80% RH  →  WBD =  3.0 °C     almost nothing
```

In dry air, evaporation runs freely and the cloth gets very cold. In humid air the surrounding
air is nearly saturated already, so almost nothing evaporates and `T_wb` creeps up towards
`T_db`.

> **This is why the problem is interesting.** An evaporative cooler sold as "lowers air
> temperature up to 5 °C" physically cannot do that in Singapore. The budget is 3.0 °C, and a
> real device captures only ~85% of it: a maximum of about **2.6 °C**, before any of it has
> even reached a person. A team that applies "5 °C" everywhere has written down an
> impossibility, and you can say so with a number.

> **Exercise 4A.** Dubai in August: 40 °C, 55% RH. Estimate `T_wb` from the trend in the table
> and decide whether an evaporative cooler is worth installing. Then check with code.

---

## 5. The three devices, physically

### 5.1 The evaporative cooler

Warm dry air is pulled through a soaked pad. Water evaporates into it, taking latent heat *from
the air itself*. The air leaves cooler and much wetter.

Because the heat comes out of the same air it goes into, the process is **adiabatic** — no
energy enters or leaves the air stream overall. It follows a line of constant wet-bulb
temperature on a psychrometric chart (very nearly a line of constant enthalpy).

A real pad is not perfect. Define **saturation efficiency** `ε` as the fraction of the budget
it actually captures:

```
T_out = T_db − ε · (T_db − T_wb)              ε ≈ 0.70–0.90 for real pads
W_out = W_in  + ε · (W_sat(T_wb) − W_in)
```

The first line is the one everybody writes. **The second line is the one that wins you marks**,
because it carries the humidity rise — and the humidity rise is what makes the device useless
in Singapore and what the "feels like" calculation later depends on.

**Worked, at Phoenix design conditions** (43 °C, 12% RH, ε = 0.85, airflow 1.1 m³/s):

```
wet-bulb 20.9 °C, so WBD = 22.1 °C
outlet air:  24.2 °C at 75% RH        (an 18.8 °C drop!)
mass flow:   1.23 kg/s
sensible cooling delivered:  23.2 kW
electrical power drawn:       1.2 kW   →  ratio 19.3×
water evaporated:            34 L/h
```

**And the same device in Singapore** (32 °C, 80% RH):

```
outlet air:  29.4 °C at 97% RH        (a 2.6 °C drop)
sensible cooling delivered:   3.3 kW
electrical power drawn:       1.2 kW   →  ratio 2.7×
water evaporated:             5 L/h
```

Same machine, same electricity, **seven times less cooling** — and it leaves the air at 97% RH,
which feels unpleasant in a way the dry-bulb reading does not capture.

### 5.2 The deepest point in the whole problem

That "19.3×" is *not* a free lunch, and understanding why will set your paper apart.

Check the air's total energy (enthalpy) before and after:

```
Phoenix:  59.87 kJ/kg  →  60.60 kJ/kg      (+1.2%, i.e. unchanged within rounding)
   of which sensible:  43.3  →  24.4       ↓
   of which latent:    16.6  →  36.2       ↑
```

**The evaporative cooler removes essentially no energy from the air at all.** It converts
sensible heat into latent heat. The thermometer falls by 18.8 °C; the energy content does not
move. The electricity only runs a fan and a pump — the cooling comes from the water, and the
"heat removed" is still right there in the air stream, hiding as vapour.

This matters enormously for a problem titled *Air Conditioning the Environment*:

> An evaporative cooler does not cool the city. It relocates heat from a form you can feel
> (temperature) into a form you cannot (humidity). A vapour-compression air conditioner is
> different again — it genuinely moves heat from inside to outside, and dumps its own
> electrical energy with it, so it makes the surroundings *hotter* to make one spot cooler.

### 5.3 The fan

A fan changes **no air property whatsoever**. `T_db`, `W`, RH all leave exactly as they
arrived. (Strictly, its 0.25 kW ends up as heat in the air — a tiny warming you should mention
and then neglect, with a one-line justification.)

So why does it help? Because it changes conditions **at your skin**, not in the air. See §6.

This is why COMAP's table is a trap. The fan's "3 °C" is a *sensation*; the coolers' "5 °C" and
"8 °C" are *air temperatures*. **These are different physical quantities and you cannot compare
them until you convert one into the other.** Doing that conversion properly is one of the
highest-value moves available in this problem.

---

## 6. The human body as a heat engine

### 6.1 You are a 100 W heater

Your body converts food into energy, and most of it ends up as waste heat — about **100 W** at
rest, 150–200 W walking. You must shed that continuously or your core temperature rises.
Heatstroke is simply failure to shed it.

Four channels:

| Channel | Mechanism | Depends on |
|---|---|---|
| **Convection** | air flowing past skin carries heat away | air temperature, **air speed** |
| **Radiation** | infrared exchange with surroundings | surface temperatures, sun |
| **Evaporation** | sweat evaporating from skin | **humidity**, air speed |
| **Conduction** | direct contact | usually negligible standing up |

### 6.2 Convection, and the sign flip that changes everything

Skin sits at roughly **35 °C**. Heat flows from hot to cold, so:

```
q_convection = h_c · (T_air − T_skin)        W/m²
```

`h_c` is the heat transfer coefficient, and it **rises with air speed** — roughly
`h_c ≈ 8.3·v^0.6` for a standing person. Still air (0.3 m/s) gives ≈ 4.4; a fan at 1.25 m/s
gives ≈ 9.5. The fan more than doubles it.

Now look at what that does, as computed:

| Air temp | still air | with fan | fan changes it by | |
|---|---|---|---|---|
| 28 °C | −28.2 W/m² | −66.4 W/m² | **−38.2** | skin loses heat — good |
| 32 °C | −12.1 W/m² | −28.5 W/m² | **−16.4** | skin loses heat — good |
| **35 °C** | 0 | 0 | **0** | nothing happens |
| 38 °C | +12.1 W/m² | +28.5 W/m² | **+16.4** | skin *gains* heat — bad |
| 43 °C | +32.2 W/m² | +75.9 W/m² | **+43.7** | skin gains heat — bad |
| 47 °C | +48.4 W/m² | +113.9 W/m² | **+65.5** | skin gains heat — very bad |

**Above skin temperature, a fan blows heat *into* you, and a faster fan does it faster.** This
is a fan-oven. It is the same physics.

### 6.3 So when does a fan still help above 35 °C?

Because of the fourth channel. Moving air also speeds up **sweat evaporation**, which cools
strongly. The fan therefore does two opposing things above 35 °C:

- convection: adds heat (bad), scaling with `(T_air − 35)`
- evaporation: removes heat (good), but **only if the air can accept more water**

In humid air, evaporation is already choked, so the convective harm wins. In dry air,
evaporation runs freely and usually wins — *until* sweat production itself becomes the limit,
at which point extra airflow adds nothing but heat and dehydration.

Human trials (Jay, Morris et al.) found fans **beneficial at 40 °C/50% RH** but **detrimental
at 47 °C/10% RH**. Public-health bodies disagree about the cut-off: CDC says 32.2 °C, WHO says
40 °C, and a 2012 Cochrane review found no solid evidence either way.

**The resolution — and a real finding for your paper — is that a single-temperature rule is the
wrong shape of rule.** The safe limit is a curve in temperature *and* humidity.

### 6.4 Why comfort indices exist

Four channels, each depending on several variables, makes "is this pleasant?" a messy question.
Comfort indices collapse it to one number:

- **Apparent temperature (AT)** — simple, hand-computable, a decent "feels like".
  `AT = T_a + 0.33e − 0.70v − 4.00` with `e` the vapour pressure in hPa and `v` in m/s.
  Note it treats wind as a flat linear benefit, so **it can never reproduce §6.2's sign flip**.
  Fine as a cross-check; wrong as your main tool.
- **SET (Standard Effective Temperature)** — solves the full body heat balance. Handles still
  *and* moving air, clothing, activity. It is the basis of ASHRAE Standard 55.
- **UTCI** — the outdoor standard, built for weather exposure, with heat-stress categories
  (no stress / moderate / strong / very strong / extreme). Officially valid only for wind
  0.5–17 m/s, so it cannot describe genuinely still air.

> **Why you should use two of them.** SET and UTCI *disagree* about fans in hot dry air, and
> the medical literature sides with UTCI. Reporting a disagreement between two standard models,
> and using outside evidence to adjudicate, is exactly what distinguishes a modelling paper
> from a calculation.

**The ASHRAE "cooling effect"** is the bridge you need for COMAP's table: it is defined as the
number of degrees you must subtract from the air temperature, in still air, to feel as
comfortable as you do with the fan running. That converts "feels 3 °C cooler" into something
directly comparable with "air is 5 °C cooler". Running it backwards says the fan must deliver
about **1.25 m/s** at the person to justify its claim in dry heat — but about **3.0 m/s** in
humid heat.

---

## 7. Radiation, and why shade is free cooling

Every object radiates according to its absolute temperature:

```
E = ε_s · σ · T⁴          σ = 5.67 × 10⁻⁸ W/(m²·K⁴),  T in kelvin
```

The fourth power is brutal: sun-baked asphalt at 60 °C radiates about **40% more** than the
same surface at 30 °C.

Standing outdoors you exchange radiation with the sky, the ground, nearby walls, and the sun.
We bundle all of it into the **mean radiant temperature `T_mrt`**: the temperature a uniform
imaginary enclosure would need to give you the same radiant load.

In full summer sun `T_mrt` can run **15–25 °C above air temperature**. In shade it is close to
air temperature. So:

> **Putting a roof over someone can be worth more than any of the three devices — and it costs
> zero kilowatts.**

Vanos et al. measured misting in Phoenix cutting UTCI by 4.4 °C, while **misting plus shade cut
it by 9.7 °C**. Shade did more than the machine.

This also breaks any pure efficiency *ratio*: shade delivers cooling for 0 kWh, so its
"comfort per kWh" is infinite. Noticing that your own metric divides by zero, and saying what
you do about it, is a sign of a team thinking rather than computing.

---

## 8. Where the cold goes: mass conservation and mixing

### 8.1 Volumetric flow

```
Q = A · v          m³/s = m² × m/s
```

A device moving 1.1 m³/s through a shelter whose air volume is 37.5 m³ replaces the air in
about 34 seconds. A 2 m/s crosswind through 10 m² of open side drives roughly 20 m³/s *past*
it. You are losing badly, and that ratio is the problem in one line.

### 8.2 Mixing: the lever rule

Mix cold supply air (mass flow `m₁`, temperature `T₁`) with infiltrating ambient air
(`m₂`, `T₂`). Conserving energy and mass:

```
T_mix = (m₁T₁ + m₂T₂)/(m₁ + m₂) = φ·T₁ + (1−φ)·T₂      where  φ = m₁/(m₁+m₂)
```

`φ` is the **capture fraction**: the share of the air you are breathing that actually came from
the cooler. It is the central quantity of Problem B, and it is what "a freezer with the door
open" means mathematically.

### 8.3 Mix on `W`, never on RH

The same lever rule applies to humidity ratio, because `W` is a mass ratio and mass is
conserved:

```
W_mix = φ·W₁ + (1−φ)·W₂              ✅
RH_mix = φ·RH₁ + (1−φ)·RH₂            ❌  meaningless
```

**Demonstration** (Phoenix design, φ = 0.255):

```
ambient  43.0 °C / 12% RH   (W = 6.44 g/kg)
supply   24.2 °C / 75% RH   (W = 14.22 g/kg)

correct — mix on W:    shelter = 38.2 °C / 20% RH
wrong   — mix on RH:   shelter = 38.2 °C / 28% RH
```

An 8-point error, in the variable the whole problem depends on, from one plausible-looking
shortcut.

### 8.4 The punchline

```
delivered drop = 43.0 − 38.2 = 4.8 °C
outlet drop    = 43.0 − 24.2 = 18.8 °C

→ 74% of the cooling never reached a person.
```

And measured infiltration losses through the air curtains of **open supermarket freezer cases**
run **67–85%** of total cooling load across five independent studies.

The bus shelter and the open freezer waste cooling at the same rate, for the same reason. That
is not an analogy. It is the same equation with different labels — which is why COMAP opened
the problem with a freezer.

---

## 9. A full worked hour, by hand

Phoenix, 2pm, 43 °C, 12% RH, 2 m/s wind. Small evaporative cooler, 1.1 m³/s, 1.2 kW. Three
people waiting.

1. **Wet-bulb.** From the table, `T_wb` = 20.9 °C → **WBD = 22.1 °C** (the budget).
2. **Device outlet.** `T_out = 43 − 0.85 × 22.1 =` **24.2 °C**, and `W` rises 6.44 → 14.22 g/kg.
3. **Capture fraction.** Infiltration `Q_inf = C_d·A·v = 0.6 × 10.7 × 0.5 ≈ 3.2 m³/s` at the
   calm design condition, so `φ = 1.1/(1.1+3.2) =` **0.255**.
4. **Shelter conditions.** Mix on `W`: `T_z` = **38.2 °C**, `W_z` = 8.4 g/kg → **20% RH**.
5. **Delivered drop:** **4.8 °C** — close to COMAP's claimed 5 °C, which is the check that your
   whole chain is right.
6. **Comfort.** Feed (38.2 °C, 20% RH, air speed, `T_mrt`) into SET and UTCI and compare with
   the no-device case.
7. **Service.** 3 people × 1 hour × (comfort improvement).
8. **Efficiency.** Divide by 1.2 kWh. Also divide by 34 L of water, and by the cost.

Every step is arithmetic you can check. That is the point: **a model you can hand-verify is a
model you can defend.**

---

## 10. Self-check problems

**10.1** A fan draws 0.25 kW. Running 14 hours a day for a 100-day summer, how many kWh? At
$0.15/kWh, what does it cost?

**10.2** Air at 35 °C, 40% RH. Using the table: what is `W`? What is the wet-bulb depression?
What is the best possible air-temperature drop from a perfect (ε = 1.0) evaporative cooler?

**10.3** Why can an evaporative cooler never cool air below its wet-bulb temperature? Answer in
one sentence about energy balance.

**10.4** A cooler delivers 2.0 m³/s. Infiltration is 6.0 m³/s. What is φ? If the outlet is
12 °C below ambient, what is the delivered drop? What fraction is wasted?

**10.5** Explain, using §6.2, why a fan at 43 °C might make someone *less* safe even though
they report feeling cooler. Why is that distinction central to this problem?

**10.6** Two shelters, same device, same climate. One serves 5 people/hour, the other 50. Which
has higher cooling efficiency, and by roughly what factor? What does that tell you about where
a city should install cooling?

### Answers

**2A.** 2450 kJ. At 1.2 kg/s cooled by 10 °C you remove 1.2 × 1.006 × 10 ≈ 12.1 kW, so
2450/12.1 ≈ **203 seconds**, about 3½ minutes per litre.

**4A.** At 40 °C/55% RH, `T_wb` ≈ 31 °C, so WBD ≈ 9 °C. A real cooler captures ~85% ≈ 7.6 °C at
the outlet, but only ~25% of that reaches people in an open shelter → under 2 °C delivered.
**Marginal**, and it would consume ~15 L/h of water in a desert city. Worth saying out loud.

**10.1** 0.25 × 14 × 100 = **350 kWh**, about **$53**. (Now compare: the large cooler would be
3500 kWh and $525. The *energy* gap is 10×; check whether the *benefit* gap is.)

**10.2** `W` = 14.13 g/kg, WBD = 11.1 °C, best possible drop = **11.1 °C** (ε = 1 means you
reach the wet-bulb exactly).

**10.3** At the wet-bulb temperature, evaporative cooling and convective warming are exactly in
balance; below it the air would have to give up heat it does not have, so there is no energy
available to drive further cooling.

**10.4** φ = 2.0/8.0 = **0.25**; delivered = 0.25 × 12 = **3 °C**; **75% wasted**.

**10.5** At 43 °C the air is 8 °C hotter than skin, so faster airflow drives *more* heat into
the body; the person may feel cooler because the moving air speeds sweat evaporation from their
skin surface, which registers as sensation, while the net heat load — and dehydration — rises.
It matters because comfort and safety are different objectives that can point in opposite
directions, so an efficiency measure built only on comfort can recommend something unsafe.

**10.6** Roughly **10× higher** for the busy shelter: energy is identical, people served is 10×.
Cities should install cooling where people *dwell in numbers*, not where it is most visible —
and this is confirmed by the sensitivity analysis, where occupancy and dwell time dominate
every device parameter.

---

## What to read next

- **Psychrometric chart** — print one. Plot the Phoenix and Singapore cases from §5.1 on it by
  hand. The constant-wet-bulb lines will make the whole problem visual.
- **EnergyPlus Engineering Reference, evaporative coolers** — the `T_out` equation in its
  native habitat.
- **ASHRAE 55** — comfort zones, elevated air speed, the cooling effect.
- The companion document, *HiMCM 2026 Problem B — extended model options*, which builds all of
  this into a competition strategy.

### Sources

- [EnergyPlus — evaporative coolers](https://bigladdersoftware.com/epx/docs/8-1/engineering-reference/page-084.html)
- [ASHRAE 55-2013 Addendum d — elevated air speed](https://www.ashrae.org/file%20library/technical%20resources/standards%20and%20guidelines/standards%20addenda/55_2013_d_20150521.pdf)
- [pythermalcomfort — cooling effect implementation](https://pythermalcomfort.readthedocs.io/en/stable/_modules/pythermalcomfort/models/cooling_effect.html)
- [Should electric fans be used during a heat wave? (Jay et al.)](https://www.sciencedirect.com/science/article/abs/pii/S0003687014001355)
- [Scientific American — fans in muggy vs extreme dry heat](https://www.scientificamerican.com/article/fans-may-be-okay-for-muggy-days-but-avoid-them-in-extreme-dry-heat/)
- [Kettering University — open display cases](https://kettering.edu/news/keeping-cool)
- [Brunel thesis — air-curtain infiltration share of load](https://bura.brunel.ac.uk/bitstream/2438/7456/1/FulltextThesis.pdf)
- [Open-Meteo historical weather API](https://open-meteo.com/en/docs/historical-weather-api)
- [Steadman apparent temperature (BoM form)](https://community.tempest.earth/t/steadman-apparent-temperature-australian-apparent-temperature/2248)
