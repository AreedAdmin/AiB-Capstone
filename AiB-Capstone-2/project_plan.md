# Heat Smart Orkney (HSO) — Project Plan

**Client:** Kaluza (formerly OVO Energy)  
**Setting:** Year **2017** — no data, prices, or statistics published after 2017 may be used as primary evidence (desk research may cite contemporaneous archives only).  
**Deliverable (Step 2):** One self-contained Jupyter Notebook (`report.ipynb`) answering the three mandated case questions and supporting a Kaluza business case.  
**Status:** Step 2 complete — see `report.ipynb`.

---

## 1. Exercise Objectives

### 1.1 Business problem

Orkney has abundant wind generation but constrained grid export (notably a **40 MW** subsea cable to mainland GB). When local generation exceeds what the island can consume or export, the network operator **curtails** wind turbines by lowering **setpoints** — caps on output — so aggregate generation stays within infrastructure limits. Curtailed energy earns no revenue and delivers no carbon benefit.

**Kaluza’s Heat Smart Orkney (HSO)** proposes **demand response (DR)** via smart control of residential electric heating (Quantum heater + retrofit hub). The platform can switch loads **almost instantaneously** when excess wind is available, turning otherwise-wasted energy into useful heat and a monetisable opportunity.

The consultancy mandate is twofold:

1. **Quantify the problem** — how much energy is curtailed today (Orkney-wide, annual).
2. **Quantify the opportunity** — how much curtailment DR can absorb at different penetration levels, and **how many households** must enrol.

The analysis must then **inform a business plan**: revenue model, costs, subsidies, break-even penetration, and actionable recommendations for Kaluza’s leadership (presentation audience) and technical stakeholders (notebook audience).

### 1.2 Mandated case questions (`Formatting Rules.txt`)

| # | Question |
|---|----------|
| **Q1** | How much energy is currently curtailed annually across the Orkney Isles? |
| **Q2** | How much can this be reduced by different levels of DR penetration? |
| **Q3** | How many local households would need to be on our DR scheme to supply this level of DR? |

### 1.3 Core datasets (2017 scenario)

| Dataset | Role | Key fields |
|---------|------|------------|
| `data/Turbine_telemetry.csv` | **One** representative 900 kW turbine, ~1 min resolution (2015–2017+) | `Timestamp`, `Power_kw`, `Setpoint_kw`, `Wind_ms` |
| `data/Residential_demand.csv` | Aggregated **proxy** residential demand, **30 min** intervals for calendar **2017** | `Timestamp`, `Demand_mean_kw` (mean **per household** in sample), `N_households` (sample size, **not** Orkney total) |

**Critical interpretation (FAQ + energy brief):**

- `N_households` ≈ 5,400 in most of 2017 is the **metering sample**, not ~10,385 total Orkney homes.
- Sep–Oct 2017 spikes in `N_households` (~32k) and late-2017 demand level shifts are **data-quality anomalies** — flag, document, and apply a consistent treatment (e.g. exclude anomalous months or cap `N_households` to a stable band).
- Official statistics post-2017 must **not** replace client data; optional sensitivity narrative only.
- Turbine telemetry has gaps and zeros — treat as real-world dirty data.

### 1.4 Broader deliverables (beyond the three questions)

Per `HSO project guidelines.pdf`, `energy_brief.pdf`, and coaching notes, a top report also includes:

- Validated **wind–power curve** (hypothesis testing).
- **Demand seasonality** linked to DR dispatch strategy.
- **Business case**: costs (£100 hub per controlled radiator; Quantum heater ~£600 in 2018 → **~£300** at 2017-equivalent per FAQ), revenue model, **subsidy scenarios** (25 / 50 / 75 / 100%), break-even DR penetration.
- Clear **assumptions & limitations**, reproducible code, storytelling (not academic question headers as section titles).

---

## 2. Grading Criteria

### 2.1 Official competencies (`HSO project guidelines.pdf`)

Markers assess:

| Competency | What “excellent” looks like |
|------------|----------------------------|
| **Hypothesis formulation & validation** | Explicit predictions (e.g. curtailment is material; events are concentrated; DR can recover a bounded share). **Power curve** validated with diagnostics (residuals, regime splits, simple vs complex model comparison). Discussion states whether hypotheses hold, with caveats. |
| **Technical analysis quality** | Rigorous handling of missing data, regimes (curtailment vs wind-limited vs storm vs downtime), defensible energy arithmetic (kW → kWh), fleet scaling, supply–demand matching at aligned timestamps. |
| **Storytelling & communication** | Logical narrative for technical readers; annotated figures; active voice; concise prose; captions on all plots. |
| **Actionable client insights** | Numbers tied to decisions: GWh curtailed, MWh avoidable at X% penetration, N households, £/year value, break-even N. |
| **Reflection / peer evaluation** | Separate from notebook; team reflective journal. |

### 2.2 Coaching “impresses vs loses marks” (`Session1_Coaching_Takeaways.pdf`)

**Impresses:**

- Orkney **context** (demographics, heating mix, barriers to adoption).
- Transparent **data problems** and cleaning ledger.
- Thorough **EDA** on demand (diurnal + seasonal profiles).
- **Power curve** modelled and validated.
- **Thread from data → business plan** (not orphan analysis).
- Thoughtful **cost / revenue** detail and **segmented marketing** view.

**Loses marks:**

- Missing the point of DR / curtailment.
- Analysis disconnected from strategy.
- Unexplained plots or appendix dumps.
- Over-engineering ML when simple methods suffice.

### 2.3 Formatting & QA (`Formatting Rules.txt`)

- Single Jupyter file preferred; appendix for heavy tables/code with **in-text references**.
- Reproducible: pinned imports, relative paths to `data/`.
- Full **QA**: spelling, grammar, proofread narrative cells.
- Main body = core findings; appendix = sensitivity tables, extra regimes, bootstrap details.

### 2.4 What we will **not** replicate from `report_beta.ipynb`

- External `src.*` modules — all logic in-notebook.
- Cached/hand-typed headline numbers disconnected from cells.
- Excessive Plotly payload / slideshow scaffolding.
- Undocumented regime taxonomy — we will simplify and explain every flag.

---

## 3. Methodology & Useful Information

### 3.1 Conceptual energy balance (`energy_brief.pdf`)

At system level (optional export layer):

```
Total energy curtailed = Total potential energy − Total residential demand − Total export
```

At **single-turbine** level (primary Q1 approach, consistent with brief examples):

```
Potential power(wind)  ≈ f_curve(Wind_ms)     # fitted on uncurtailed regimes
Actual power           = Power_kw
Curtailed power        = max(0, min(Potential, Setpoint) − Actual)   [when regime = curtailed]
```

Also:

```
Potential energy = Unrealised power + Actual generated power
```

**Interpretation of examples (brief p.8):**

- **Wind-limited:** low wind → actual ≈ potential ≪ setpoint → **no curtailment**.
- **Rated cap:** potential > 900 kW → actual capped at nameplate.
- **Demand / grid limited:** setpoint active below 900 kW; actual may track setpoint or demand context.

Setpoint **< 900 kW does not imply curtailment** if wind cannot reach setpoint anyway.

### 3.2 Turbine regime taxonomy (in-notebook, transparent)

Classify each telemetry row before curtailment sums:

| Regime | Rule (indicative) | Use |
|--------|-------------------|-----|
| **Storm** | 10-min rolling mean wind > **25 m/s** OR peak > **30 m/s** | Exclude from curve fit & curtailment energy |
| **Downtime** | `Power_kw == 0` with wind above cut-in threshold | Exclude |
| **Curtailed** | `Setpoint_kw < 0.99 × 900` and wind supports higher output than actual | **Q1 numerator** |
| **Normal** | Otherwise | **Power curve fitting** |
| **Anomaly** | `Power_kw > Setpoint_kw` by material margin (gust/momentum) | Flag; brief notes say often immaterial to annual totals |

**Storm and cut-in/out:** FAQ confirms storm thresholds; cut-in/out can be read from data but are secondary.

### 3.3 Power curve (hypothesis backbone)

**Objective:** Estimate counterfactual `P_potential(wind)` for curtailed minutes.

**Approach (2017-appropriate, simple):**

1. Filter **normal** regime rows (optionally also require `Setpoint_kw == 900`).
2. Fit a **monotone** curve — e.g. binned mean wind → power with isotonic or smooth spline — cap at **900 kW**.
3. **Validate:** RMSE/MAE on holdout wind bins; overlay rated region; check seasonality in residuals; compare to a parametric logistic/sigmoid alternative.
4. **Hypothesis statement:** “Power is a non-linear, saturating function of wind speed at ≤900 kW.” Confirm/reject in Discussion.

**Do not** use post-2017 turbine specs or ML black boxes unless justified; markers prefer interpretable fits.

### 3.4 Curtailed energy calculation (Q1)

For each curtailed timestep \(i\):

\[
\Delta P_i = \max\bigl(0,\; \min(f_{\text{curve}}(v_i),\; S_i) - P_i\bigr)
\]

\[
\Delta E_i = \Delta P_i \times \Delta t_i \quad (\Delta t_i \text{ from forward diff, cap at 1 h for gaps})
\]

**Annual headline:** Sum \(\Delta E_i\) for calendar **2017** on cleaned series.

**Fleet scaling:**

\[
E_{\text{fleet}} = E_{\text{turbine,2017}} \times N_{\text{turbines}} \times \rho_{\text{corr}}
\]

| Parameter | Central assumption | Sensitivity |
|-----------|-------------------|-------------|
| \(N_{\text{turbines}}\) | **500** (brief: >500 turbines as of Sept 2018; FAQ encourages 500 or 2017-cited figure) | 400 – 600 |
| \(\rho_{\text{corr}}\) | 1.0 (identical turbines) | 0.85 – 1.0 |

Report results in **MWh** and **GWh** with uncertainty (bootstrap by day or by month).

**Optional cross-check:** Compare curtailed share to `Total potential − demand − export` on aggregated half-hourly system model (export capped at 40 MW per hour) — state as secondary sanity check, not double-counted as headline.

### 3.5 Residential demand processing

**Convert to island-scale power:**

\[
P_{\text{demand,total}}(t) = \text{Demand\_mean\_kw}(t) \times N_{\text{hh,orkney}}
\]

Use \(N_{\text{hh,orkney}} = \mathbf{10{,}385}\) (FAQ) for scaling to full island; keep sample-weighted profiles for shape.

**Cleaning:**

- Parse UTC timestamps; verify **30 min** spacing.
- Exclude or winsorise **Aug–Oct 2017** anomaly window if `N_households` or mean demand discontinuities distort flex estimates (document in ledger).
- EDA: average **day-in-year** profiles by season (winter vs summer peaks for heating-led demand).

### 3.6 DR flexible capacity (input to Q2/Q3)

DR can only absorb **incremental** flexible load above baseline, not total demand.

**Decomposition:**

\[
P_{\text{flex}}(t) = f_{\text{flex}} \times \sigma_{\text{season}}(t) \times P_{\text{variable}}(t)
\]

| Parameter | Central | Low / high scenario |
|-----------|---------|---------------------|
| \(f_{\text{flex}}\) | **0.40** (share of demand that is shiftable heating) | 0.25 – 0.55 |
| Availability | **0.70** (devices online when called) | 0.50 – 0.90 |
| Per-household cap | Derive from seasonal profile × 0.5 h per interval | — |

**Penetration:**

\[
\text{DR penetration} = \frac{N_{\text{enrolled}}}{10{,}385}
\]

\[
P_{\text{DR}}(t) = P_{\text{flex}}(t) \times \text{penetration} \times \text{availability}
\]

### 3.7 Supply–demand matching (Q2 & Q3)

**Pipeline:**

1. Aggregate turbine **curtailed power** (or curtailed energy rate) to **30 min** to align with demand.
2. Scale supply to fleet: \(P_{\text{curt,fleet}} = P_{\text{curt,turbine}} \times N_{\text{turbines}} \times \rho_{\text{corr}}\).
3. For each interval, **avoided curtailment**:

\[
\Delta E_{\text{avoided}} = \min\bigl(E_{\text{curt,fleet}},\; P_{\text{DR}} \times 0.5\,\text{h}\bigr)
\]

4. Sum to annual **MWh avoided** vs enrolled households curve \(N \in \{0, 100, \ldots, 10385\}\).

**Q3:** Invert curve — report \(N\) needed for target reductions (e.g. 10%, 25%, 50% of fleet curtailed energy recovered).

**Delayed demand:** Note in narrative that heaters can pre-heat within comfort bands; 30 min matching is conservative (FAQ: delay negligible for case).

### 3.8 Financial / business layer (supports Discussion, not Q1–Q3 directly)

| Item | 2017 planning assumption |
|------|-------------------------|
| Hub retrofit | **£100** per radiator/device controlled |
| Quantum heater | **~£300** per household (50% of ~£600 2018 list price) |
| Platform R&D | **£0** incremental (ready to deploy) |
| Wholesale value of avoided curtailment | **£35 – £55/MWh** central **£45/MWh** (contemporaneous GB wholesale proxy — cite assumption) |
| Kaluza value capture | **~33%** of gross avoided value (negotiated share with consumer + generator) — sensitivity 20–50% |
| Consumer subsidy scenarios | Equipment subsidised **25 / 50 / 75 / 100%** |
| Revenue streams | Installation fees, consumer subscription/tiered tariff, **royalty** from wind operators on avoided curtailment |

**Break-even:** Solve smallest \(N_{\text{enrolled}}\) where annual Kaluza margin > upfront deployment cost per household × N.

### 3.9 Client & industry context (`Kaluza Industry Insights Transcript.txt`)

- Power system must balance supply and demand **continuously**; renewables shift balancing to **demand side**.
- Value = **metric before vs after**, translated to **£** for executives.
- State assumptions openly; stakeholders decide despite uncertainty.
- Privacy / GDPR relevant for real deployment (PII separate from telemetry) — mention as implementation note.
- **James Scofield / Kaluza:** simple, fast models often beat complex ones; most time is data wrangling.

### 3.10 Technology & library constraints (2017)

Use stack available in 2017: **Python 3.6+**, `pandas`, `numpy`, `matplotlib` (and optionally `seaborn`, `scipy` for isotonic/splines). Avoid post-2017 APIs or data. Plotly optional for interactivity; static matplotlib preferred for reproducibility and marking.

---

## 4. Notebook Structure

Proposed file: **`report.ipynb`** — narrative titles tell a story; the three case questions are answered explicitly in **Results** and summarised in the **Executive Summary**.

### Section 0 — Title & metadata
- Title, team, date, client, “2017 scenario” disclaimer.

### Section 1 — Executive Summary (markdown)
- One paragraph: problem, method, headline Q1–Q3 answers, business implication (£/year order of magnitude).
- Small summary table (populated by code outputs, not hand-typed).

### Section 2 — Introduction
- Orkney grid context (40 MW cable, wind-rich island).
- Kaluza HSO proposition.
- Business problem & three questions.
- **Hypotheses P1–P3** (material curtailment; temporal concentration; recoverable share bounded by flex).
- Roadmap of analysis.

### Section 3 — Data & Assumptions
- Data dictionary for both CSVs.
- **Assumptions table** (editable constants at top of notebook): `N_turbines`, `N_households_orkney`, `f_flex`, `availability`, prices, cost stack.
- Cleaning functions (inline): timestamps, duplicates, gap handling, demand anomaly policy.
- **Data quality ledger** (counts dropped per rule).

### Section 4 — Exploratory Data Analysis
- Turbine: wind vs power scatter coloured by setpoint; setpoint time series; monthly capacity factor.
- Demand: seasonal daily profiles; `N_households` stability; total island demand estimate.
- **Insight bullets** linking patterns to DR dispatch (night vs evening peaks, winter heating).

### Section 5 — Power Curve Modelling *(hypothesis validation)*
- Define `fit_power_curve()`, `predict_power()`.
- Fit on normal regime; show curve + confidence band.
- Validation metrics + residual plots.
- Brief comparison to alternative functional form.

### Section 6 — Q1: Annual Curtailed Energy (Orkney-wide)
- Regime classification function.
- `compute_curtailment_energy()` per timestep → annual single turbine 2017.
- Fleet scale + bootstrap CI.
- Figures: daily curtailment 2017; setpoint vs actual exemplar week.
- **Answer Q1** in a highlighted markdown callout (GWh/yr + CI).

### Section 7 — Residential Flexibility for DR
- `build_demand_profile()`, `estimate_flexible_kw()`.
- Sensitivity table for `f_flex` and availability.
- Figure: flexible kW profile vs curtailed supply (representative week).

### Section 8 — Q2 & Q3: DR Penetration Scenarios
- `join_supply_demand()` at 30 min.
- `avoided_curtailment_vs_households()` → curve and penetration %.
- Scenarios: low / central / high (`f_flex`, availability).
- **Answer Q2** (MWh avoided vs penetration %).
- **Answer Q3** (households required for 10%, 25%, 50% recovery targets).
- Figure: avoided MWh vs N households; optional heatmap (hour × day) of unmatched curtailed energy.

### Section 9 — Business Case & Monetisation
- Value of avoided curtailment (£/year) under price scenarios.
- Cost stack per household; subsidy sweep; break-even N.
- Revenue model narrative (consumer + wind-farm royalty).
- **Segmentation & go-to-market** (storage heaters, oil replacement, trials).

### Section 10 — Discussion
- Hypothesis verdicts (P1–P3 + power curve).
- Strengths, limitations (data proxy, single turbine, correlation factor, no export model in headline).
- Comparison to beta / why central estimate differs if applicable.

### Section 11 — Conclusion & Recommendations
- 3–5 bullet recommendations for Kaluza CEO (non-technical tone).

### Section 12 — References
- AiB datasets, energy brief, FAQ, Orkney household count source (2017-era citation only).

### Technical Appendix (same notebook, clearly labelled)
- A1: Full assumptions & sensitivity grids.
- A2: Cleaning code duplicates / alternative anomaly handling.
- A3: Bootstrap & fleet size sensitivity tables.
- A4: Optional export-limited system balance check.
- A5: Payback tables by subsidy level.

### Code organisation principles (Step 2 rules)
- All functions defined **in notebook cells** before use; simple docstrings; section-level “helper” cells acceptable.
- **English only** in code, comments, docstrings.
- Constants block at top for reproducibility.
- Every figure: title, axis labels, units (kW, kWh, MWh, GWh), caption in markdown below.

---

## 5. Implementation Sequence (after approval)

1. Set up `.venv` dependencies: `pandas`, `numpy`, `matplotlib`, `jupyter`, `scipy` (if isotonic used).
2. Build notebook skeleton following Section 4 outline.
3. Implement cleaning → EDA → power curve → Q1 → flex → Q2/Q3 → business case.
4. QA pass against checklist (Section 2.3).
5. Compare headline numbers to beta only as sanity check; reconcile differences via documented assumptions.

---

## 6. Open Decisions for Your Review

Please confirm or adjust before Step 2:

| # | Decision | Recommendation |
|---|----------|----------------|
| 1 | Headline year for turbine | **2017** (align with demand) |
| 2 | Fleet size | **500** turbines |
| 3 | Demand anomaly months | **Exclude Sep–Oct 2017** from flex profiling (FAQ: likely anomaly) |
| 4 | Headline Q1 method | **Power-curve counterfactual** on curtailed regimes (primary); system balance as appendix |
| 5 | Export modelling | **Appendix only** (40 MW cap) unless you want it in headline |
| 6 | Visualisation library | **Matplotlib** primary (marking reproducibility) |

---

**Next step:** Upon your approval of this plan (and any changes to Section 6), I will implement **`report.ipynb`** per Section 4 and Step 2 execution rules.
