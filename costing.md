# Costing — Heat Smart Orkney

> The money side of the analysis: what curtailment is worth, what demand response can
> recover, and what each business model costs and returns. All figures are 2017 proxy
> economics and **illustrative / scenario-grade** — they support direction and order of
> magnitude, not point precision. Source: `report.ipynb` (§3 and §6).

---

## 1. The prize — theoretical value of curtailed energy

The full value of the wind energy thrown away each year (76,861 MWh/yr = 76.86 GWh/yr at
fleet scale), valued at the wholesale price. This is the loss **before** any DR recovery.

| Wholesale price | Single turbine (£/yr) | **Fleet — 500 turbines (£/yr)** |
|---|---|---|
| Low (£35/MWh) | £5,380 | **£2.69m** |
| **Central (£45/MWh)** | £6,916 | **£3.46m** |
| High (£55/MWh) | £8,454 | **£4.23m** |

- **Headline: ~£3.46m/yr** stranded by curtailment (central price).
- With volume uncertainty (90% CI on curtailed MWh) **and** the price range, the loss spans
  roughly **£2.2m – £5.1m/yr**.

---

## 2. The sliver — what residential DR actually recovers

```
Theoretical loss (all curtailment):   ~£3,458,000 / yr   ← the prize
Residential DR can recover:               ~£12,028 / yr   ← 0.35% of it
Kaluza's share of that pool (25%):         ~£3,007 / yr
```

Residential heating flexibility recovers only **267 MWh/yr** of the 76,861 MWh curtailed —
**0.35%**. The £12,028/yr "value pool" is a thin sliver of the £3.46m total loss. This is the
core reason the business case cannot rest on capturing curtailment energy.

### Four-actor split of the £12,028 energy pool (full enrolment)

| Actor | Share | £/yr |
|---|---|---|
| Households | 40% | £4,811 |
| Wind farmers | 25% | £3,007 |
| Kaluza | 25% | £3,007 |
| Grid / DNO | 10% | £1,203 |

---

## 3. The cost side — per-home unit costs

| Item | Value | Note |
|---|---|---|
| Hub | £100 × 2 radiators | `HUB_GBP × RADIATORS_PER_HOME` |
| Heater | £300 | `HEATER_GBP` (2017 money) |
| **Capex per home (CAC)** | **£500** | heating-only models |
| Capex per home (Model 3) | £700 | +£200 EV/battery integration |
| Opex per home | £12 / yr | platform, comms, dispatch, metering |
| Churn drag | 3% / yr of capex | ≈ £15/home/yr (heating-only) |

DCF basis: **10-year horizon, 8% discount rate** (annuity factor 6.71), evaluated at full
enrolment (10,385 homes), from Kaluza's point of view.

---

## 4. The business-model ladder — costs vs returns

| Rung | Model | Revenue £/home/yr | Net £/home/yr | NPV/home | IRR | Payback | **Fleet NPV** |
|---|---|---|---|---|---|---|---|
| 0 | Standalone arbitrage | £0.29 | −£26.71 | −£679 | n/a | >10y | **−£7.0m** |
| 1 | Subsidised arbitrage (100% grant) | £0.29 | −£26.71 | −£179 | n/a | >10y | **−£1.9m** |
| 2 | Grid constraint contract | £40.15 | +£13.15 | −£412 | −19% | >10y | **−£4.3m** |
| 3 | Multi-asset value stack | £561.44 | +£528.44 | +£2,846 | 75% | 1.3y | **+£29.6m** |

### Value stack — revenue per home per year by source

| Stream | M0 | M2 | M3 |
|---|---|---|---|
| Energy arbitrage | £0.29 | — | — |
| Capacity (availability) | — | £35.00 | £105.00 |
| Utilisation (energy) | — | £5.15 | £15.44 |
| Frequency response | — | — | £252.00 |
| Capacity market | — | — | £189.00 |
| **Total** | **£0.29** | **£40.15** | **£561.44** |

### Break-even subsidy frontier (NPV/home crosses £0)

| Capex subsidy | Model 2 NPV/home | Model 3 NPV/home |
|---|---|---|
| 0% | −£412 | +£2,846 |
| 25% | −£287 | +£3,021 |
| 50% | −£162 | +£3,196 |
| 75% | −£37 | +£3,371 |
| 100% | +£88 | +£3,546 |

Model 2 reaches break-even only near **100% capex subsidy**; Model 3 is positive at any
subsidy level (and unsubsidised).

---

## 5. The costing conclusion

1. The energy lost is genuinely valuable in aggregate (**~£3.46m/yr**), but residential DR
   can monetise only **0.35%** of it.
2. The pure-energy play (Rungs 0–1) is structurally loss-making — even free hardware loses
   money, because £0.29/home revenue cannot cover ~£27/home operating cost.
3. A grid/DNO constraint contract (Rung 2) makes **operations** profitable (+£13/home) but
   the rollout still needs heavy capex subsidy.
4. The case turns decisively positive only by **stacking system services across multiple
   asset types** (Rung 3): **+£29.6m fleet NPV, 75% IRR, 1.3-yr payback.**

The cost structure points to a **partnership-/contract-led, multi-asset platform**, not a
residential-arbitrage rollout funded by avoided-curtailment value.
