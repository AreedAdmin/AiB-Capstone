# Heat Smart Orkney — Complete Project Explainer

> A from-scratch guide to *everything* in this capstone. No prior energy or data-science
> knowledge assumed. Read it top to bottom and you'll understand the problem, the data, the
> maths, the results, the business case, and what we delivered.

---

## 0. The one-paragraph version

The Orkney Islands (north of Scotland) generate **more wind power than their single cable to
mainland Britain can carry**. When that happens, wind turbines are forced to throttle down —
this is called **curtailment** — and that clean energy (and its revenue) is wasted. Our client,
**Kaluza**, wants to know: instead of switching turbines *off*, can we switch household heaters
*on* to soak up the surplus? This is **demand response (DR)**. Our job was to put a **number** on
that opportunity. We found Orkney curtails about **76.86 GWh of wind per year**, but residential
heating demand response could realistically absorb only about **267 MWh/year (≈0.35%)** of it —
real, but tiny. The financial value to Kaluza is correspondingly small (**~£3,007/year**) without
subsidies or grid partnerships. The strategic conclusion: HSO isn't a curtailment-elimination
play; it's a way to **prove flexible-demand orchestration works** and build the platform for
bigger future smart-grid services.

---

## 1. What kind of project is this?

- **Type:** A university *capstone consultancy project* for the **Analytics in Business (AiB) 2026**
  programme (Imperial College).
- **Team:** "Group B" — students acting as **data-science consultants**.
- **Client (role-played):** **Kaluza** (a demand-response technology company, formerly part of OVO
  Energy), in partnership with **Community Energy Scotland**.
- **Framing:** It is a **business-case development** exercise, not a pure modelling exercise. The
  guiding quote from Kaluza's senior data scientist is:
  > *"The value of anything can only be compared to the cost of the alternative."*
  So we treat **today's curtailment** as the baseline and measure DR against it.
- **What we had to produce:**
  1. A **technical report** (a Jupyter Notebook) for Kaluza's data team.
  2. An **executive presentation** for the CEO / board (≤10 minutes, non-technical).
  3. A **peer evaluation** (role-played client Q&A).

---

## 2. The energy background (the only physics you need)

**The single rule of power grids:**
> Electricity supply and demand must always be in **perfect balance, in real time**. If they
> aren't, grid frequency drifts and equipment trips offline.

Historically, the **supply side** chases demand — a gas plant ramps up when everyone boils a
kettle. That works because we control the throttle on fossil fuels.

**Wind and solar are different.** We can't tell the wind to blow harder or softer. So in a
renewables-heavy system, balancing increasingly has to come from the **demand side** — i.e.
shifting *when* people use energy. That shift is **demand response**.

### Why Orkney specifically?

| Feature | Detail |
| --- | --- |
| Status | **Net energy exporter** — it makes more renewable energy than it uses |
| Generation | Heavy **wind**, plus some solar / wave / tidal |
| Link to mainland GB | A single **40 MW subsea cable** (the interconnector) |
| The real bottleneck | **Cable capacity**, not generation capacity |
| Who gets throttled first | **Newest turbines first** (often small, community-owned farms) |

When local wind output **exceeds local demand + the 40 MW the cable can export**, the network
operator forces some turbines to reduce output. Newer wind farms get curtailed first and lose the
most revenue.

### The Demand Response proposition

- **Without DR:** surplus wind → curtailed → turbine throttled → **£0 revenue**, energy wasted.
- **With DR:** surplus wind → **consumed by Orkney homes** (heaters, hot-water tanks switched on)
  → revenue at wholesale price + cheaper energy for residents + less waste.

This is exactly what Kaluza's **Heat Smart Orkney (HSO)** programme does: it remotely switches on
enrolled household heating during surplus-wind periods.

### Who benefits

| Stakeholder | Benefit |
| --- | --- |
| **Wind generators** | Get paid for energy that would otherwise be curtailed |
| **Orkney households** | Cheaper/free energy during DR events; less fuel poverty |
| **Kaluza** | Commercial revenue from a scalable DR product |
| **The grid / UK** | More renewables actually delivered; fewer expensive cable upgrades |
| **Climate** | Higher renewable utilisation, less zero-carbon energy wasted |

> **Important caveat:** during the trial, households are **fully reimbursed**, so all the
> curtailment-avoidance value flows to wind generators. Long-term it would split three ways. We
> were asked to size the **upper-bound** prize.

---

## 3. The questions we had to answer

**Main research question:**
> *How much Orkney wind curtailment can be mitigated through residential demand response, and what
> economic value does this unlock?*

It breaks into three concrete sub-questions:

| # | Question | In plain English |
| --- | --- | --- |
| **Q1** | How much energy is curtailed annually across Orkney? | How big is the waste? |
| **Q2** | How much can DR reduce curtailment at different penetration levels? | How much can we actually catch? |
| **Q3** | How many households are needed to deliver each level? | How many homes must sign up? |

Everything ultimately gets converted into the one metric the board understands:
**curtailed energy (MWh/year) → £/year at the wholesale price.**

---

## 4. The data

Two CSV files in `Data/`. **No personal data (no PII)** — only device telemetry and aggregated
demand. (Kaluza deliberately keeps personal info separate from telemetry by design.)

### 4.1 `Turbine_telemetry.csv` — the SUPPLY side

High-frequency readings from a wind turbine.

| Field | Meaning |
| --- | --- |
| `Timestamp` | Reading time (~1-minute granularity) |
| `Power_kw` | **Actual** power being generated right now |
| `Setpoint_kw` | **Maximum allowed** output — *lowered during curtailment* |
| `Wind_ms` | Local wind speed (metres per second) |

- **~1,069,637 rows**, spanning **2015-05 → 2018-01**, ~1-minute samples.
- **The key trick:** when `Setpoint_kw` is pushed below the turbine's nameplate (900 kW), the grid
  is capping the turbine → that's a **curtailment signal**.

### 4.2 `Residential_demand.csv` — the DEMAND side

Aggregated household electricity use.

| Field | Meaning |
| --- | --- |
| `Timestamp` | Half-hour interval start |
| `Demand_mean_kw` | **Mean** demand *per participating household* |
| `N_households` | How many homes are in the sample at that time |

- **~17,569 rows**, covering **2017** (one full year), 30-minute intervals.

### 4.3 Why 2017?

The two datasets only **overlap fully in 2017**. So all curtailment totals and demand matching use
**2017 only**, even though turbine data stretches back to 2015 (the older data still helps calibrate
the power curve). Post-2017 statistics are deliberately excluded.

```
Turbine telemetry:  2015 ████████████████████████ 2018
Residential demand:           2017 ████████ 2018
                                   ▲▲▲▲▲▲▲▲  ← overlap = valuation window
```

---

## 5. Key concepts / glossary

| Term | Meaning |
| --- | --- |
| **Curtailment** | Forcing a turbine to produce *less* than it physically could, because the grid can't absorb it. The "wasted" energy = potential − actual output. |
| **Setpoint** | The max power the turbine is *currently allowed* to make. Equals nameplate (900 kW) when normal; reduced during curtailment. |
| **Power curve** | The relationship between **wind speed → expected power output**. Used to estimate what a turbine *would have* made (the "counterfactual"). |
| **Counterfactual** | The "what-if" generation: what the turbine *would* have produced if it hadn't been curtailed. |
| **Demand Response (DR)** | Adjusting electricity *consumption* in response to grid signals — here, *increasing* it to absorb surplus wind. |
| **Interconnector** | The 40 MW subsea cable to mainland GB — the hard constraint causing curtailment. |
| **Penetration** | The share of Orkney households enrolled in the DR scheme (e.g. 25% = 2,596 homes). |
| **Flexible load** | The portion of a home's demand that can be shifted in time (mainly heating / hot water). NOT the always-on stuff (fridge, lights). |
| **Wholesale price** | The £/MWh price generators get for selling energy — the basis for valuing avoided curtailment. |
| **Nameplate capacity** | The turbine's maximum rated output = **900 kW** here. |

---

## 6. How we did it — the analysis pipeline

Everything lives in **one Jupyter notebook** (`report.ipynb`) so Kaluza's team can re-run it.
Six stages:

| Stage | What it does |
| --- | --- |
| **1. Load & clean** | Parse the CSVs, flag special "regimes" (storm, downtime, curtailed), cap gaps in telemetry. |
| **2. Power curve** | Build the wind→power model from *normal* data only. |
| **3. Curtailment** | Use the power curve to compute lost MWh, then scale to the whole fleet. |
| **4. Flexible demand** | Work out how much household load can realistically be shifted. |
| **5. DR matching** | Match flexible demand against curtailed supply, half-hour by half-hour. |
| **6. Economics** | Turn avoided MWh into £, split the value across actors, find break-even. |

### 6.1 Cleaning & "regime flags"

Each turbine minute is tagged:
- `is_storm`: wind > 25 m/s mean (or gust > 30) → turbine shut down for safety → **excluded**.
- `is_downtime`: power ≈ 0 but wind is fine → maintenance/fault → **excluded**.
- `is_curtailed_regime`: `Setpoint_kw < 0.99 × 900` → grid is capping it → **this is curtailment**.
- "Normal" = none of the above → used to build the power curve.

### 6.2 Stage 2 — The power curve (a *mandatory* deliverable)

This is the analytical heart of the project. We needed a function `P̂(v)` that says: *"given wind
speed `v`, how much power should this turbine make if nothing is holding it back?"*

How we built it:
1. Use **only "normal" minutes** (not storm, not downtime, not curtailed).
2. Split wind speed into ~35 **bins**; compute the **mean power** in each bin.
3. Force the curve to be **non-decreasing** (more wind can't mean less power — physics).
4. Smooth it with a **PCHIP spline** and clip to the range **[0, 900] kW**.

We validated the fit:
- **R² = 0.984** (explains 98.4% of variance — excellent)
- **MAE = 24.79 kW** (average error)
- **RMSE = 43.34 kW**

The shape is the classic S-curve: flat until ~3 m/s (**cut-in**), a steep ramp, then a **rated
plateau** near 900 kW.

### 6.3 Stage 3 — Quantifying curtailment (answers Q1)

For every curtailed minute, the lost energy is the gap between what the turbine *could* have made
and what it *actually* made:

```
curtailed_kW   = max(0, P̂(wind) − Power_actual)      ← only during curtailed regime
curtailed_kWh  = curtailed_kW × Δt                    ← Δt = minutes converted to hours
```

Sum that over all of 2017 for one turbine, then scale to the fleet:

```
Fleet curtailment = single_turbine × N_turbines (500) × correlation (1.0)
```

**Result:** ≈ **76.86 GWh/year** for the fleet (single turbine = 153.70 MWh; 90% CI ≈
62.1–91.9 GWh). There were **154 curtailment days** in 2017.

### 6.4 Stage 4 — Flexible demand

Not all household demand can be shifted. We split each home's half-hourly demand `d` into:
1. **Baseline** = rolling 24-hour minimum (the always-on load).
2. **Variable** = `max(0, d − baseline)`.
3. **Flexible** = `0.40 × variable` (we assume 40% of variable load is shiftable heating).

And only **70% availability** — at any moment only ~70% of enrolled homes are online and
dispatchable (devices off, opt-outs, comfort limits).

```
Dispatchable DR power = flexible × N_enrolled × 0.70
```

### 6.5 Stage 5 — Matching supply to demand (answers Q2 & Q3)

For each 30-minute interval, the energy DR can actually absorb is the **smaller** of (what's being
curtailed) and (what DR can supply):

```
avoided = min(curtailed_fleet_energy, dispatchable_DR_energy)
recovery% = 100 × Σ avoided / total_fleet_curtailment
```

We then sweep the number of enrolled households from 100 up to all 10,385 Orkney homes and plot the
**avoided-curtailment-vs-enrolment** curve. It **saturates** — past a point, adding homes barely
helps, because flexible heating capacity (not curtailed energy) becomes the bottleneck.

### 6.6 Stage 6 — Economics

Convert avoided MWh to £ at **£45/MWh** wholesale, then split the "value pool" across four actors
and find how many homes are needed to break even under different subsidy levels.

---

## 7. The headline results

| Question | Answer |
| --- | --- |
| **Q1 — Annual curtailment** | **76.86 GWh/year** (≈ £ millions of stranded clean energy) |
| **Q2 — Max recoverable by residential DR** | **~267 MWh/year** = only **0.35%** of curtailment |
| **Q3 — Homes for 25% DR penetration** | **2,596 households** |
| **Kaluza revenue at full enrolment** | **~£3,007/year** |

### Households required, by target

| DR penetration | Households | Avoided MWh/yr | % of fleet curtailment |
| --- | --- | --- | --- |
| 10% | 1,038 | 26.4 | 0.03% |
| 25% | 2,596 | 78.7 | 0.10% |
| 50% | 5,192 | 130.2 | 0.17% |
| 100% | 10,385 | 267.3 | 0.35% |

### The "scale mismatch" — the single most important insight

In the **worst week of 2017** (25 Sep–01 Oct), **8,036 MWh** was curtailed. Even at 100% enrolment
× availability, the maximum DR the whole island's heaters could provide is a **flat line near the
bottom of the chart** — orders of magnitude smaller than the curtailment flood. **Residential
heating flexibility is a sliver of the problem.**

---

## 8. The business case

The curtailment "value pool" at full enrolment is about **£12,028/year**, split four ways:

| Actor | Annual value | Role |
| --- | --- | --- |
| **Households** | £4,811 | provide flexible load, get bill savings |
| **Wind farmers** | £3,007 | sell energy that would've been curtailed |
| **Kaluza** | £3,007 | orchestrates the DR |
| **Grid / DNO** | £1,203 | gets constraint relief |

Two stylised business models were tested:
- **Model A — Orchestrator + royalty (Kaluza-led):** Kaluza earns a share of energy value.
  Direct revenue stays small (~£3k/yr).
- **Model B — Constraint procurement (grid-led):** a grid/DNO anchor contract pays for capacity.
  This lifts Kaluza revenue dramatically (to ~£366k/yr in the illustration) but needs a multi-year
  grid contract.

**Break-even (how many homes Kaluza needs to cover install costs), by subsidy level:**

| Subsidy on hardware | Break-even homes |
| --- | --- |
| 25% | 1,296 |
| 50% | 864 |
| 75% | 432 |
| 100% | 0 |

**Bottom line:** residential participation economics alone **cannot** sustain the programme — it
needs subsidy or a grid/generator partnership.

---

## 9. The findings statement (the verdict)

Four hypotheses, all **supported**:

| Hypothesis | Verdict |
| --- | --- |
| Curtailment is material (10+ GWh) | ✅ Supported — 76.86 GWh/yr |
| Curtailment is temporally concentrated | ✅ Supported — bursty, windy low-demand periods |
| Residential DR can recover curtailed energy | ✅ Supported, but **tiny** (≤0.35%) |
| Power follows a non-linear saturating curve | ✅ Supported — validated curve, R² 0.984 |

**Strategic conclusion:** Heat Smart Orkney is **not** a curtailment-elimination solution. Its real
value is in **demonstrating that flexible-demand orchestration works** and building the operational
infrastructure (the platform, the customer relationships, the dispatch software) for *broader*
smart-grid services. Materially reducing curtailment would need **more flexible assets** — EVs,
batteries, industrial demand, or network reinforcement — well beyond residential heating.

**Recommended next step:** a **targeted winter pilot** of high-flexibility storage-heater homes
during peak-curtailment periods, to validate real-world responsiveness — combined with pursuing
**grid/generator partnerships** for a sustainable business model.

---

## 10. Limitations (be honest about these)

1. **Lower-bound estimate.** Curtailment is detected only via the setpoint signal
   (`setpoint < 891 kW`). Grid-driven reductions without a setpoint change are missed — so 76.86 GWh
   is likely a *floor*, not an exact figure.
2. **Fleet scaling is crude.** We scaled **one turbine × 500**, ignoring differences in turbine age,
   type, location, and maintenance.
3. **Fixed flexibility assumptions.** Real homes vary by occupancy, comfort, weather, and
   compliance. We didn't model thermal-storage duration, rebound effects, or intra-hour timing.
4. **Residential-only scope.** No EVs, batteries, commercial DR, or grid storage included — so the
   267 MWh is an upper bound *for residential heating only*.
5. **Economic uncertainty.** Results swing with wholesale price, capex, and regulatory incentives.
6. **Data quality.** A Sep–Oct 2017 anomaly (the metering sample size spikes) had to be flagged and
   excluded from per-household statistics.

### Future work
- Add more flexible assets (EVs, batteries, industrial) for a true system-level view.
- Replace rule-based matching with **optimisation-based control** under uncertainty.
- Add **network constraints** (voltage, transformer loading, feeder congestion) via power-system
  simulation.
- **Collect real pilot data** — the highest-priority next step.

---

## 11. The key assumptions (the "control panel")

Every headline number flows from these constants (central values shown):

| Parameter | Value | What it controls |
| --- | --- | --- |
| `HEADLINE_YEAR` | 2017 | The analysis year |
| `NAMEPLATE_KW` | 900 | Turbine max rated output |
| `NAMEPLATE_FRAC` | 0.99 | Below this fraction of nameplate ⇒ "curtailed" |
| `N_TURBINES` | 500 | Scales one turbine to the Orkney fleet |
| `FLEET_CORRELATION` | 1.0 | Assumes turbines behave identically |
| `STORM_MEAN/PEAK_MS` | 25 / 30 | Storm-shutdown thresholds (excluded) |
| `CUT_IN_MS` | 3.0 | Min wind for generation |
| `N_HOUSEHOLDS_ORKNEY` | 10,385 | Total Orkney homes (penetration denominator) |
| `F_FLEX` | 0.40 | Share of variable load that's shiftable (range 25–55%) |
| `AVAILABILITY` | 0.70 | Fraction of enrolled homes online (range 50–90%) |
| `WHOLESALE_GBP_MWH` | 45 | £ value per MWh avoided (range £35–55) |
| `KALUZA_VALUE_SHARE` | 0.333 | Kaluza's cut of the value pool |
| `HUB_GBP` | 100 | Cost per radiator control hub |
| `RADIATORS_PER_HOME` | 2 | Heating zones per home |
| `HEATER_GBP` | 300 | Heater hardware cost per home |
| `SUBSIDY_LEVELS` | 25–100% | Capex covered by programme/government |

---

## 12. What's in this repository

| Path | What it is |
| --- | --- |
| `README.md` | The full project brief (business context + analytical approach) |
| `report.ipynb` | **The deliverable** — the technical notebook (all code, analysis, figures) |
| `report.html` | The notebook rendered to HTML (no code, for reading) |
| `presentation.html` | The Palantir-style executive slide deck (open in a browser) |
| `Data/` | The two raw CSVs (turbine telemetry + residential demand) |
| `documentation/` | Briefs, FAQ, project guidelines, transcripts |
| `Class Documentation/` | Course materials, weekly slides, starter notebooks |
| `requirements.txt` | Python libraries needed (pandas, scipy, plotly, etc.) |

### The visualisations produced (all in `report.ipynb`)
- Turbine coverage + wind-speed distribution (data is annual & plausible)
- Wind→power scatter coloured by regime (curtailment is *visible*)
- Setpoint distribution + curtailed minutes by month (how/when throttling happens)
- Demand sample-size anomaly (the Sep–Oct data issue)
- Residential load shapes (diurnal, island-scale, monthly, seasonal)
- Demand distribution + weekly heatmap + monthly boxplots (load structure)
- **The fitted power curve** + residual diagnostics (the mandatory deliverable)
- Daily & cumulative curtailed energy + hour×month heatmap (the 76.86 GWh)
- Worst-week curtailed vs max DR (the scale mismatch)
- Avoided-curtailment-vs-enrolment + recovery curves (the saturation)
- Kaluza revenue vs enrolment (the thin economics)

---

## 13. If you remember only five things

1. **The problem:** Orkney wastes ~**76.86 GWh/year** of wind because the cable is too small.
2. **The idea:** switch household heaters **on** to absorb surplus wind instead of throttling
   turbines off (demand response).
3. **The catch:** residential heating can only catch **~267 MWh/year (0.35%)** — a tiny sliver.
4. **The money:** Kaluza earns only **~£3,007/year** at full scale — not viable without subsidy or
   a grid partnership.
5. **The takeaway:** HSO's value is **proving the technology and building the platform**, not
   eliminating curtailment. Scale needs more asset types (EVs, batteries, industrial).
