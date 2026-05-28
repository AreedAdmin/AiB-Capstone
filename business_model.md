# Business Model Plan — Heat Smart Orkney

> Planning document for the commercial / business-model layer of the HSO capstone.
> Purpose: agree the modelling approach here, then implement into `report.ipynb` (§6).
> Status: **PLAN — not yet implemented.** Last updated: 2026-05-28.
---

## 0. Why this document exists

The notebook already has an economics section (§6) with two illustrative structures
(Model A = Kaluza-led, Model B = grid-led), a value-pool split, a break-even table, and a
tornado sensitivity. The numbers are honest but **single-year and largely illustrative**
(hardcoded opex, magic multipliers). This plan upgrades that layer into a board-credible,
**full-DCF model ladder** that drives the project's core argument home.
---

## 1. The point the models must prove

From the findings already in the report:

- Curtailment is huge: **76.86 GWh/yr** fleet-wide.
- Residential heating DR catches only **0.35% (267 MWh/yr)** at full enrolment.
- That is worth a **~£12k/yr gross value pool**, of which **~£3k/yr** reaches Kaluza.

**Therefore the models exist to prove one thing:**

> Residential curtailment-arbitrage cannot fund a programme. Viability comes from
> subsidy, system-service (grid) contracts, and a multi-asset platform — **not** from
> wholesale energy value.

The models are deliberately built as a **ladder**: each rung answers *"what would it take
to make this work?"* and the answer escalates. That escalation **is** the argument.
---

## 2. The model ladder (the four rungs)

| Rung | Model | Revenue mechanism | What it proves |
|---|---|---|---|
| **0** | Standalone residential arbitrage (the null) | Avoided-curtailment energy value only | It fails — anchors the gap |
| **1** | Subsidy / grant-funded rollout | Arbitrage + capex grant (fuel-poverty / net-zero capital) | Households can win even when Kaluza's margin is thin |
| **2** | Grid / DNO constraint procurement | Capacity (£/MW/yr) + utilisation (£/MWh) contract | Credible path to scale — value is a *system service* |
| **3** | Multi-asset flexibility platform (value-stacking) | Arbitrage + constraint + balancing/frequency + capacity market, across heating + EV + battery + hot water | The real prize is the *platform*, not the Orkney heating slice |

### Model 0 — Standalone residential arbitrage (null / anchor)
- Kaluza monetises only avoided-curtailment energy value (~£3k/yr).
- Against ~£500/home capex → deeply negative NPV at any realistic enrolment.
- **Keep it.** It is the anchor that exposes why everything else is needed.

### Model 1 — Subsidy / grant-funded rollout
- Public / fuel-poverty / net-zero capital covers some or all capex (Year-0 inflow).
- Household value = bill savings + fuel-poverty relief.
- Extends the existing break-even-vs-subsidy table into a proper NPV view.

### Model 2 — Grid / DNO constraint procurement (anchor contract)
- Revenue decoupled from the tiny energy pool: **availability payment (£/MW/yr)** plus
  **utilisation payment (£/MWh dispatched)** under a multi-year flexibility contract.
- This is today's "Model B," made rigorous with real flex-market mechanics.

### Model 3 — Multi-asset flexibility platform (value-stacking)
- Same orchestration layer across heating + EVs + batteries + hot water.
- **Stacks** multiple revenue streams on the same enrolled asset base.
- Directly demonstrates the strategic conclusion: HSO is a platform play.
- Non-heating assets modelled as **clearly-flagged scenario multipliers** (the data does
  not support real EV/battery flex numbers).
---

## 3. Shared financial engine — full DCF

Applies to all four rungs so they are directly comparable.

- **Horizon:** 10 years.
- **Discount rate:** WACC, default **~8%** (flagged as an assumption — open question 5.1).
- **Cash flows:**
  - Year 0 = −capex (£500/home × homes, net of subsidy).
  - Years 1–10 = revenue streams − opex − churn / replacement.
- **Outputs per model:** **NPV, IRR, payback, and £/home LTV vs CAC.**
- Revenue streams by rung (this is what the value-stack waterfall visualises):
  - Model 0: wholesale arbitrage only.
  - Model 1: arbitrage + capex grant (one-off, Year 0).
  - Model 2: + capacity (£/MW/yr) + utilisation (£/MWh).
  - Model 3: + balancing/frequency + capacity-market, across multiple asset types.

---

## 4. Deliverables when greenlit

### 4.1 Notebook (`report.ipynb` §6, rebuilt)
- The 4-model ladder.
- A DCF table per model (NPV / IRR / payback / LTV vs CAC).
- Three charts:
  1. **Value-stack waterfall** — arbitrage → +constraint → +balancing → +capacity, per model.
  2. **NPV-by-model bar** — Model 0 deep negative, climbing to Model 3 positive.
  3. **Break-even frontier** — the (subsidy %, grid contract value, asset mix) combination
     where NPV crosses zero.

### 4.2 New constants (added to the cell-5 assumptions register, all labelled illustrative)
- `DISCOUNT_RATE`
- `HORIZON_YEARS`
- `CAPACITY_GBP_MW_YR`
- `UTILISATION_GBP_MWH`
- `OPEX_PER_HOME_YR`
- `CHURN_RATE`
- Asset-mix flex multipliers for Model 3 (e.g. `EV_FLEX_MULT`, `BATTERY_FLEX_MULT`).

### 4.3 Deck (`presentation.html`, optional follow-on pass)
- Promote the **value-stack waterfall** and **NPV-by-model** chart for the board.
---

## 5. Open questions to settle before implementation

1. **WACC / horizon defaults** — 8% / 10 yr acceptable?
2. **Model 3 non-heating assets** — real flex numbers vs clearly-flagged scenario
   multipliers. Recommendation: **scenario multipliers** (data doesn't support real numbers).
3. **Keep Model 0 explicitly?** Recommendation: **yes** — it is the anchor that proves the point.
---

## 6. Guardrails

- Data only supports **scenario-grade** economics — label everything illustrative.
- Keep Model 2 / 3 contract terms as transparent, named assumptions.
- No false precision (no fabricated opex to 5 significant figures).
- All new constants live in the existing assumptions register, not buried in code cells.
---

## 7. Reference — current state of §6 (what we're replacing)

- 6.1 Four-actor value table (Households, Kaluza, Wind farmers, Grid/DNO).
- 6.2 Two structures: Model A (orchestrator + royalty), Model B (constraint procurement).
- Code: `value_pool_gbp`, `split_pool`, Model A table, Model B table, break-even table,
  tornado sensitivity.
- 6.4 Interpretation, 6.5 Decision implications, 6.6 Viability improvements, 6.7 Sensitivity.
- Current capex: `HUB_GBP (100) × RADIATORS_PER_HOME (2) + HEATER_GBP (300) = £500/home`.
- Current shares: Household 0.40 / Wind 0.25 / Kaluza 0.25 / Grid 0.10.