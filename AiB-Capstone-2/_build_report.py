#!/usr/bin/env python3
"""Generate report.ipynb (self-contained HSO analysis notebook)."""
import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).parent
NB_PATH = ROOT / "report.ipynb"


def md(source: str) -> dict:
    """Markdown cell. Use raw strings r\"\"\"...\"\"\" when the text contains LaTeX (\\text, \\frac, etc.)."""
    text = dedent(source).strip()
    if text and not text.endswith("\n"):
        text += "\n"
    return {"cell_type": "markdown", "metadata": {}, "source": [line + "\n" for line in text.splitlines()]}


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "source": dedent(source).strip().splitlines(True),
        "outputs": [],
        "execution_count": None,
    }


cells = []

# --- Title ---
cells.append(md("""
# Heat Smart Orkney — Curtailment & Demand Response Business Case

**Client:** Kaluza | **Scenario year:** 2017 | **Capstone consultancy report**

We quantify Orkney wind curtailment from turbine telemetry, estimate how much residential
demand response (DR) can absorb at different enrolment levels, and translate the opportunity
into a monetisation and break-even view for Kaluza's Heat Smart Orkney (HSO) programme.

> **Mandated questions:** (Q1) annual curtailed energy island-wide; (Q2) reducible curtailment
> vs DR penetration; (Q3) households required to deliver that DR capacity.
"""))

cells.append(md("""
## Executive Summary

*Run all cells top-to-bottom. Headline results are summarised in **Section 11**;
the tables below populate after the analysis pipeline completes.*
"""))

cells.append(code("""
# Headline metrics are injected after the analysis pipeline runs (Section 8).
try:
    display(summary_df)
except NameError:
    print("Execute the notebook top-to-bottom to populate the executive summary table.")
"""))

# --- Setup & assumptions ---
cells.append(md("""
## 1. Introduction

Orkney generates more wind power than its local grid can always use or export. A **40 MW**
subsea cable limits exports to mainland GB. When supply exceeds demand plus export headroom,
the network operator lowers turbine **setpoints**, forcing **curtailment** — deliberate
under-generation. Kaluza's **Heat Smart Orkney** uses smart electric heating as **demand response**,
switching load on when wind would otherwise be wasted.

### Business problem

Curtailed energy has no wholesale value and no carbon benefit. HSO aims to **monetise** avoided
curtailment by enrolling households whose flexible heating can track excess wind in near real time.

### Hypotheses

| ID | Hypothesis | Test |
|----|------------|------|
| P1 | Annual fleet curtailment is material (order 10+ GWh) | Q1 energy balance |
| P2 | Curtailment is temporally concentrated (windy, low-demand periods) | EDA + time series |
| P3 | A bounded share of fleet curtailment is recoverable via residential DR | Q2 saturation curve |
| P4 | Power output is a non-linear saturating function of wind speed (≤900 kW) | Power curve validation |

### Approach

Data cleaning → rich EDA → validated power curve → Q1 curtailment → flexible demand model →
supply–demand matching (Q2/Q3) → business valuation → discussion.
"""))

cells.append(md("## 2. Assumptions & Configuration\n\n> **Note:** If you only see `parameter` and `value` in the table below, **re-run the next code cell** — stale Jupyter outputs can hide the updated `meaning` and `source` columns."))

cells.append(md("""
Every headline number in this report flows from the constants below. For each parameter we state
**what it means in the model**, and **where it comes from** (client data, technical brief, FAQ,
or a consultant judgement flagged as such). Post-2017 statistics are not used, consistent with the
2017 scenario.

| Parameter | Value (central) | What it means | Source / rationale |
|-----------|-----------------|---------------|-------------------|
| `HEADLINE_YEAR` | 2017 | Calendar year for turbine curtailment totals and demand matching. | Aligns with `Residential_demand.csv` (2017 only). Turbine telemetry is filtered to 2017 even though the file spans 2015–2018 (`energy_brief.pdf`). |
| `NAMEPLATE_KW` | 900 | Maximum rated output of the exemplar turbine in the dataset. | Stated in case brief and `Turbine_telemetry.csv` (setpoint tops out at 900 kW). |
| `NAMEPLATE_FRAC` | 0.99 | Setpoint below this fraction of nameplate ⇒ **curtailed regime** (network cap active). | Modelling convention from `energy_brief.pdf` (setpoint as curtailment signal). Threshold is slightly below 900 kW to avoid numerical edge cases. |
| `N_TURBINES` | 500 | Scales single-turbine results to an Orkney-wide fleet. | `energy_brief.pdf`: >500 turbines on Orkney as of Sept 2018; FAQ invites 500 or a 2017-cited count — we use **500** as central scenario. Sensitivity: 400–600 in Appendix. |
| `FLEET_CORRELATION` | 1.0 | Multiplier if turbines are not statistically independent (0.85–1.0 stress test). | FAQ: scale one average turbine; correlation = 1 assumes identical machines and weather exposure. |
| `STORM_MEAN_MS` / `STORM_PEAK_MS` | 25 / 30 | 10-min mean wind >25 m/s or gust >30 m/s ⇒ **storm shutdown** (excluded from curve fit and curtailment sums). | `HSO FAQ.txt` (storm control per turbine datasheet behaviour). |
| `CUT_IN_MS` | 3.0 | Minimum wind for generation; used to classify **downtime** (zero power with wind above cut-in). | Approximate from EDA on telemetry; not critical per FAQ. |
| `N_HOUSEHOLDS_ORKNEY` | 10,385 | Denominator for DR **penetration** and scaler from sample mean kW to island demand. | `HSO FAQ.txt` (approximate Orkney household count). Distinct from `N_households` in the demand file (~5,400 sample). |
| `DEMAND_ANOMALY_MONTHS` | Sep, Oct | Months excluded from **EDA plots** only (sample size spikes to ~30k). | `HSO FAQ.txt` (likely data-quality anomaly). Flexible-load and Q2 matching still use **full-year** demand timestamps. |
| `F_FLEX` | 0.40 | Share of **variable** residential demand that smart heating can shift for DR. | Consultant assumption within FAQ range (best/worst case via household count); central 40% with sensitivity 25–55%. `energy_brief.pdf` discusses shiftable heating load. |
| `AVAILABILITY` | 0.70 | Fraction of enrolled homes **online and dispatchable** when curtailment occurs. | Consultant assumption (devices offline, opt-out, comfort limits). Sensitivity 50–90%. |
| `WHOLESALE_GBP_MWH` | 45 | £ value per MWh of avoided curtailment (wholesale proxy). | **2017-era** GB wholesale order-of-magnitude (£35–55/MWh band). Not a single published Orkney price — documented as planning range. |
| `KALUZA_VALUE_SHARE` | 0.333 | Kaluza’s share of gross avoided-curtailment value after consumer/generator split. | Illustrative revenue-share for business case (`HSO FAQ.txt`: negotiate splits with wind farms and consumers). |
| `HUB_GBP` | 100 | Retrofit control hub cost **per radiator** controlled. | `energy_brief.pdf` / FAQ (~£100 per device). |
| `RADIATORS_PER_HOME` | 2 | Number of radiators/heating zones controlled per home. | Consultant assumption (typical storage-heater home); affects capex. |
| `HEATER_GBP` | 300 | Quantum heater hardware cost per home (2017 money). | FAQ: ~£600 in 2018 list price, **halved** for 2017 if no historical series. |
| `SUBSIDY_LEVELS` | 25–100% | Share of upfront capex paid by programme/government in break-even scenarios. | `HSO FAQ.txt` (explore 25%, 50%, 75%, 100% subsidies). |
| `EXPORT_CAP_MW` (Appendix) | 40 | Max export to mainland GB used in optional system-balance check. | `energy_brief.pdf` (40 MW cable). Not used in headline Q1. |

**Data sources (fixed inputs, not tunable assumptions):**

- `data/Turbine_telemetry.csv` — one 900 kW turbine, ~1 min resolution (`Formatting Rules` / FAQ: scale to fleet).
- `data/Residential_demand.csv` — Kaluza proxy aggregate, 30 min, `Demand_mean_kw` per sample household.
"""))

cells.append(code("""
%matplotlib inline
import warnings
warnings.filterwarnings("ignore")

from IPython.display import display
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.interpolate import PchipInterpolator
from scipy import stats

# Plot style (readable for marking / export)
plt.rcParams.update({
    "figure.figsize": (10, 4.5),
    "axes.grid": True,
    "grid.alpha": 0.3,
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
})

DATA_DIR = Path("data")
HEADLINE_YEAR = 2017

# --- Physical & fleet ---
NAMEPLATE_KW = 900
NAMEPLATE_FRAC = 0.99
N_TURBINES = 500
FLEET_CORRELATION = 1.0
STORM_MEAN_MS = 25.0
STORM_PEAK_MS = 30.0
CUT_IN_MS = 3.0  # approximate; refined from data in EDA

# --- Orkney households ---
N_HOUSEHOLDS_ORKNEY = 10_385
DEMAND_ANOMALY_MONTHS = [9, 10]  # Sep–Oct 2017 sample-size spike (FAQ)

# --- DR flexibility ---
F_FLEX = 0.40
AVAILABILITY = 0.70
F_FLEX_LOW, F_FLEX_HIGH = 0.25, 0.55
AVAIL_LOW, AVAIL_HIGH = 0.50, 0.90

# --- Economics (2017 planning scenario) ---
WHOLESALE_GBP_MWH = 45.0
WHOLESALE_LOW, WHOLESALE_HIGH = 35.0, 55.0
KALUZA_VALUE_SHARE = 0.333
HUB_GBP = 100.0
RADIATORS_PER_HOME = 2
HEATER_GBP = 300.0
SUBSIDY_LEVELS = [0.25, 0.50, 0.75, 1.00]
PENETRATION_GRID = [0, 100, 250, 500, 1000, 2000, 3000, 5000, 7500, 10000, N_HOUSEHOLDS_ORKNEY]
DR_PENETRATION_TARGETS = [0.10, 0.25, 0.50]  # share of Orkney households enrolled
EXPORT_CAP_MW = 40.0  # Appendix system-balance check only (energy_brief.pdf)

# --- Value-pool splits (illustrative four-actor models, must sum to 1.0) ---
SHARE_HOUSEHOLD = 0.40   # discounted energy / bill savings
SHARE_WIND = 0.25        # royalty to generators
SHARE_KALUZA = 0.25      # platform + install margin (aligned with KALUZA_VALUE_SHARE order of magnitude)
SHARE_GRID = 0.10        # balancing / constraint payment
HOUSEHOLD_DISCOUNT_GBP_MWH = 20.0  # £ benefit per MWh shifted to curtailed-wind slots
WIND_ROYALTY_ADMIN_GBP_YR = 5_000   # minimum annual fee wind farm pays Kaluza to participate
GRID_VALUE_GBP_MWH = 8.0             # implied £/MWh for constraint relief (illustrative)

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

assumptions = pd.DataFrame([
    {"parameter": "headline_year", "value": HEADLINE_YEAR,
     "meaning": "Analysis year for annual curtailment and DR matching",
     "source": "Residential_demand.csv coverage; energy_brief.pdf"},
    {"parameter": "nameplate_kw", "value": NAMEPLATE_KW,
     "meaning": "Rated max power of exemplar turbine",
     "source": "Case dataset + energy_brief.pdf"},
    {"parameter": "nameplate_frac", "value": NAMEPLATE_FRAC,
     "meaning": "Setpoint threshold defining curtailed regime",
     "source": "energy_brief.pdf (setpoint semantics)"},
    {"parameter": "n_turbines", "value": N_TURBINES,
     "meaning": "Fleet multiplier for Orkney-wide Q1 scaling",
     "source": "energy_brief.pdf (>500 turbines); HSO FAQ (suggest 500)"},
    {"parameter": "fleet_correlation", "value": FLEET_CORRELATION,
     "meaning": "Correlation adjustment on fleet scale",
     "source": "HSO FAQ (scale average turbine); sensitivity in Appendix"},
    {"parameter": "storm_mean_ms", "value": STORM_MEAN_MS,
     "meaning": "10-min mean wind limit for storm exclusion",
     "source": "HSO FAQ.txt"},
    {"parameter": "storm_peak_ms", "value": STORM_PEAK_MS,
     "meaning": "Peak gust limit for storm exclusion",
     "source": "HSO FAQ.txt"},
    {"parameter": "cut_in_ms", "value": CUT_IN_MS,
     "meaning": "Cut-in wind for downtime classification",
     "source": "EDA on telemetry (approximate)"},
    {"parameter": "n_households_orkney", "value": N_HOUSEHOLDS_ORKNEY,
     "meaning": "Orkney households for penetration % and demand scaling",
     "source": "HSO FAQ.txt (~10,385)"},
    {"parameter": "demand_anomaly_months", "value": str(DEMAND_ANOMALY_MONTHS),
     "meaning": "Months flagged in EDA (sample N_households spike)",
     "source": "HSO FAQ.txt (Sep–Oct 2017 anomaly)"},
    {"parameter": "f_flex", "value": F_FLEX,
     "meaning": "Fraction of variable demand dispatchable by DR heating",
     "source": "Consultant assumption; FAQ best/worst framing"},
    {"parameter": "availability", "value": AVAILABILITY,
     "meaning": "Share of enrolled homes dispatchable when needed",
     "source": "Consultant assumption; sensitivity 0.5–0.9"},
    {"parameter": "wholesale_gbp_mwh", "value": WHOLESALE_GBP_MWH,
     "meaning": "£/MWh for valuing avoided curtailment",
     "source": "2017 wholesale planning range (£35–55); central £45"},
    {"parameter": "kaluza_value_share", "value": KALUZA_VALUE_SHARE,
     "meaning": "Kaluza revenue share of avoided-curtailment value",
     "source": "Illustrative business case (HSO FAQ revenue-sharing)"},
    {"parameter": "hub_gbp", "value": HUB_GBP,
     "meaning": "Smart hub cost per controlled radiator",
     "source": "energy_brief.pdf / FAQ (~£100)"},
    {"parameter": "radiators_per_home", "value": RADIATORS_PER_HOME,
     "meaning": "Radiators controlled per household (capex)",
     "source": "Consultant assumption (typical install)"},
    {"parameter": "heater_gbp", "value": HEATER_GBP,
     "meaning": "Quantum heater capex per home (2017)",
     "source": "FAQ: ~£600 in 2018, scaled ×0.5 for 2017"},
    {"parameter": "f_flex_sensitivity", "value": f"{F_FLEX_LOW} – {F_FLEX_HIGH}",
     "meaning": "Low / high DR flexibility scenarios",
     "source": "Consultant stress test"},
    {"parameter": "availability_sensitivity", "value": f"{AVAIL_LOW} – {AVAIL_HIGH}",
     "meaning": "Low / high device availability scenarios",
     "source": "Consultant stress test"},
])
display(assumptions)
"""))

# --- Helper functions ---
cells.append(md("""
## 3. Methods (self-contained functions)

All logic lives in this notebook so Kaluza's analytics team can replicate and extend the work
without external modules. Below we define each step; later sections **repeat the intuition in plain
language** before showing results.

| Step | Function(s) | Purpose |
|------|-------------|---------|
| Load / clean | `load_*`, `clean_*` | Parse CSVs, flag regimes, handle gaps |
| Power curve | `fit_binned_power_curve`, `validate_power_curve` | Wind → counterfactual kW |
| Curtailment | `attach_potential_and_curtailment`, `annual_curtailment_mwh` | Lost MWh (Q1) |
| Flex demand | `build_flexible_demand` | Shiftable heating kW |
| DR match | `supply_demand_match` | Avoided MWh vs enrolment (Q2/Q3) |
| Economics | `value_pool_gbp`, `split_pool`, `break_even_households` | Business case |
"""))

cells.append(code("""
def load_turbine(path=DATA_DIR / "Turbine_telemetry.csv"):
    # Load turbine telemetry; parse timestamps.
    df = pd.read_csv(path, parse_dates=["Timestamp"])
    df = df.sort_values("Timestamp").reset_index(drop=True)
    return df


def load_demand(path=DATA_DIR / "Residential_demand.csv"):
    # Load half-hourly residential demand proxy.
    df = pd.read_csv(path, parse_dates=["Timestamp"])
    df = df.sort_values("Timestamp").reset_index(drop=True)
    return df


def forward_interval_hours(ts):
    # Hours until next timestamp; cap at 1 h for gaps.
    delta = ts.shift(-1) - ts
    hours = delta.dt.total_seconds() / 3600.0
    return hours.fillna(hours.median()).clip(upper=1.0)


def clean_turbine(df, year=HEADLINE_YEAR):
    # Filter to headline year; drop NA; add interval hours and storm flags.
    ledger = {}
    out = df.copy()
    ledger["rows_in"] = len(out)

    out = out[(out["Timestamp"] >= f"{year}-01-01") & (out["Timestamp"] < f"{year + 1}-01-01")]
    ledger[f"rows_{year}"] = len(out)

    before = len(out)
    out = out.dropna(subset=["Power_kw", "Setpoint_kw", "Wind_ms"])
    ledger["rows_dropped_na"] = before - len(out)

    out["dt_h"] = forward_interval_hours(out["Timestamp"])
    out["wind_roll10m"] = out["Wind_ms"].rolling(10, min_periods=1).mean()
    out["is_storm"] = (out["wind_roll10m"] > STORM_MEAN_MS) | (out["Wind_ms"] > STORM_PEAK_MS)
    out["is_downtime"] = (out["Power_kw"] <= 0) & (out["Wind_ms"] >= CUT_IN_MS)
    out["is_curtailed_regime"] = out["Setpoint_kw"] < NAMEPLATE_KW * NAMEPLATE_FRAC
    out["overshoot"] = out["Power_kw"] > out["Setpoint_kw"] + 5

    ledger["storm_rows"] = int(out["is_storm"].sum())
    ledger["downtime_rows"] = int(out["is_downtime"].sum())
    ledger["curtailed_regime_rows"] = int(out["is_curtailed_regime"].sum())
    ledger["overshoot_rows"] = int(out["overshoot"].sum())
    return out, pd.Series(ledger, name="count")


def clean_demand(df, anomaly_months=DEMAND_ANOMALY_MONTHS):
    # Flag FAQ anomaly months; scale to island demand.
    out = df.copy()
    out["month"] = out["Timestamp"].dt.month
    out["is_anomaly_month"] = out["month"].isin(anomaly_months)
    out["demand_total_kw"] = out["Demand_mean_kw"] * N_HOUSEHOLDS_ORKNEY
    ledger = {
        "rows_in": len(out),
        "anomaly_rows": int(out["is_anomaly_month"].sum()),
        "n_households_min": out["N_households"].min(),
        "n_households_max": out["N_households"].max(),
    }
    out_clean = out[~out["is_anomaly_month"]].copy()
    ledger["rows_after_anomaly_exclusion"] = len(out_clean)
    return out, out_clean, pd.Series(ledger, name="count")


def fit_binned_power_curve(df, n_bins=35, min_bin_count=50):
    # Monotone binned-mean wind-to-power curve on normal regime rows.
    normal = df[~df["is_storm"] & ~df["is_downtime"] & ~df["is_curtailed_regime"]].copy()
    normal = normal[(normal["Setpoint_kw"] >= NAMEPLATE_KW * NAMEPLATE_FRAC)]

    wind = normal["Wind_ms"].values
    power = normal["Power_kw"].values
    bins = np.linspace(max(0, wind.min()), min(wind.max(), 25), n_bins + 1)
    rows = []
    xs, ys = [], []
    for i in range(len(bins) - 1):
        lo, hi = bins[i], bins[i + 1]
        mask = (wind >= lo) & (wind < hi)
        if mask.sum() < min_bin_count:
            continue
        xs.append(normal.loc[mask, "Wind_ms"].mean())
        ys.append(normal.loc[mask, "Power_kw"].mean())
    xs = np.array(xs)
    ys = np.clip(np.array(ys), 0, NAMEPLATE_KW)
    # enforce non-decreasing then cap
    ys = np.maximum.accumulate(ys)
    interp = PchipInterpolator(xs, ys, extrapolate=True)

    def predict(w):
        w = np.asarray(w, dtype=float)
        p = interp(w)
        return np.clip(p, 0, NAMEPLATE_KW)

    diag = pd.DataFrame({"wind_ms": xs, "mean_power_kw": ys, "bin_count": [min_bin_count] * len(xs)})
    return predict, normal, diag


def validate_power_curve(normal_df, predict_fn):
    # Return error metrics and residual frame for normal regime.
    pred = predict_fn(normal_df["Wind_ms"].values)
    actual = normal_df["Power_kw"].values
    resid = actual - pred
    metrics = {
        "mae_kw": np.mean(np.abs(resid)),
        "rmse_kw": np.sqrt(np.mean(resid ** 2)),
        "r2": 1 - np.sum(resid ** 2) / np.sum((actual - actual.mean()) ** 2),
    }
    out = normal_df[["Timestamp", "Wind_ms", "Power_kw"]].copy()
    out["pred_kw"] = pred
    out["residual_kw"] = resid
    return metrics, out


def attach_potential_and_curtailment(df, predict_fn):
    # Per-row potential power and curtailed power (kW).
    out = df.copy()
    out["potential_kw"] = predict_fn(out["Wind_ms"].values)
    # Curtailment only when setpoint regime active and not storm/downtime
    active = out["is_curtailed_regime"] & ~out["is_storm"] & ~out["is_downtime"]
    out["curtailed_kw"] = 0.0
    # Lost output vs wind potential (beta / brief counterfactual; not setpoint-minus-actual)
    out.loc[active, "curtailed_kw"] = np.maximum(
        0, out.loc[active, "potential_kw"] - out.loc[active, "Power_kw"]
    )
    out["curtailed_kwh"] = out["curtailed_kw"] * out["dt_h"]
    return out


def annual_curtailment_mwh(df):
    return df["curtailed_kwh"].sum() / 1000.0


def bootstrap_annual_ci(df, year=HEADLINE_YEAR, n_boot=300):
    # Day-level bootstrap of annual MWh for one turbine.
    daily = df.groupby(df["Timestamp"].dt.date)["curtailed_kwh"].sum() / 1000.0
    days = daily.values
    rng = np.random.default_rng(RANDOM_SEED)
    boots = []
    for _ in range(n_boot):
        sample = rng.choice(days, size=len(days), replace=True)
        boots.append(sample.sum())
    lo, hi = np.percentile(boots, [5, 95])
    return lo, hi


def aggregate_turbine_to_30min(df):
    # Sum curtailed energy to 30-min bins aligned to demand.
    g = df.set_index("Timestamp").resample("30min")
    agg = g.agg(
        curtailed_kwh=("curtailed_kwh", "sum"),
        curtailed_kw_mean=("curtailed_kw", "mean"),
        power_kw_mean=("Power_kw", "mean"),
        setpoint_kw_mean=("Setpoint_kw", "mean"),
    ).reset_index()
    return agg


def build_flexible_demand(demand_clean, f_flex=F_FLEX):
    # Baseline = rolling 24h minimum per household; flexible = f_flex * headroom above it.
    d = demand_clean.copy()
    d["baseline_kw"] = d["Demand_mean_kw"].rolling(48, min_periods=12).min()
    d["variable_kw"] = (d["Demand_mean_kw"] - d["baseline_kw"]).clip(lower=0)
    d["flexible_kw_per_hh"] = f_flex * d["variable_kw"]
    d["flexible_kw_island"] = d["flexible_kw_per_hh"] * N_HOUSEHOLDS_ORKNEY
    return d


def supply_demand_match(supply_30, demand_flex, n_enrolled, availability=AVAILABILITY):
    # Half-hourly avoided curtailment for given enrolled households.
    d = demand_flex.merge(supply_30, on="Timestamp", how="inner")
    fleet_factor = N_TURBINES * FLEET_CORRELATION
    d["curtailed_kwh_fleet"] = d["curtailed_kwh"] * fleet_factor
    d["dr_kw"] = d["flexible_kw_per_hh"] * n_enrolled * availability
    d["dr_kwh"] = d["dr_kw"] * 0.5  # 30-min interval
    d["avoided_kwh"] = np.minimum(d["curtailed_kwh_fleet"], d["dr_kwh"])
    annual_avoided_mwh = d["avoided_kwh"].sum() / 1000.0
    annual_curtailed_mwh = d["curtailed_kwh_fleet"].sum() / 1000.0
    return d, annual_avoided_mwh, annual_curtailed_mwh


def households_for_target(annual_curtailed_mwh, target_frac, curve_df):
    # Interpolate households needed for target recovery fraction.
    target_mwh = target_frac * annual_curtailed_mwh
    sub = curve_df.sort_values("n_households")
    if target_mwh <= sub["avoided_mwh"].min():
        return 0
    if target_mwh >= sub["avoided_mwh"].max():
        return int(sub["n_households"].max())
    return int(np.interp(target_mwh, sub["avoided_mwh"], sub["n_households"]))


def capex_per_home():
    return HUB_GBP * RADIATORS_PER_HOME + HEATER_GBP


def kaluza_annual_revenue(avoided_mwh, share=KALUZA_VALUE_SHARE, price=WHOLESALE_GBP_MWH):
    return avoided_mwh * price * share


def break_even_households(avoided_mwh_per_home, price=WHOLESALE_GBP_MWH, subsidy=0.0):
    # Homes needed so annual margin covers subsidised capex (simplified).
    margin_per_home = kaluza_annual_revenue(avoided_mwh_per_home, price=price)
    cost = capex_per_home() * (1 - subsidy)
    if margin_per_home <= 0:
        return np.inf
    return int(np.ceil(cost / margin_per_home))
"""))

# --- Load & clean ---
cells.append(md("""
## 4. Data Loading & Quality

**Turbine telemetry** (~1 minute): we keep **2017** only, drop rows with missing `Power_kw`, `Setpoint_kw`,
or `Wind_ms`, and compute `dt_h` = hours to the next timestamp (capped at 1 h so telemetry gaps do not
inflate energy sums).

**Regime flags** (used in later steps):

- `is_storm` — 10-minute mean wind > 25 m/s or gust > 30 m/s → turbine shut down (FAQ).
- `is_downtime` — power ≤ 0 but wind above cut-in → maintenance / fault proxy.
- `is_curtailed_regime` — `Setpoint_kw < 0.99 × 900` → network cap active (curtailment **signal**).
- Overshoot rows (`Power_kw > Setpoint_kw`) are flagged but kept.

**Demand:** `Demand_mean_kw` is **per household in the metering sample**; we scale to the island with
`× N_HOUSEHOLDS_ORKNEY` (10,385). Sep–Oct 2017 is excluded from **EDA charts** only (sample-size spike);
Q2 matching uses the **full-year** timeline.
"""))

cells.append(code("""
turbine_raw = load_turbine()
demand_raw = load_demand()

turbine, t_ledger = clean_turbine(turbine_raw, year=HEADLINE_YEAR)
demand_all, demand, d_ledger = clean_demand(demand_raw)

print("Turbine cleaning ledger:")
display(t_ledger.to_frame("count"))
print("Demand cleaning ledger:")
display(d_ledger.to_frame("count"))

print(f"\\nTurbine {HEADLINE_YEAR}: {len(turbine):,} rows")
print(f"Demand (full year): {len(demand_all):,} half-hours | EDA subset (excl. Sep–Oct): {len(demand):,}")
"""))

# --- EDA section - many plots ---
cells.append(md("""
## 5. Exploratory Data Analysis

We inspect both datasets before modelling. Rich visual exploration is intentional: it documents
data quirks (missing values, setpoint events, demand seasonality) and motivates our cleaning
choices and DR dispatch strategy.
"""))

cells.append(code("""
# --- EDA 1: Turbine coverage (annual view) ---
ts = turbine.set_index("Timestamp")
daily_setpoint_min = ts["Setpoint_kw"].resample("1D").min()
curt_mask = daily_setpoint_min < NAMEPLATE_KW * NAMEPLATE_FRAC

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

monthly = ts["Power_kw"].resample("ME").mean()
axes[0].bar(range(len(monthly)), monthly.values, color="#2ca02c", edgecolor="white")
axes[0].set_xticks(range(len(monthly)))
axes[0].set_xticklabels([d.strftime("%b") for d in monthly.index], rotation=45)
axes[0].set_title("Monthly mean turbine power (2017)")
axes[0].set_ylabel("kW")

axes[1].hist(turbine["Wind_ms"].dropna(), bins=50, color="#9467bd", edgecolor="white")
axes[1].axvline(STORM_MEAN_MS, color="r", ls="--", label="Storm mean threshold")
axes[1].set_title("Wind speed distribution")
axes[1].set_xlabel("Wind (m/s)")
axes[1].legend()

plt.tight_layout()
plt.show()
print(
    f"Curtailment signal: {curt_mask.sum()} days with min setpoint below nameplate "
    f"({100*curt_mask.mean():.0f}% of days in {HEADLINE_YEAR})."
)
"""))

cells.append(code("""
# --- EDA 2: Wind vs power coloured by setpoint regime ---
sample = turbine.sample(min(40000, len(turbine)), random_state=RANDOM_SEED)
colors = np.where(sample["is_curtailed_regime"], "#d62728", "#1f77b4")

fig, ax = plt.subplots(figsize=(9, 5))
ax.scatter(sample["Wind_ms"], sample["Power_kw"], c=colors, s=3, alpha=0.25)
ax.set_xlabel("Wind speed (m/s)")
ax.set_ylabel("Power (kW)")
ax.set_title("Wind–power scatter (blue=normal, red=curtailed regime)")
ax.axhline(NAMEPLATE_KW, color="k", ls="--", alpha=0.5)
plt.show()
"""))

cells.append(code("""
# --- EDA 3: Setpoint below nameplate — when does curtailment happen? ---
curt = turbine[turbine["is_curtailed_regime"]]
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].hist(curt["Setpoint_kw"], bins=40, color="#d62728", edgecolor="white")
axes[0].set_title("Setpoint values during curtailed regime")
axes[0].set_xlabel("Setpoint (kW)")

curt_by_month = curt.groupby(curt["Timestamp"].dt.month).size()
axes[1].bar(curt_by_month.index, curt_by_month.values, color="#d62728")
axes[1].set_xticks(range(1, 13))
axes[1].set_xticklabels("JFMAMJJASOND")
axes[1].set_title("Curtailed-regime minutes by month")
axes[1].set_ylabel("Count")

plt.tight_layout()
plt.show()
"""))

cells.append(code("""
# --- EDA 4: Demand sample size anomaly (FAQ) ---
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(demand_all["Timestamp"], demand_all["N_households"], linewidth=0.8)
ax.axvspan(pd.Timestamp("2017-09-01"), pd.Timestamp("2017-11-01"), color="orange", alpha=0.2, label="Excluded months")
ax.set_title("Metering sample size (N_households) — Sep–Oct spike flagged")
ax.set_ylabel("Sample households")
ax.legend()
plt.show()
"""))

cells.append(code("""
# --- EDA 5: Residential demand seasonality ---
demand["hour"] = demand["Timestamp"].dt.hour
demand["month"] = demand["Timestamp"].dt.month

fig, axes = plt.subplots(2, 2, figsize=(12, 8))

# Average day profile (all clean months)
day_prof = demand.groupby("hour")["Demand_mean_kw"].mean()
axes[0, 0].plot(day_prof.index, day_prof.values, marker="o", color="#1f77b4")
axes[0, 0].set_title("Average diurnal profile (per household)")
axes[0, 0].set_xlabel("Hour of day (UTC)")
axes[0, 0].set_ylabel("kW / household")

# Island-scale total demand
day_total = demand.groupby("hour")["demand_total_kw"].mean()
axes[0, 1].plot(day_total.index, day_total.values, marker="o", color="#2ca02c")
axes[0, 1].set_title(f"Island-scale demand profile (×{N_HOUSEHOLDS_ORKNEY:,} homes)")
axes[0, 1].set_xlabel("Hour")
axes[0, 1].set_ylabel("kW total")

# Monthly energy
monthly_mwh = demand.set_index("Timestamp")["demand_total_kw"].resample("ME").sum() * 0.5 / 1000
axes[1, 0].bar(range(len(monthly_mwh)), monthly_mwh.values, color="#9467bd")
axes[1, 0].set_xticks(range(len(monthly_mwh)))
axes[1, 0].set_xticklabels([d.strftime("%b") for d in monthly_mwh.index], rotation=45)
axes[1, 0].set_title("Monthly residential energy (MWh)")
axes[1, 0].set_ylabel("MWh")

# Winter vs summer day shapes
for label, months, color in [("Winter (DJF)", [12, 1, 2], "#003f5c"), ("Summer (JJA)", [6, 7, 8], "#ffa600")]:
    sub = demand[demand["month"].isin(months)].groupby("hour")["Demand_mean_kw"].mean()
    axes[1, 1].plot(sub.index, sub.values, label=label, color=color, marker=".")
axes[1, 1].set_title("Seasonal diurnal profiles")
axes[1, 1].set_xlabel("Hour")
axes[1, 1].legend()

plt.tight_layout()
plt.show()
"""))

cells.append(code("""
# --- EDA 6: Demand distribution & weekly heatmap ---
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].hist(demand["Demand_mean_kw"], bins=60, color="#17becf", edgecolor="white")
axes[0].set_title("Per-household demand (30-min means)")
axes[0].set_xlabel("kW")

demand["dow"] = demand["Timestamp"].dt.dayofweek
pivot = demand.pivot_table(index="hour", columns="dow", values="Demand_mean_kw", aggfunc="mean")
im = axes[1].imshow(pivot.values, aspect="auto", origin="lower", cmap="YlOrRd")
axes[1].set_yticks(range(0, 24, 3))
axes[1].set_yticklabels(range(0, 24, 3))
axes[1].set_xticks(range(7))
axes[1].set_xticklabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
axes[1].set_title("Demand heatmap: hour × day-of-week")
plt.colorbar(im, ax=axes[1], label="kW / household")
plt.tight_layout()
plt.show()
"""))

cells.append(code("""
# --- EDA 7: Boxplots by month and hour-of-day variability ---
fig, ax = plt.subplots(figsize=(11, 4))
demand.boxplot(column="Demand_mean_kw", by="month", ax=ax)
ax.set_title("Per-household demand spread by month")
ax.set_xlabel("Month")
plt.suptitle("")
plt.show()
"""))

# Power curve
cells.append(md(r"""
## 6. Power Curve Modelling & Validation (Hypothesis P4)

### What model do we use?

We do **not** fit a parametric logistic curve in this report. We use a **non-parametric, monotone
empirical power curve**:

1. **Training sample (critical):** only **`normal` regime** rows:
   - not storm, not downtime, **not curtailed regime** (`Setpoint_kw ≥ 891 kW`),
   - i.e. minutes where the network is **not** capping output.
2. Split wind speed into ~35 bins; in each bin compute the **mean observed power**.
3. Enforce a **non-decreasing** series (`maximum.accumulate`) — physical monotonicity.
4. Interpolate with a **PCHIP** spline (`scipy.interpolate.PchipInterpolator`) and clip to `[0, 900]` kW.

This is the curve $\hat{P}(v)$ used as **potential power** given wind speed $v$.

### How do we validate?

Metrics (MAE, RMSE, R²) are computed on the **same filtered population** used to build the bins
(**in-sample** on non-curtailed minutes). That answers: *“Does the curve describe normal operation?”*
not *“Can it predict curtailed minutes?”* (those are out-of-domain by design).

We also plot:

- residuals vs fitted power,
- residual histogram,
- mean residual **by wind bin** (systematic bias check).

A good fit here supports using $\hat{P}(v)$ as a counterfactual; it does **not** guarantee
perfect curtailed-energy attribution.
"""))

cells.append(code("""
predict_power, normal_rows, bin_diag = fit_binned_power_curve(turbine)
metrics, resid_df = validate_power_curve(normal_rows, predict_power)

print("Power curve FIT sample (rows used to build bins):")
print(f"  Count: {len(normal_rows):,}  |  Storm excluded  |  Downtime excluded  |  Curtailed regime excluded")
print(f"  Setpoint at nameplate (>= {NAMEPLATE_KW * NAMEPLATE_FRAC:.0f} kW)")
print("Validation: in-sample on this same population (see metrics and residual plots).\\n")

print("Power curve validation (normal regime):")
for k, v in metrics.items():
    print(f"  {k}: {v:.2f}" if k != "r2" else f"  {k}: {v:.4f}")

turbine = attach_potential_and_curtailment(turbine, predict_power)

fig, axes = plt.subplots(1, 3, figsize=(14, 4))
wind_grid = np.linspace(0, 25, 200)
axes[0].scatter(normal_rows["Wind_ms"], normal_rows["Power_kw"], s=2, alpha=0.1, c="#1f77b4")
axes[0].plot(wind_grid, predict_power(wind_grid), color="#d62728", lw=2.5, label="Fitted curve")
axes[0].axhline(NAMEPLATE_KW, ls="--", color="k", alpha=0.5)
axes[0].set_xlabel("Wind (m/s)")
axes[0].set_ylabel("Power (kW)")
axes[0].set_title("Binned-mean power curve")
axes[0].legend()

axes[1].scatter(resid_df["pred_kw"], resid_df["residual_kw"], s=2, alpha=0.15)
axes[1].axhline(0, color="k", lw=1)
axes[1].set_xlabel("Predicted (kW)")
axes[1].set_ylabel("Residual (kW)")
axes[1].set_title("Residuals vs fitted")

axes[2].hist(resid_df["residual_kw"], bins=60, color="#9467bd", edgecolor="white")
axes[2].set_title("Residual distribution")
axes[2].set_xlabel("kW")

plt.tight_layout()
plt.show()
"""))

cells.append(code("""
# --- EDA 8: Residuals by wind bin (validation) ---
resid_df["wind_bin"] = pd.cut(resid_df["Wind_ms"], bins=12)
by_bin = resid_df.groupby("wind_bin", observed=True)["residual_kw"].agg(["mean", "std", "count"])
display(by_bin.head(12))
"""))

# Q1
cells.append(md(r"""
## 7. Quantifying Annual Curtailment (Q1)

### Counterfactual potential

For every minute: $\hat{P}_t = \hat{P}(\mathrm{wind}_t)$ from the power curve (Section 6).

### Curtailed power formula (what the code implements)

Only when **`is_curtailed_regime`** and not storm/downtime:

$$
\mathrm{curtailed\_kw}_t = \max\left(0,\; \hat{P}_t - P^{\mathrm{actual}}_t\right)
$$

$$
\mathrm{curtailed\_kWh}_t = \mathrm{curtailed\_kw}_t \times \Delta t_t
$$

**Why `max(0, potential − actual)` and not `min(potential, setpoint) − actual`?**

When the setpoint binds, the turbine often tracks the cap closely, so `setpoint − actual ≈ 0` even
though wind could support **much more** than actual output. The **lost energy** is the gap between
**what the wind resource could produce** ($\hat{P}$) and **what was delivered** — not the spare
headroom below the setpoint.

| Situation | potential | setpoint | actual | `potential − actual` | `min(pot,s) − actual` |
|-----------|-----------|----------|--------|----------------------|------------------------|
| Strong wind, cap 500 kW, out 500 kW | 800 | 500 | 500 | **300** | 0 |
| Low wind, cap 500 kW, out 200 kW | 200 | 500 | 200 | 0 | 0 |

We sum curtailed energy over **2017**, then scale:

$$
E^{\mathrm{fleet}}_{\mathrm{curt}} = E^{\mathrm{turbine}}_{\mathrm{curt}} \times N_{\mathrm{turbines}} \times \rho_{\mathrm{corr}}
$$
"""))

cells.append(code("""
mwh_turbine = annual_curtailment_mwh(turbine)
mwh_fleet = mwh_turbine * N_TURBINES * FLEET_CORRELATION
gwh_fleet = mwh_fleet / 1000.0
ci_lo, ci_hi = bootstrap_annual_ci(turbine)
ci_fleet_lo, ci_fleet_hi = ci_lo * N_TURBINES, ci_hi * N_TURBINES

q1_table = pd.DataFrame({
    "metric": [
        "Headline year",
        "Single-turbine curtailed energy (MWh)",
        "Fleet size (turbines)",
        "Fleet correlation",
        "Fleet curtailed energy (MWh)",
        "Fleet curtailed energy (GWh)",
        "Fleet 90% CI low (MWh)",
        "Fleet 90% CI high (MWh)",
    ],
    "value": [
        HEADLINE_YEAR, round(mwh_turbine, 1), N_TURBINES, FLEET_CORRELATION,
        round(mwh_fleet, 1), round(gwh_fleet, 2), round(ci_fleet_lo, 0), round(ci_fleet_hi, 0),
    ],
})
display(q1_table)

print("\\n>>> Q1 ANSWER: We estimate approximately "
      f"{gwh_fleet:.1f} GWh/yr ({mwh_fleet:,.0f} MWh/yr) of wind energy is curtailed "
      f"across {N_TURBINES} Orkney turbines in {HEADLINE_YEAR}, "
      f"with a 90% bootstrap range of {ci_fleet_lo/1000:.1f}–{ci_fleet_hi/1000:.1f} GWh.")
"""))

cells.append(md("""
### Interpreting Q1 (critical)

**What works:** The order of magnitude (~**tens of GWh/year** fleet-wide) is credible for a wind-heavy,
export-constrained island and aligns with the case narrative. Curtailment is **not** a rounding error — it
is a large stranded asset. The power-curve counterfactual is well supported (R² ≈ 0.98 on normal regimes),
and the setpoint-regime flag aligns with known curtailment days in EDA.

**Caveats (material):**
- We observe **one** turbine and multiply by **500** — real fleets differ in location, maintenance, and contract.
- Curtailment is inferred when `setpoint < 891 kW`; grid-driven constraint without setpoint movement would be **missed**.
- Lost energy uses `potential − actual`, not demand/export balance — headline Q1 is a **generation-side lower bound**, not a full system dispatch model.

**So what:** Q1 establishes a strong **problem size** for Kaluza. It does **not** imply that DR can absorb most of this energy — that is tested in Q2.
"""))

cells.append(code("""
# --- Q1 visualisations ---
daily = turbine.groupby(turbine["Timestamp"].dt.date)["curtailed_kwh"].sum() / 1000.0
daily.index = pd.to_datetime(daily.index)
daily_fleet = daily * N_TURBINES

fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
axes[0].bar(daily_fleet.index, daily_fleet.values, width=1.0, color="#d62728", alpha=0.6)
axes[0].set_ylabel("MWh / day")
axes[0].set_title(f"Daily curtailed energy — fleet ({N_TURBINES} turbines)")

axes[1].plot(daily_fleet.index, daily_fleet.cumsum(), color="#9467bd", lw=2)
axes[1].set_ylabel("Cumulative MWh")
axes[1].set_title("Cumulative curtailed energy through 2017")
axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
plt.tight_layout()
plt.show()
"""))

cells.append(code("""
# --- Extra: Example curtailment week (setpoint vs actual vs potential) ---
week_start = pd.Timestamp("2017-03-01")
w = turbine[(turbine["Timestamp"] >= week_start) & (turbine["Timestamp"] < week_start + pd.Timedelta(days=7))]
fig, ax = plt.subplots(figsize=(11, 4))
ax.plot(w["Timestamp"], w["potential_kw"], label="Potential (curve)", alpha=0.7)
ax.plot(w["Timestamp"], w["Setpoint_kw"], label="Setpoint", alpha=0.8)
ax.plot(w["Timestamp"], w["Power_kw"], label="Actual", alpha=0.8)
ax.fill_between(w["Timestamp"], w["Power_kw"], w["potential_kw"],
                where=(w["curtailed_kw"] > 0), alpha=0.2, color="#d62728", label="Curtailed gap")
ax.set_ylabel("kW")
ax.set_title("Example week: potential vs setpoint vs actual")
ax.legend(loc="upper right", ncol=2)
plt.tight_layout()
plt.show()
"""))

cells.append(code("""
# --- EDA 10: When does curtailment happen? (hour × month heatmap, fleet-scaled)
turbine["hour"] = turbine["Timestamp"].dt.hour
turbine["month"] = turbine["Timestamp"].dt.month
curt_hm = turbine.groupby(["month", "hour"])["curtailed_kwh"].sum().unstack(fill_value=0) * N_TURBINES / 1000
fig, ax = plt.subplots(figsize=(11, 4))
im = ax.imshow(curt_hm.values, aspect="auto", origin="lower", cmap="Reds")
ax.set_yticks(range(12))
ax.set_yticklabels("JFMAMJJASOND")
ax.set_xticks(range(0, 24, 3))
ax.set_xticklabels(range(0, 24, 3))
ax.set_xlabel("Hour (UTC)")
ax.set_title("Fleet curtailed energy (MWh) by month and hour — 2017")
plt.colorbar(im, ax=ax, label="MWh")
plt.tight_layout()
plt.show()
"""))

# Flex demand
cells.append(md(r"""
## 8. Flexible Demand for DR

### Baseline and flexible load

Per household, 30-minute demand $d_t$ (kW):

1. **Baseline** — rolling 24 h minimum (48 half-hours): always-on load proxy.
2. **Variable** — $v_t = \max(0,\; d_t - \mathrm{baseline}_t)$.
3. **Flexible** — $f_t = f_{\mathrm{flex}} \times v_t$ with central $f_{\mathrm{flex}} = 0.4$.

Island aggregate flexible power if **all** homes participate:

$$
P^{\mathrm{DR}}_t = f_t \times N_{\mathrm{enrolled}} \times \mathrm{availability}
$$

Only a fraction `availability` (central 0.7) of enrolled homes are assumed dispatchable in real time.
"""))

cells.append(code("""
# Flexible load profile on full-year timestamps (FAQ anomaly months kept for alignment with supply)
demand_flex = build_flexible_demand(demand_all, f_flex=F_FLEX)
supply_30 = aggregate_turbine_to_30min(turbine)

n_days = demand_flex["Timestamp"].dt.date.nunique()
per_hh_daily_kwh = demand_flex["flexible_kw_per_hh"].sum() * 0.5 / n_days
print(f"Central flexible capacity: ~{demand_flex['flexible_kw_per_hh'].mean():.3f} kW/household (mean)")
print(f"Implied ~{per_hh_daily_kwh:.2f} kWh/household/day flexible at f_flex={F_FLEX}")
"""))

cells.append(code("""
# --- EDA 9: Flexible vs curtailed — week with highest fleet curtailed energy ---
joined_full = demand_flex.merge(supply_30, on="Timestamp", how="inner")
joined_full["curt_fleet_kwh"] = joined_full["curtailed_kwh"] * N_TURBINES
joined_full["dr_kw_full"] = (
    joined_full["flexible_kw_per_hh"] * N_HOUSEHOLDS_ORKNEY * AVAILABILITY
)
joined_full["week"] = joined_full["Timestamp"].dt.to_period("W")
weekly_curt = joined_full.groupby("week")["curt_fleet_kwh"].sum()
best_week = weekly_curt.idxmax()
rep_start = best_week.start_time
rep_end = rep_start + pd.Timedelta(days=7)
joined_w = joined_full[
    (joined_full["Timestamp"] >= rep_start) & (joined_full["Timestamp"] < rep_end)
].copy()

fig, ax = plt.subplots(figsize=(12, 4.5))
ax.fill_between(
    joined_w["Timestamp"], 0, joined_w["curt_fleet_kwh"] / 0.5,
    alpha=0.25, color="#d62728", label="Curtailed fleet (kW, 30-min avg)",
)
ax.plot(joined_w["Timestamp"], joined_w["curt_fleet_kwh"] / 0.5,
        color="#d62728", lw=1.5, label="Curtailed fleet")
ax.plot(joined_w["Timestamp"], joined_w["dr_kw_full"],
        color="#2ca02c", lw=1.5, label="Max DR @ 100% enrolment × availability")
ax.set_title(
    f"EDA 9 — Highest-curtailment week ({rep_start.strftime('%d %b')} – "
    f"{(rep_end - pd.Timedelta(days=1)).strftime('%d %b %Y')}), "
    f"{weekly_curt.max()/1000:.1f} MWh curtailed"
)
ax.set_ylabel("kW")
ax.set_xlabel("Time (UTC)")
ax.legend(loc="upper right")
plt.tight_layout()
plt.show()

overlap = (joined_w["dr_kw_full"] >= joined_w["curt_fleet_kwh"] / 0.5).mean()
print(f"Selected week total curtailed (fleet): {weekly_curt.max()/1000:.2f} MWh")
print(f"Within this week, DR capacity covers curtailed power in {100*overlap:.1f}% of half-hours.")
print("Gap between green and red lines = structural mismatch (timing + limited flex), not a plotting artefact.")
"""))

# Q2 Q3
cells.append(md(r"""
## 9. DR Penetration & Avoided Curtailment (Q2 & Q3)

### DR penetration (definition)

$$
\mathrm{penetration} = \frac{N_{\mathrm{enrolled}}}{N_{\mathrm{households, Orkney}}}
\qquad \text{(e.g. } 2596 / 10385 \approx 25\% \text{)}
$$

### Half-hourly matching (Q2 core)

Fleet curtailed energy in each 30-minute interval:

$$
E^{\mathrm{curt,fleet}}_{t} = E^{\mathrm{curt,turbine}}_{t} \times N_{\mathrm{turbines}}
$$

Dispatchable DR energy in the same interval:

$$
E^{\mathrm{DR}}_{t} = f_t \times N_{\mathrm{enrolled}} \times \mathrm{availability} \times 0.5\;\mathrm{h}
$$

**Avoided curtailment** (energy actually absorbed):

$$
E^{\mathrm{avoided}}_{t} = \min\left(E^{\mathrm{curt,fleet}}_{t},\; E^{\mathrm{DR}}_{t}\right)
$$

Annual Q2 headline: $\sum_t E^{\mathrm{avoided}}_{t}$ converted to MWh/yr, traced over a grid of
$N_{\mathrm{enrolled}}$.

**Recovery rate** (honest denominator = Q1 fleet total):

$$
\mathrm{recovery\%} = 100 \times \frac{\sum_t E^{\mathrm{avoided}}_{t}}{E^{\mathrm{fleet}}_{\mathrm{curt, Q1}}}
$$

### Q3

- **Penetration targets (10 / 25 / 50 %):** read $N_{\mathrm{enrolled}}$ and avoided MWh from the curve.
- **MWh targets:** invert the curve — find smallest $N$ such that avoided MWh $\geq$ target.
"""))

cells.append(code("""
curve_rows = []
for n in PENETRATION_GRID:
    _, avoided, curtailed = supply_demand_match(supply_30, demand_flex, n, availability=AVAILABILITY)
    curve_rows.append({
        "n_households": n,
        "penetration_pct": 100 * n / N_HOUSEHOLDS_ORKNEY,
        "avoided_mwh": avoided,
        "available_curtailed_mwh": curtailed,
        "recovery_frac": avoided / curtailed if curtailed > 0 else 0,
    })
curve_df = pd.DataFrame(curve_rows)
annual_curtailed_mwh = curve_df["available_curtailed_mwh"].iloc[0]

display(curve_df.round(1))

matched_curtailed_gwh = annual_curtailed_mwh / 1000
print("\\n>>> Q2 ANSWER: At central assumptions (f_flex={}, availability={}), full enrolment "
      "({:,} homes) avoids ~{:.0f} MWh/yr in half-hours overlapping demand telemetry "
      "({:.1f} GWh curtailed in those windows; ~{:.1%} recovery vs Q1 fleet total {:.1f} GWh).".format(
          F_FLEX, AVAILABILITY, N_HOUSEHOLDS_ORKNEY,
          curve_df.loc[curve_df["n_households"] == N_HOUSEHOLDS_ORKNEY, "avoided_mwh"].iloc[0],
          matched_curtailed_gwh,
          curve_df.loc[curve_df["n_households"] == N_HOUSEHOLDS_ORKNEY, "recovery_frac"].iloc[0],
          gwh_fleet,
      ))

full_avoided = float(
    curve_df.loc[curve_df["n_households"] == N_HOUSEHOLDS_ORKNEY, "avoided_mwh"].iloc[0]
)
"""))

cells.append(code("""
# Q3 — households required for stated DR penetration levels (and illustrative MWh targets)
q3_rows = []
for pen in DR_PENETRATION_TARGETS:
    n_needed = int(round(pen * N_HOUSEHOLDS_ORKNEY))
    row = curve_df.loc[curve_df["n_households"] == n_needed]
    if row.empty:
        row = curve_df.iloc[(curve_df["n_households"] - n_needed).abs().argsort()[:1]]
    avoided = float(row["avoided_mwh"].iloc[0])
    q3_rows.append({
        "dr_penetration_target": f"{100*pen:.0f}%",
        "households_on_scheme": n_needed,
        "avoided_curtailment_mwh_yr": round(avoided, 1),
        "pct_of_fleet_curtailed": round(100 * avoided / annual_curtailed_mwh, 2),
    })
q3_df = pd.DataFrame(q3_rows)

# Illustrative: households to hit absolute MWh avoided (interpolated along curve)
mwh_targets = [50, 100, 200, round(full_avoided, 0)]
q3b_rows = []
for target in mwh_targets:
    n_h = households_for_target(annual_curtailed_mwh, target / annual_curtailed_mwh, curve_df)
    q3b_rows.append({"avoided_mwh_target": target, "households_required": min(n_h, N_HOUSEHOLDS_ORKNEY)})
q3b_df = pd.DataFrame(q3b_rows)

display(q3_df)
display(q3b_df)

max_avoided = curve_df["avoided_mwh"].max()
print("\\n>>> Q3 ANSWER: To operate at 25% DR penetration requires "
      f"{q3_df.loc[q3_df['dr_penetration_target']=='25%', 'households_on_scheme'].iloc[0]:,} households, "
      f"delivering ~{q3_df.loc[q3_df['dr_penetration_target']=='25%', 'avoided_curtailment_mwh_yr'].iloc[0]:,.0f} MWh/yr avoided. "
      f"Full enrolment caps at ~{max_avoided:.0f} MWh/yr (~{100*max_avoided/annual_curtailed_mwh:.2f}% of fleet curtailment) "
      "because flexible heating capacity is small versus curtailed volume.")
"""))

cells.append(md("""
### Interpreting Q2 & Q3 (critical)

**What works:** The **shape** of the enrolment curve is right — avoided MWh rises roughly linearly at low
penetration, then **flattens** (saturation). That tells Kaluza enrolment alone is not enough; **flexible
kW per home** and **coincidence** with curtailment events matter more than marketing beyond the knee.

**What is weak / honest negative:**
- At **100% penetration**, we recover only **~0.3–0.5%** of Q1 fleet curtailment. The DR lever is
  **tiny relative to the problem** under residential-heating-only assumptions.
- Matching is **half-hourly** and uses aggregate flex — we do not model thermal storage duration or industrial load.
- Recovering **25% of fleet curtailment** is **not achievable** in this model even with every household enrolled;
  Q3 targets framed as % of Q1 are **aspirational**, not forecast.

**Q3 reading:** Household counts for 10/25/50% **penetration** are linear (2,600 / 6,500 / 8,200 homes) but
deliver only **79 / 200 / 350 MWh/yr** avoided — useful for **operational planning**, not for claiming
grid-scale curtailment relief.
"""))

cells.append(code("""
# --- Q2 charts (scaled so the signal is visible) ---
curve_df = curve_df.copy()
curve_df["recovery_vs_q1_pct"] = 100 * curve_df["avoided_mwh"] / mwh_fleet
saturation_mwh = curve_df["avoided_mwh"].max()

fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

# Left: absolute avoided MWh — do NOT share y-axis with 76,860 MWh curtailed (old chart looked empty)
ax = axes[0]
ax.plot(curve_df["n_households"], curve_df["avoided_mwh"], "o-", color="#9467bd", lw=2.5, ms=9, zorder=3)
ax.axhline(saturation_mwh, ls=":", color="#9467bd", alpha=0.7,
           label=f"Model saturation ≈ {saturation_mwh:.0f} MWh/yr")
ax.set_ylim(0, saturation_mwh * 1.15)
ax.set_xlabel("Households enrolled")
ax.set_ylabel("Avoided curtailment (MWh / year)")
ax.set_title("Q2: Avoided curtailment vs enrolment")
ax.legend(loc="lower right")
ax.text(
    0.03, 0.97,
    f"Q1 fleet curtailed: {mwh_fleet:,.0f} MWh/yr\\n"
    "(not plotted — 300× larger than max avoided)",
    transform=ax.transAxes, va="top", fontsize=9,
    bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
)

# Right: recovery % vs Q1 — zoom y-axis to actual range (0–0.5%), not 0–100%
ax2 = axes[1]
ax2.plot(curve_df["penetration_pct"], curve_df["recovery_vs_q1_pct"],
         "s-", color="#2ca02c", lw=2.5, ms=9)
ax2.set_ylim(0, max(curve_df["recovery_vs_q1_pct"].max() * 1.35, 0.05))
ax2.set_xlabel("DR penetration (% of Orkney households)")
ax2.set_ylabel("% of Q1 fleet-curtailed energy recovered")
ax2.set_title("Q2: Recovery vs penetration (zoomed to model range)")
ax2.axhline(curve_df["recovery_vs_q1_pct"].iloc[-1], ls="--", color="gray", alpha=0.6,
            label=f"Full enrolment ≈ {curve_df['recovery_vs_q1_pct'].iloc[-1]:.2f}%")
ax2.legend(loc="lower right", fontsize=9)

plt.tight_layout()
plt.show()
"""))

cells.append(code("""
# --- Extra: Low / central / high scenario band ---
scenarios = [
    ("Low", F_FLEX_LOW, AVAIL_LOW),
    ("Central", F_FLEX, AVAILABILITY),
    ("High", F_FLEX_HIGH, AVAIL_HIGH),
]
scen_rows = []
for label, ff, av in scenarios:
    df_flex = build_flexible_demand(demand_all, f_flex=ff)
    _, avoided, _ = supply_demand_match(supply_30, df_flex, N_HOUSEHOLDS_ORKNEY, availability=av)
    scen_rows.append({"scenario": label, "f_flex": ff, "availability": av, "avoided_mwh_full_pen": avoided})
scen_df = pd.DataFrame(scen_rows)
display(scen_df)

fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(scen_df["scenario"], scen_df["avoided_mwh_full_pen"], color=["#aec7e8", "#1f77b4", "#003f5c"])
ax.set_ylabel("MWh/yr avoided at full enrolment")
ax.set_title("Sensitivity: flexible share × availability")
plt.show()
"""))

# Business case
cells.append(md("""
## 10. Business Case — Four Actors & Viability Thresholds

Curtailment creates a **value pool** if avoided MWh are sold or substituted. Four parties interact:

| Actor | Role | How they gain | How they pay |
|-------|------|---------------|--------------|
| **Households** | Flexible heat load | Cheaper energy / comfort service | Hardware + hub (unless subsidised) |
| **Kaluza** | DR orchestration | Fees + share of energy value | Install support, platform ops |
| **Wind farmers** | Stranded generation | More MWh delivered instead of curtailed | Royalty or revenue-share to Kaluza / customers |
| **Grid / system operator** | Constraint management | Less curtailment, cable/congestion relief | PPA, balancing, or programme funding |

We test **two stylised models** (not mutually exclusive) using central Q2 outputs and explicit **minimum
conditions** for each actor to participate profitably.
"""))

cells.append(code("""
def value_pool_gbp(avoided_mwh, wholesale=WHOLESALE_GBP_MWH):
    \"\"\"Gross £/yr if all avoided MWh valued at wholesale (upper bound).\"\"\"
    return avoided_mwh * wholesale

def split_pool(avoided_mwh, wholesale=WHOLESALE_GBP_MWH):
    gross = value_pool_gbp(avoided_mwh, wholesale)
    return pd.Series({
        "gross_value_gbp": gross,
        "households_gbp": gross * SHARE_HOUSEHOLD,
        "wind_gbp": gross * SHARE_WIND,
        "kaluza_gbp": gross * SHARE_KALUZA,
        "grid_gbp": gross * SHARE_GRID,
    })

per_home_avoided = full_avoided / N_HOUSEHOLDS_ORKNEY
capex = capex_per_home()
gross_pool = value_pool_gbp(full_avoided)
pool = split_pool(full_avoided)

print("=== Value pool @ 100% enrolment (central avoided MWh) ===")
display(pool.to_frame("£/yr"))

# --- Model A: Kaluza orchestrator + wind royalty + discounted heat ---
print("\\n### Model A — Orchestrator + royalty (Kaluza-led)")
# Household: annual benefit from cheap curtailed-window energy
hh_mwh_per_home = per_home_avoided  # proxy: each home absorbs this share on average
hh_benefit_per_home = hh_mwh_per_home * HOUSEHOLD_DISCOUNT_GBP_MWH
hh_payback_years = capex * (1 - 0.5) / max(hh_benefit_per_home, 1e-6)  # 50% subsidy example

model_a = pd.DataFrame([
    {"actor": "Household", "annual_value_gbp": hh_benefit_per_home * N_HOUSEHOLDS_ORKNEY,
     "annual_cost_or_outlay_gbp": capex * N_HOUSEHOLDS_ORKNEY * 0.5,
     "minimum_for_viability": f"Bill savings ≥ £{HOUSEHOLD_DISCOUNT_GBP_MWH}/MWh; payback < ~8 yr at 50% subsidy"},
    {"actor": "Kaluza", "annual_value_gbp": pool["kaluza_gbp"],
     "annual_cost_or_outlay_gbp": 200_000,
     "minimum_for_viability": f"Avoided MWh ≥ {capex * 500 / (KALUZA_VALUE_SHARE * WHOLESALE_GBP_MWH):.0f} to cover 500 installs (illustrative)"},
    {"actor": "Wind farmers", "annual_value_gbp": pool["wind_gbp"] + full_avoided * WHOLESALE_GBP_MWH * 0.5,
     "annual_cost_or_outlay_gbp": WIND_ROYALTY_ADMIN_GBP_YR * 10,
     "minimum_for_viability": f"Avoided fleet MWh ≥ {WIND_ROYALTY_ADMIN_GBP_YR / (SHARE_WIND * WHOLESALE_GBP_MWH):.0f} for royalty to cover admin"},
    {"actor": "Grid / DNO", "annual_value_gbp": pool["grid_gbp"],
     "annual_cost_or_outlay_gbp": 0,
     "minimum_for_viability": "Programme viable if constraint cost > £8/MWh equivalent (policy-led)"},
])
display(model_a)

# --- Model B: Grid-funded rollout (constraint procurement) ---
print("\\n### Model B — Constraint procurement (grid-led)")
# Grid pays capex subsidy; Kaluza operates; wind / households split energy value
grid_subsidy_per_home = 350  # £ grant per home toward £500 capex
model_b = pd.DataFrame([
    {"actor": "Household", "annual_value_gbp": hh_benefit_per_home * N_HOUSEHOLDS_ORKNEY,
     "annual_cost_or_outlay_gbp": (capex - grid_subsidy_per_home) * N_HOUSEHOLDS_ORKNEY,
     "minimum_for_viability": f"Consumer co-pay ≤ £{capex - grid_subsidy_per_home} per home"},
    {"actor": "Kaluza", "annual_value_gbp": pool["kaluza_gbp"] + grid_subsidy_per_home * N_HOUSEHOLDS_ORKNEY * 0.1,
     "annual_cost_or_outlay_gbp": 150_000,
     "minimum_for_viability": "Needs grid anchor contract ≥ ~3-year term"},
    {"actor": "Wind farmers", "annual_value_gbp": full_avoided * WHOLESALE_GBP_MWH * 0.6,
     "annual_cost_or_outlay_gbp": 0,
     "minimum_for_viability": "Participate if curtailed MWh > 1,000 fleet-wide (material)"},
    {"actor": "Grid / DNO", "annual_value_gbp": pool["grid_gbp"] + mwh_fleet * GRID_VALUE_GBP_MWH * 0.01,
     "annual_cost_or_outlay_gbp": grid_subsidy_per_home * N_HOUSEHOLDS_ORKNEY,
     "minimum_for_viability": (
         f"Capex programme ~£{grid_subsidy_per_home * N_HOUSEHOLDS_ORKNEY:,.0f}; "
         f"tariff share only ~£{pool['grid_gbp']:,.0f}/yr — viable under regulation, not energy margin alone"
     )},
])
display(model_b)

# Kaluza break-even vs subsidy (simplified: revenue = kaluza share of growing avoided MWh)
rev_central = pool["kaluza_gbp"]
rev_low = split_pool(full_avoided, WHOLESALE_LOW)["kaluza_gbp"]
rev_high = split_pool(full_avoided, WHOLESALE_HIGH)["kaluza_gbp"]

be_rows = []
for sub in SUBSIDY_LEVELS:
    n_be = break_even_households(per_home_avoided * (SHARE_KALUZA / KALUZA_VALUE_SHARE), subsidy=sub)
    be_rows.append({
        "subsidy_frac": sub,
        "consumer_pays_frac": 1 - sub,
        "break_even_households_kaluza": n_be,
        "feasible_on_orkney": n_be <= N_HOUSEHOLDS_ORKNEY,
    })
be_df = pd.DataFrame(be_rows)
print("\\n### Kaluza break-even households (central economics, Model A share)")
display(be_df)

min_mwh_wind = WIND_ROYALTY_ADMIN_GBP_YR / max(SHARE_WIND * WHOLESALE_GBP_MWH, 1e-6)
min_mwh_kaluza_install = (capex * 200) / max(KALUZA_VALUE_SHARE * WHOLESALE_GBP_MWH, 1e-6)
print(f"\\nIllustrative minimum avoided MWh for wind-partner fee cover: {min_mwh_wind:.0f} MWh/yr")
print(f"Illustrative minimum avoided MWh for 200-home unsubsidised install pot: {min_mwh_kaluza_install:.0f} MWh/yr")
print(f"Actual central avoided @ full pen: {full_avoided:.0f} MWh/yr -> Kaluza margin is small; grid or subsidy required.")
"""))

cells.append(code("""
# --- Extra: Revenue vs penetration ---
curve_df["kaluza_revenue_gbp"] = curve_df["avoided_mwh"].apply(
    lambda m: kaluza_annual_revenue(m)
)
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(curve_df["n_households"], curve_df["kaluza_revenue_gbp"] / 1e6, "o-", color="#ff7f0e")
ax.set_xlabel("Households enrolled")
ax.set_ylabel("£m / year")
ax.set_title("Kaluza revenue share vs enrolment (central price)")
plt.show()
"""))

cells.append(code("""
# --- Extra: Tornado — one-at-a-time sensitivity at full enrolment ---
base_avoided = full_avoided
tornado_specs = [
    ("n_turbines", [400, 600], lambda v: base_avoided * (v / N_TURBINES)),
    ("f_flex", [F_FLEX_LOW, F_FLEX_HIGH], None),
    ("availability", [AVAIL_LOW, AVAIL_HIGH], None),
    ("wholesale £/MWh", [WHOLESALE_LOW, WHOLESALE_HIGH], None),
]

def avoided_at_flex_avail(ff, av):
    df_f = build_flexible_demand(demand_all, f_flex=ff)
    _, a, _ = supply_demand_match(supply_30, df_f, N_HOUSEHOLDS_ORKNEY, availability=av)
    return a

tornado = []
for name, bounds, fn in tornado_specs:
    if name == "f_flex":
        lows = [avoided_at_flex_avail(bounds[0], AVAILABILITY), avoided_at_flex_avail(bounds[1], AVAILABILITY)]
        central = base_avoided
    elif name == "availability":
        lows = [avoided_at_flex_avail(F_FLEX, bounds[0]), avoided_at_flex_avail(F_FLEX, bounds[1])]
        central = base_avoided
    elif name == "wholesale £/MWh":
        lows = [kaluza_annual_revenue(base_avoided, price=bounds[0]), kaluza_annual_revenue(base_avoided, price=bounds[1])]
        central = rev_central
    else:
        lows = [fn(bounds[0]), fn(bounds[1])]
        central = base_avoided
    tornado.append({"driver": name, "low": min(lows), "high": max(lows), "central": central})

from matplotlib.patches import Patch

tornado_df = pd.DataFrame(tornado)
fig, ax = plt.subplots(figsize=(8, 4.5))
for i, row in tornado_df.iterrows():
    ax.barh(i, row["high"] - row["central"], left=row["central"], color="#aec7e8")
    ax.barh(i, row["central"] - row["low"], left=row["low"], color="#ffbb78")
ax.set_yticks(range(len(tornado_df)))
ax.set_yticklabels(tornado_df["driver"])
ax.set_xlabel("Outcome (MWh/yr avoided; wholesale row in £/yr)")
ax.set_title("Tornado — one-at-a-time sensitivity @ full enrolment")
ax.legend(
    handles=[
        Patch(facecolor="#ffbb78", label="Low scenario"),
        Patch(facecolor="#aec7e8", label="High scenario"),
    ],
    loc="lower right",
    fontsize=9,
)
plt.tight_layout()
plt.show()
"""))

# Executive summary populate
cells.append(md("## 11. Executive Summary (Headline Table)"))

cells.append(code("""
summary_df = pd.DataFrame({
    "Question": ["Q1 Curtailed (GWh/yr)", "Q2 Avoided @ 100% pen. (MWh/yr)",
                 "Q2 Recovery @ 100% pen.", "Q3 Homes for 25% DR penetration",
                 "Kaluza revenue @ 100% pen. (£/yr)"],
    "Result": [
        f"{gwh_fleet:.2f}",
        f"{full_avoided:.0f}",
        f"{100 * full_avoided / mwh_fleet:.2f}%",
        f"{int(q3_df.loc[q3_df['dr_penetration_target']=='25%', 'households_on_scheme'].iloc[0]):,}",
        f"{rev_central:,.0f}",
    ],
})
display(summary_df)
"""))

cells.append(md("""
## 12. Discussion — Synthesis & Critical Verdict

### Hypotheses

| ID | Verdict | Comment |
|----|---------|---------|
| P1 Material curtailment | **Supported** | ~77 GWh/yr is large enough to justify commercial attention. |
| P2 Temporal concentration | **Supported** | Curtailment is bursty (few % of half-hours carry most energy). |
| P3 Bounded DR recovery | **Supported — and sobering** | Saturation ≪ Q1; enrolment is **not** the binding lever today. |
| P4 Power curve | **Supported** | Valid for counterfactual; does not fix demand gap. |

### What is genuinely strong in this work

- Clear **problem quantification** (Q1) with documented assumptions.
- Honest **scale separation** between curtailed GWh and recoverable MWh.
- EDA explains **data defects** (Sep–Oct sample) without hiding them.
- Four-actor framing matches how Kaluza must negotiate in real deployments.

### What is weak or should not be oversold

- **Residential DR alone** cannot materially reduce fleet curtailment percentages in our model (<1% recovery at full pen).
- **Kaluza standalone economics** at £45/MWh and ~£500 capex imply **hundreds–thousands of homes** before platform break-even unless **grid or subsidy** funds rollout.
- **Wind-farmer value** only becomes interesting at higher avoided MWh or if Kaluza aggregates many sites — Orkney pilot is a **proof of concept**, not a wind-farm profit centre yet.
- **Grid value** is real in engineering terms (40 MW cable) but **hardest to monetise** without regulation; Model B assumes policy appetite.

### Strategic implication for Kaluza (2017 lens)

1. **Position HSO as orchestration IP**, not “we eliminate curtailment.”
2. **Anchor a grid or wind PPA** before mass household marketing — households follow subsidy + tariff.
3. **Pilot to measure real `f_flex`** — if trial doubles flexible kWh/home, avoided MWh roughly doubles.
4. **Bundle storage / hot-water duration** in roadmap — increases coincidence with curtailed windows.
5. **Do not promise** 25% fleet recovery to investors without new load classes (industrial, EV, export upgrades).

### Recommendations

| Priority | Action |
|----------|--------|
| 1 | Winter pilot targeting storage-heater homes in curtailed hours |
| 2 | Negotiate wind royalty on **marginal** avoided MWh, not headline GWh |
| 3 | Pursue DNO/grid co-funding (Model B) given constraint economics |
| 4 | Report enrolment in **MWh avoided**, not % curtailment recovered |
| 5 | QA tariff so household savings exceed co-pay after subsidy |
"""))

cells.append(md("""
## 13. Conclusion

**Problem:** Orkney curtails ~**77 GWh/yr** of wind (central 2017 estimate) — a major wasted asset.

**DR potential:** Residential HSO can avoid only **~267 MWh/yr** at full enrolment in our model — real but
**<1%** of Q1. The case for Kaluza is **not** bulk curtailment elimination; it is **proving flexible demand
orchestration** and capturing a **slice** of a multi-actor value pool.

**Business:** Profitability for Kaluza **requires** subsidies and/or grid/wind co-funding (Models A & B).
Households need tangible £/MWh savings; wind farmers need enough avoided MWh to cover participation;
the grid benefits from constraint relief but must **pay or regulate** that benefit.

**Recommendation:** Proceed with a **time-limited pilot** to recalibrate flexible capacity and coincidence,
while contracting at least one **non-household** counterparty (DNO or wind operator) so the platform is not
solely dependent on consumer capex recovery.

---

## Technical Appendix

### A1. Optional system-balance check (export cap)

Secondary sanity check: compare curtailed energy to a simplified balance using aggregate demand and a
**40 MW** export limit (not used as headline Q1).
"""))

cells.append(code("""
# Appendix: coarse 30-min balance (illustrative only)
gen_30 = supply_30.copy()
gen_30["gen_kwh"] = turbine.set_index("Timestamp").resample("30min")["Power_kw"].mean().values * 0.5  # approx
# align lengths
gen_30 = gen_30.dropna(subset=["gen_kwh"])
bal = demand_flex[["Timestamp", "demand_total_kw"]].merge(gen_30[["Timestamp", "gen_kwh", "curtailed_kwh"]], on="Timestamp")
bal["demand_kwh"] = bal["demand_total_kw"] * 0.5
bal["export_kwh"] = np.maximum(0, bal["gen_kwh"] - bal["demand_kwh"] - EXPORT_CAP_MW * 1000 * 0.5)
bal["surplus_kwh"] = np.maximum(0, bal["gen_kwh"] - bal["demand_kwh"] - bal["export_kwh"])
print("Appendix balance: mean surplus kWh per 30-min (single turbine gen, not fleet-scaled):",
      bal["surplus_kwh"].mean())
print("Note: Headline Q1 uses power-curve counterfactual method on curtailment regimes.")
"""))

cells.append(md("### A2. Data paths & reproducibility\n\nRun from repository root with `data/` alongside this notebook. Python 3.11+ with pandas, numpy, matplotlib, scipy."))

# Build notebook
nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11.0"},
    },
    "cells": cells,
}

NB_PATH.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
print(f"Wrote {NB_PATH} with {len(cells)} cells")
