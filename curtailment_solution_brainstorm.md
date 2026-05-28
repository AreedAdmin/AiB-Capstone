# Curtailment Solution & Win-Win Business Model — Brainstorming Plan

> **Purpose:** brainstorm a *workable* answer to the two problems the analysis exposed:
> (1) how to actually absorb Orkney's curtailment at a material scale, and (2) a business
> model where **the grid (SSEN), Kaluza, wind generators, households, and the public purse
> all win and most of them make money**.
> **Status:** BRAINSTORM — for review, not yet committed. Created 2026-05-28.
> **Companion to:** `business_model.md` (the DCF model-ladder plan) and `sumamryh.md` (findings).

---

## 0. The problem in one paragraph (why the current model fails)

Orkney curtails **~76.86 GWh/yr** of wind. Residential *heating* demand response can absorb
only **~267 MWh/yr (0.35%)** even at 100% enrolment, generating a **~£12k/yr** value pool
(~£3k/yr to Kaluza). That is a rounding error — it cannot fund hardware, let alone a
business. The reason is structural, not a tuning problem:

1. **Wrong asset.** Household heating is a *small, time-constrained* sink. Curtailment
   arrives in multi-GWh bursts during windy, low-demand periods; heaters can soak up only a
   trickle and only when someone wants heat.
2. **Wrong revenue.** Wholesale energy value of curtailed power is near-zero by definition
   (it's curtailed *because* nobody will pay for it). Arbitrage on a worthless commodity
   stays worthless.
3. **Wrong frame.** We priced a *sliver of one asset class against the spot price*. The
   real money in flexibility is **system services** (capacity, constraint, balancing) and
   **avoided network capex** — not energy arbitrage.

**The fix has two halves, and we need both:**

> **Physical:** add *bigger, dumber, cheaper* energy sinks (thermal stores, EVs, batteries,
> hydrogen, flexible industrial load) so there is actually somewhere for the energy to go.
>
> **Commercial:** stop selling energy and start selling *flexibility as a system service*,
> then **stack** several revenue streams onto the same enrolled asset base so every
> stakeholder is paid from a different pocket.

---

## 1. The stakeholders — what each one actually needs

| Stakeholder | What they have | What they want | What "winning" looks like |
|---|---|---|---|
| **Wind generators** (often community-owned, curtailed first) | Stranded clean energy worth ~£0 when curtailed | Any revenue on curtailed MWh; higher capacity factor | Get paid *something* for energy that was £0 → pure upside |
| **Households** (many fuel-poor) | Flexible load, roof/garage space, EVs | Cheaper/warmer homes, no upfront cost | Lower bills + warmth + possibly an asset stake |
| **Kaluza** | The orchestration platform, dispatch software, customer base | A *scalable, repeatable* revenue product — not a one-island science project | Recurring % of a *stacked* multi-MW revenue pool |
| **Grid / DNO (SSEN)** | The constraint (40 MW cable), a huge reinforcement bill | Defer/avoid capex, manage constraints, hit Ofgem targets | Flexibility cheaper than copper → regulated/shared savings |
| **Government / public funders** | Fuel-poverty & net-zero capital, carbon targets | Decarbonisation, fuel-poverty relief, jobs, a replicable model | Public £ leveraged into a self-sustaining template |
| **System Operator (NESO) / GB market** | Balancing, capacity & ancillary markets | Cheap flexibility, frequency response | Orkney flex bid into national markets |

**Key realisation:** no single pocket pays enough. The win-win comes from **paying each
stakeholder out of the pocket that values the service most**, and orchestrating all of them
on one platform. That is Kaluza's actual product.

---

## 2. Physical layer — give the energy somewhere to go (the "sink stack")

Ranked by how much curtailment each could realistically absorb on Orkney. Residential
heating is deliberately at the bottom — it's the *proof of concept*, not the solution.

| # | Sink | Curtailment-absorption potential | Why it fits Orkney | Maturity |
|---|---|---|---|---|
| **A** | **Green hydrogen electrolysis** | **Very high (GWh-scale)** | Orkney already pioneered this (EMEC, Surf 'n' Turf, BIG HIT). Electrolysers are the textbook curtailment sink — large, interruptible, location-flexible. H₂ sells into ferries, buses, heating, export. | Proven on-island, scaling |
| **B** | **Flexible industrial / compute load** | **High** | Site interruptible load *behind the constraint*: green data centre / AI-or-crypto compute, cold storage, desalination, aquaculture processing — runs only when wind is free. | Mature elsewhere |
| **C** | **Community / grid-scale batteries** | **Medium–High** | Store the burst, release over hours/days; also earn frequency & balancing revenue. | Mature |
| **D** | **Smart EV charging + V2G** | **Medium** | Orkney has high EV uptake; charge on surplus wind, V2G discharges back. Big, growing, household-owned. | Smart charging mature; V2G emerging |
| **E** | **Thermal storage (the upgrade to today's HSO)** | **Low–Medium** | Replace "switch a radiator on now" with **high-capacity storage heaters + hot-water/heat-battery tanks** that bank hours of heat → decouples absorption from comfort timing. District-heat power-to-heat where feasible. | Mature |
| **F** | **Residential live heating DR (today's HSO)** | **Tiny (0.35%)** | Keep it as the *demonstrator* and the customer-relationship beachhead — not the value driver. | Proven (this project) |

**Design principle:** curtailment is **bursty and cheap**. The best sinks are **big, cheap,
interruptible, and storage-backed** so they don't need the energy *the instant* it appears.
A portfolio (A+C+D+E) smooths the mismatch the worst-week chart exposed (8,036 MWh in one
week vs a flat DR line).

---

## 3. Commercial layer — the revenue stack (stop selling energy)

The same enrolled MW earns from **multiple markets at once**. This is "value stacking" and
it's how aggregators actually make money.

| Revenue stream | Who pays | Rough basis | Why it's bankable here |
|---|---|---|---|
| **1. Network constraint / flexibility** | **SSEN (DNO)** | £/MW/yr availability + £/MWh utilisation | The 40 MW cable *is* the constraint — flexibility that defers reinforcement is worth real money (avoided capex shared). This is the **anchor contract**. |
| **2. Curtailment PPA arbitrage** | Wind generators → offtakers | The spread between ~£0 (curtailed) and retail/H₂/heat value | Generators sell otherwise-lost MWh cheaply; the spread funds everyone. Pure upside for them. |
| **3. Balancing & ancillary (frequency)** | NESO / national markets | £/MW for response, £/MWh dispatched | Batteries + aggregated load bid into GB-wide markets — revenue independent of local curtailment. |
| **4. Capacity Market** | GB capacity market | £/kW/yr for guaranteed availability | Aggregated flexible fleet qualifies as a CMU. |
| **5. Retail tariff margin / ToU** | Households | Spread on a "wind-tracking" cheap tariff | Households get cheap power when wind is surplus; Kaluza/supplier earns the platform margin. |
| **6. Fuel-poverty & net-zero capital** | Government / ECO / Scottish funds | Capex grant (Year-0 inflow) | Covers hardware so households pay £0 upfront; de-risks rollout. |
| **7. Carbon / green premium** | Corporates, H₂/data-centre offtakers | £/tCO₂ or green-product premium | "Made with curtailed Orkney wind" is a sellable green attribute. |

**The trick:** streams 1, 3, 4 are *capacity/availability* payments — they pay **whether or
not** curtailment happens that day, decoupling revenue from the tiny energy pool. Stream 2
turns the worthless curtailed MWh into the cheap *fuel* that makes streams 5–7 profitable.

---

## 4. The win-win business model — three candidate structures

### Model X — "Flexibility-as-a-Service Aggregator" (Kaluza-led platform)
- **Kaluza** orchestrates the whole sink stack (§2) and bids it into every market (§3).
- Revenue flows to Kaluza, which pays each asset owner their share and keeps a platform fee
  (e.g. 10–20% of stacked revenue).
- **Pros:** scalable, repeatable beyond Orkney, asset-light for Kaluza. **This is the
  product Kaluza can actually sell to the next island/region.**
- **Cons:** needs the anchor DNO contract (Stream 1) to underwrite it.

### Model Y — "Constraint Procurement Anchor" (SSEN-led, Kaluza delivers)
- **SSEN** procures X MW of flexibility via a multi-year contract *instead of/to defer*
  cable reinforcement; Kaluza is the delivery partner.
- This is today's "Model B" made real — and it's where the big numbers live (the report's
  illustrative ~£366k/yr to Kaluza came from exactly this lever).
- **Pros:** anchor revenue, regulator-backed (Ofgem's "flexibility-first" mandate).
  **Cons:** procurement cycles are slow; needs SSEN at the table early.

### Model Z — "Community Energy SPV / Co-op" (shared ownership)
- A **community-owned SPV** owns the assets (batteries, electrolyser, thermal stores);
  households/community buy in or are gifted equity via grant capital.
- Kaluza operates it for a fee; profits are shared back to the community.
- **Pros:** maximal local buy-in, fuel-poverty alignment, story sells to funders.
  **Cons:** governance overhead; slower to stand up.

> **Recommendation to test:** a **hybrid** — Model Y's DNO anchor contract underwrites a
> Model X platform, with a Model Z community-ownership wrapper for the household-facing
> assets and grant capital. Each stakeholder is paid from the pocket that values them most.

---

## 5. Who pays whom — the value-flow (the win-win made explicit)

```
   PUBLIC FUNDS ──grant──> HARDWARE (heaters, EV chargers, batteries, electrolyser)
        │                          │
        │                          ▼
   WIND GEN ──cheap curtailed MWh──> KALUZA PLATFORM ──orchestrates──> SINK STACK (§2)
        ▲                          │   │   │   │
        │ paid for £0 energy       │   │   │   └──> HOUSEHOLDS: cheap warmth, £0 upfront
        │                          │   │   └──────> H₂ / DATA-CENTRE offtake: green product £
        │                          │   └──────────> NESO markets: balancing/capacity £
   SSEN (DNO) <──defers cable capex─┘   └──────────> SSEN: constraint-relief £/MW/yr
        │
        └──shares avoided-reinforcement savings──> back into the pool
```

**Every arrow is someone winning:**
- **Wind gen:** revenue on £0 energy → pure upside, higher effective capacity factor.
- **Households:** free hardware + cheaper/warmer homes (+ optional co-op dividend).
- **Kaluza:** recurring platform fee on a *stacked, multi-MW* pool — a real product.
- **SSEN:** flexibility cheaper than copper → deferred capex, Ofgem brownie points.
- **Government:** fuel-poverty + net-zero outcomes, a *replicable template* for other
  constrained regions (the real ROI on the grant).
- **Climate/GB:** more clean energy actually used, less waste.

---

## 6. Numbers to pressure-test (illustrative — to be modelled in `report.ipynb` §6)

These are the levers that move the model from £3k/yr to a real business. Each should become
a clearly-flagged assumption in the DCF ladder (`business_model.md`).

| Lever | Today (residential-only) | Target to test | Where the money comes from |
|---|---|---|---|
| Addressable curtailment absorbed | 267 MWh/yr (0.35%) | **5–30%** with H₂ + batteries + EV | §2 sinks A–D |
| Flexible MW under management | <1 MW effective | **5–40 MW** | Multi-asset fleet |
| Revenue per MW/yr | ~£0 (energy only) | **£20k–£60k/MW/yr** (constraint + balancing + capacity) | §3 streams 1,3,4 |
| Kaluza take | ~£3k/yr | **£100k–£500k+/yr** | Platform fee on stacked pool |
| Household upfront cost | £500 | **£0** | §3 stream 6 (grant) |
| Generator revenue on curtailed MWh | £0 | **>£0** (any PPA price) | §3 stream 2 |

> **Honesty guardrail (carry over from `business_model.md`):** the data only supports
> *scenario-grade* economics for non-heating assets. Model EV/battery/H₂ as **clearly
> flagged scenario multipliers**, not false-precision forecasts. The *direction* (residential
> alone fails → platform + system services + storage sinks wins) is robust; the magnitudes
> are illustrative.

---

## 7. Phased roadmap (de-risked, fundable in stages)

| Phase | Horizon | What | Primary stakeholder | Funding |
|---|---|---|---|---|
| **0 — Demonstrator** | Now | Targeted **winter storage-heater pilot** (the report's recommended next step) + collect real responsiveness data | Households + Kaluza | Grant |
| **1 — Anchor contract** | 6–18 mo | Sign an **SSEN flexibility/constraint contract** (Stream 1) — the bankable underwrite | SSEN | DNO procurement |
| **2 — Add storage sinks** | 1–2 yr | Community batteries + smart EV charging; stack balancing/capacity revenue (Streams 3,4) | Kaluza + households | Anchor revenue + grant |
| **3 — Big sink** | 2–4 yr | **Green hydrogen / flexible industrial offtaker** to absorb GWh-scale curtailment (Stream 2,7) | Wind gen + offtakers | Project finance / SPV |
| **4 — Replicate** | 4 yr+ | Package the platform as a product for other constrained regions/islands | Kaluza | Commercial |

Each phase pays for the next and is independently defensible to a funder/board.

---

## 8. Risks & open questions to settle before implementation

1. **DNO appetite:** will SSEN actually procure flexibility vs. just build the cable
   (a ~220 MW Orkney–Caithness link has been progressing)? → Flexibility's role may be the
   *bridge before* and the *constraint-management after* the upgrade. **Confirm SSEN's stance.**
2. **Cable upgrade interaction:** if the new interconnector lands, does curtailment shrink
   enough to kill the case — or does high-wind constraint persist? **Model both worlds.**
3. **Hydrogen economics:** electrolyser capex + H₂ offtake demand on Orkney — real or still
   subsidy-dependent? **Sanity-check against EMEC/BIG HIT outcomes.**
4. **Stacking rules:** can the same MW legally earn constraint + balancing + capacity
   simultaneously, or are there exclusivity rules? **Check market eligibility.**
5. **Grant availability:** which specific funds (ECO, Scottish Government fuel-poverty,
   net-zero capital) are live and stackable? **Map the funding landscape.**
6. **Who owns the assets** (Kaluza / SPV / households / SSEN)? Drives the win-win split and
   the DCF. → links to Model X/Y/Z choice in §4.
7. **WACC / horizon** for the SPV (carry the 8% / 10-yr defaults from `business_model.md`).

---

## 9. The one-line pitch per stakeholder (for the deck)

- **To SSEN:** "Flexibility is cheaper than copper — we defer your reinforcement bill and
  manage your constraint for a fraction of the capex."
- **To Kaluza:** "Orkney isn't the prize — it's the *template*. We build a stacked-revenue
  flexibility platform here and sell it to every constrained region after."
- **To wind generators:** "We pay you for energy that earns £0 today. Pure upside."
- **To households:** "Free hardware, warmer home, lower bills — and a stake in the energy
  your island already makes."
- **To government:** "Leverage your fuel-poverty and net-zero £ into a self-sustaining,
  replicable model — not a one-off subsidy."

---

## 10. What to do with this doc

1. **Review & prune** — kill the structures/sinks we don't believe (esp. H₂ if Orkney
   economics don't hold).
2. **Pick the model** (recommend the §4 hybrid) and the §2 sink portfolio to model.
3. **Feed §6 levers into `business_model.md`'s DCF ladder** — add Model 4: "Multi-asset
   stacked-revenue platform" as the top rung, replacing the thin residential-only top.
4. **Confirm the §8 open questions** (esp. SSEN stance + cable upgrade) before any numbers
   go to the board.
5. **Build the §5 value-flow diagram and §9 pitch lines into `presentation.html`.**
```
