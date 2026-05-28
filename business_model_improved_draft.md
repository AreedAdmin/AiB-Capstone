# Business Model — Improved Draft (DROP-IN for Report Section 6)


## 6. Business Model & Recommendation

### 6.1 The problem the numbers force

On residential heating alone, Heat Smart Orkney absorbs **267 MWh/year (0.35%)** of the
**76.86 GWh** Orkney curtails — a gross value of **£12,028/year**, of which Kaluza's share is only
**~£3,007/year**. Spread over 10,385 homes that is **≈£1.16 of curtailment value per home per year**,
against hardware of **£200–£500 per home**. On avoided-curtailment value alone, no subsidy makes this
a business.

The conclusion is not to abandon HSO, but to **reposition it**: from a *curtailment product sold to
households* into a **flexibility-orchestration platform** whose revenue comes from a recurring
service, a broadening asset base, and system-level contracts — with residential heating as the entry
wedge, not the business itself.

### 6.2 The size of the prize (why the opportunity is real even if the current capture is small)

The captured value is small; the *available* value is not. The gap between them is the strategy.

| Scenario | Energy captured | @ £45/MWh | @ £150/MWh* | Kaluza @ 25% |
|---|---|---|---|---|
| Residential heating only (current) | 267 MWh (0.35%) | £12k | £40k | £3k–£10k |
| Multi-asset, ~10% captured | ~7,700 MWh | £346k | £1.15M | £86k–£288k |
| Full curtailment (theoretical ceiling) | 76,860 MWh (100%) | £3.46M | £11.5M | £0.9M–£2.9M |
| Network constraint relief (deferred cable upgrade) | — | one-off, £millions | — | negotiated |

\*£150/MWh reflects avoided curtailment valued at the PPA + ROC support stack rather than bare
wholesale. **[SOURCE NEEDED — 2017]**. The 100% row is the *size of the gisement if fully absorbed*,
not a residential-achievable figure (it would need industrial-scale flexible load).

### 6.3 How Kaluza makes meaningfully more — three levers

| Lever | Type | Illustrative basis | What it adds |
|---|---|---|---|
| **M1 — Recurring platform/service fee** | Business model | Smart-heating + bill-optimisation service, **£18–25/home/year** **[ASSUMPTION; anchor to ~£1.50–2/month comparator]** | Decouples revenue from the tiny curtailment slice — the floor that makes it a business |
| **M2 — Broaden the flexible asset base** | Product/scope | Add EVs, hot-water/immersion, batteries, C&I loads under one orchestration layer | Captures more of the 76.86 GWh → grows energy revenue toward the §6.2 ladder |
| **M3 — Grid service + public funding** | Business model + policy | DNO flexibility/capacity payment; fuel-poverty / decarbonisation capex subsidy | Prices the system value retail margin can't; de-risks rollout |

**Honesty guardrail:** M1 must be justified by the *household* value (cheaper, smarter heating), not
by curtailment (worth ~£1/home). M2 is a product change, not just pricing. M3's DNO flexibility
market was **nascent in 2017 [SOURCE NEEDED]** — present it as a forward bet.

### 6.4 Illustrative revenue stack (Kaluza, £/year)

| Revenue line | Conservative (residential wedge) | Ambitious (multi-asset platform) |
|---|---|---|
| Platform/service fee (M1) | ~£190k (10,385 homes × £18) | ~£260k (× £25) |
| Curtailment royalty (M2, Kaluza 25%) | £3k (@£45, residential) | ~£288k (10% capture @£150) |
| Grid flexibility / availability (M3) | ~£0–5k (market immature) | ~£50–150k (anchor contract) |
| **Annual total (indicative)** | **~£200k/yr** | **~£550k–700k/yr** |
| Network-deferral value (one-off) | — | £millions, conditional on M2 |

vs. the current model's **£3k/year**. All figures **[ASSUMPTION]** — defend each line; do **not**
present as model outputs.

### 6.5 Per-home unit economics (why the retrofit pivot matters)

| | Full replacement | **Retrofit-only (recommended)** |
|---|---|---|
| Capex/home | ~£500 (hub + heater) | **~£200 (hub on existing storage heaters)** |
| Annual service fee (M1) | £18–25 | £18–25 |
| Simple payback, no subsidy | ~20 yr | ~10 yr |
| Simple payback, 50% subsidy | ~10 yr | **~5–6 yr** |

The **retrofit-only + recurring fee + 50% subsidy** combination is the only configuration with a
defensible per-home payback. This is the unit-economics case for the pivot.

### 6.6 Market & segmentation (Orkney, 2017)

10,385 households; **~63% fuel poverty [SOURCE NEEDED]**; mixed heating stock.

| Segment | Basis | Capex | Priority |
|---|---|---|---|
| A — Electric storage-heater homes | Retrofit-ready | ~£200 | **First** — lowest cost, fastest dispatch |
| B — Oil / solid-fuel homes | Need replacement | ~£500 | Subsidy-led (fuel-poverty funding) |
| C — Commercial / community loads (distilleries, halls, harbour) | Few sites, high volume | Bespoke | **High flex per site**, best curtailment coincidence |

Channel: partner with **Community Energy Scotland** + local project officers for trusted access;
free/subsidised retrofit with a bill-saving guarantee to overcome adoption friction.

### 6.7 Recommendation — three horizons

| Horizon | Move | Goal | Revenue |
|---|---|---|---|
| **1 — Prove it** | Winter pilot, retrofit-only, Segment A, contract-backed + subsidised | Measure real flexibility & dispatch reliability cheaply | Grid anchor + subsidy + M1 |
| **2 — Scale the platform** | Add EV/battery/immersion; pool multiple wind farms | Grow dispatchable MWh (the binding constraint) | M1 + M2 royalty |
| **3 — Flexibility-as-a-service** | Sell constraint relief to the DNO; add C&I "sponge" loads | Capture system value beyond residential | M3 grid contracts |

**Board line:** *"Residential curtailment alone is worth ~£3k/year — which is exactly why HSO must
be a flexibility **platform**, not a heating product. Fund a contract-backed winter pilot, then scale
to multi-asset + grid services where the £3.5M+ prize actually sits."*

### 6.8 Risks & viability conditions

- **Behavioural:** comfort overrides / rebound erode the 0.7 availability assumption.
- **Subsidy dependence:** near-term case leans on public/grid funding — policy risk.
- **Regulatory maturity:** 2017 DNO flexibility procurement was early — grid revenue is a forward bet.
- **Price compression:** curtailment coincides with wind gluts when prices fall, squeezing energy value **[ASSUMPTION]**.

---

## TEAM NOTES (not for the report body)

### A. Number fixes to make in `report.ipynb` BEFORE using this section

1. **£3,007 vs £4,005 — one Kaluza share everywhere.** Set `KALUZA_VALUE_SHARE = SHARE_KALUZA = 0.25`
   so the four-actor split (0.40/0.25/0.25/0.10 = 1.0) holds and £3,007 appears in the summary table,
   value pool, and Discussion alike. Re-run.
2. **Separate one-off capex from annual flows** in Models A/B. Show capex as a one-off row and report
   a payback period (or annualise capex over device life ~10 yr). Don't put £2.6M capex in an
   "annual cost" column next to £5k annual value.
3. **Remove the Model B £366k artifact** (it's mostly 10% of a grid subsidy counted as Kaluza
   revenue). Replace with an explicit grid service fee (£/home/yr or £/MWh dispatched) — see M3.
4. **Pick one £/MWh valuation basis** and label it: £45 wholesale (conservative) and/or £150 PPA+ROC
   (upside). Don't let both float unlabelled.

### B. Assumptions that need a 2017-era source or a defensible anchor

- £150/MWh PPA + ROC value for avoided curtailment.
- ~63% Orkney fuel-poverty figure.
- £18–25/home/year platform/service fee (anchor to a real smart-energy service comparator).
- DNO flexibility/capacity payment existence & rate in 2017.
- Network-reinforcement (cable upgrade) deferral value.


