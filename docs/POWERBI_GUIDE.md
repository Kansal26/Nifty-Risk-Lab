# Power BI Dashboard Architecture & Implementation Guide

This guide details the complete data model, exact DAX formulas, visual page layouts, headline empirical findings, and analytical constraints for constructing the **`nifty-risk-lab`** interactive dashboard in **Power BI on the Web** (Power BI Service) or Power BI Desktop.

---

## 1. Web-Optimized Data Model Architecture

### Design Philosophy
Power BI on the web is optimized for clean star schemas with lightweight data models:
- **Zero Heavy Computations in Power BI**: All intensive mathematical operations (20d/60d realized volatility, 250-day rolling Historical and Normal VaR, Kupiec POF likelihood ratio tests, Black-Scholes Greeks, 60-day rolling Pearson correlations, rebased 100 indices, and OLS market model regressions) are **precomputed in Python** and exported both as a consolidated multi-sheet Excel workbook (`exports/nifty_risk_lab.xlsx`) and clean flat CSVs in `exports/`.
- **Excel Workbook Compatibility (`exports/nifty_risk_lab.xlsx`)**: Contains 9 sheets corresponding to each table (`date_table`, `market_daily`, `risk_metrics`, `vol_comparison`, `correlations`, `budget_events_summary`, `budget_event_paths`, `var_backtest`, `kpi_summary`). Each sheet is formatted as an official Excel Table named identically to the sheet, with native Excel date cells (`d`), numeric columns stored as numbers, no merged cells, no blank rows, and headers in row 1.
- **Single Date Dimension**: All time-series tables relate to a single standardized `date_table` via 1-to-many relationships on ISO `date` (`YYYY-MM-DD`).
- **Minimal Relationships**: Cross-filtering is set to **Single (Dimension $\to$ Fact)** to avoid ambiguous relationship paths and maintain rapid, sub-second query rendering in browser sessions.

```
                      ┌──────────────────────┐
                      │      date_table      │
                      │  (Primary Key: date) │
                      └──────────┬───────────┘
                                 │ 1
        ┌────────────────┬───────┼───────────────┬────────────────┐
        │ *              │ *     │ *             │ *              │ *
┌───────┴──────┐  ┌──────┴───────┴──────┐  ┌─────┴───────┐  ┌─────┴────────┐
│ market_daily │  │     risk_metrics    │  │ vol_compar. │  │ correlations │
└──────────────┘  └─────────────────────┘  └─────────────┘  └──────────────┘

                      ┌────────────────────────────┐
                      │   budget_events_summary    │
                      │ (Primary Key: event_date)  │
                      └──────────────┬─────────────┘
                                     │ 1
                                     │ *
                      ┌──────────────┴─────────────┐
                      │     budget_event_paths     │
                      └────────────────────────────┘

                      ┌────────────────────────────┐
                      │        var_backtest        │
                      │    (Standalone Summary)    │
                      └────────────────────────────┘

                      ┌────────────────────────────┐
                      │        kpi_summary         │
                      │    (Executive Cards)       │
                      └────────────────────────────┘
```

### Table Dictionary & Entity Relationships
| Table Name | Source File / Sheet | Type | Primary / Join Key | Relationship Cardinality | Cross-Filter Direction |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`date_table`** | `date_table.csv` / `date_table` | Date Dimension | `date` | Dimension (1) | — |
| **`market_daily`** | `market_daily.csv` / `market_daily` | Fact Table | `date` | Many-to-One ($\text{Fact } * \to \text{Date } 1$) | Single (`date_table` filters `market_daily`) |
| **`risk_metrics`** | `risk_metrics.csv` / `risk_metrics` | Fact Table | `date` | Many-to-One ($\text{Fact } * \to \text{Date } 1$) | Single (`date_table` filters `risk_metrics`) |
| **`vol_comparison`** | `vol_comparison.csv` / `vol_comparison` | Fact Table | `date` | Many-to-One ($\text{Fact } * \to \text{Date } 1$) | Single (`date_table` filters `vol_comparison`) |
| **`correlations`** | `correlations.csv` / `correlations` | Fact Table | `date` | Many-to-One ($\text{Fact } * \to \text{Date } 1$) | Single (`date_table` filters `correlations`) |
| **`budget_events_summary`** | `budget_events_summary.csv` / `budget_events_summary` | Event Dimension | `event_date` | Dimension (1) | — |
| **`budget_event_paths`** | `budget_event_paths.csv` / `budget_event_paths` | Event Trajectory Fact | `event_date` | Many-to-One ($\text{Fact } * \to \text{Summary } 1$) | Single (`summary` filters `paths`) |
| **`var_backtest`** | `var_backtest.csv` / `var_backtest` | Regulatory Summary | None (Standalone) | Disconnected | — |
| **`kpi_summary`** | `kpi_summary.csv` / `kpi_summary` | Executive Cards | None (Standalone) | Disconnected | — |

---

## 2. Standardized DAX Measures

Create a dedicated measures table `_Measures` and insert the following exact DAX formulas:

### 1. Latest NIFTY 50 Close
```dax
Latest Nifty Close = 
CALCULATE(
    MAX(market_daily[nifty50_close]),
    LASTDATE(date_table[date]),
    market_daily[nifty50_close] > 0
)
```

### 2. Daily Return (Average Log Return in Selected Period)
```dax
Daily Return = 
AVERAGE(market_daily[nifty50_log_return])
```

### 3. Annualized Realized Volatility (20-Day Lookback)
```dax
Annualised Realized Volatility = 
CALCULATE(
    AVERAGE(risk_metrics[nifty50_vol_20d]),
    LASTDATE(date_table[date])
)
```

### 4. Latest India VIX Close
```dax
Latest VIX = 
CALCULATE(
    MAX(market_daily[india_vix_close]),
    LASTDATE(date_table[date]),
    market_daily[india_vix_close] > 0
)
```

### 5. Volatility Risk Premium (VIX minus Realized Volatility)
```dax
VIX Minus Realized Volatility = 
VAR _CurrentVIX = [Latest VIX]
VAR _CurrentRealized = [Annualised Realized Volatility] * 100.0
RETURN
IF(
    NOT ISBLANK(_CurrentVIX) && NOT ISBLANK(_CurrentRealized),
    _CurrentVIX - _CurrentRealized,
    BLANK()
)
```

### 6. Value at Risk (VaR) Exceptions Count
```dax
VaR Exceptions Count = 
SUM(risk_metrics[nifty50_exc_norm_99])
```

### 7. Cumulative Abnormal Return (Average CAR[-1, +1] across Budgets)
```dax
Average CAR = 
AVERAGE(budget_events_summary[nifty_car_minus1_plus1_pct])
```

### 8. NIFTY Current Drawdown
```dax
Nifty Current Drawdown = 
CALCULATE(
    AVERAGE(risk_metrics[nifty50_drawdown]),
    LASTDATE(date_table[date])
)
```

---

## 3. Dashboard Page Layouts, Visual Specifications & Findings

---

### Page 1: Market Overview

#### Layout & Visual Cards:
1. **Header KPI Cards (Top Banner)**:
   - Card 1: `[Latest Nifty Close]` (Formatted as Currency ₹, e.g. `₹25,227.95` on `2026-11-18`).
   - Card 2: `[Daily Return]` (Formatted as Percentage, e.g. `-0.63%` on `2026-11-18`).
   - Card 3: `[Latest VIX]` (Formatted as Points, e.g. `15.57` on `2026-11-18`).
   - Card 4: `Bank NIFTY Close` (Formatted as Currency ₹, e.g. `₹62,038.65` on `2026-11-18`).
2. **Slicers (Top Left & Side Panel)**:
   - Date Range Slicer: `date_table[date]` (Relative date slider or Year dropdown).
   - Index Slicer: Switch between `NIFTY 50` and `Bank NIFTY`.
3. **Main Visual 1 (Line Chart - 60% Width)**:
   - Direct Comparative Rebased Series:
     - X-Axis: `date_table[date]`
     - Y-Axis: `market_daily[nifty50_idx100]` and `market_daily[bank_nifty_idx100]` (both rebased to 100 on 2015-01-02).
     - Tooltips: Date, Close Level, Rebased Level, Daily Log Return.
4. **Main Visual 2 (Area / Line Chart - 40% Width)**:
   - X-Axis: `date_table[date]`
   - Y-Axis: `market_daily[india_vix_close]`
   - Reference Line: Historical median VIX line at `15.31%`.

#### Headline Finding (Written strictly from the data):
> **Data Headline:** "Over the 2015–2026 sample period (2015-01-02 to 2026-11-18), the NIFTY 50 compounded from ₹8,395.45 to ₹25,227.95 (+200.50%), while India VIX maintained a long-run median of 15.31% with acute volatility spikes peaking at 83.61% on 2020-03-24."

#### What This Cannot Tell You:
> **Limitations Note:** "This page displays historical nominal closing prices. It cannot predict future index direction, execute intraday stop-losses, account for transaction costs/taxes (STT), or capture the cash dividend yield component of total returns."

---

### Page 2: Risk and Volatility

#### Layout & Visual Cards:
1. **Header KPI Cards**:
   - Card 1: `[Annualised Realized Volatility]` (20-day annualized, e.g. `14.06%` on `2026-11-18`).
   - Card 2: `[VIX Minus Realized Volatility]` (VRP spread, e.g. `+1.51 pts`).
   - Card 3: `[Nifty Current Drawdown]` (`-4.18%` on `2026-11-18`).
   - Card 4: `[VaR Exceptions Count]` (Total 99% Normal VaR breaches: `50` breaches).
2. **Visual 1 (Dual Line Chart - Top Half)**:
   - X-Axis: `date_table[date]`
   - Y-Axis: `vol_comparison[india_vix_close]` (Implied Volatility) vs `vol_comparison[trailing_vol_21d]` (Realized Volatility).
3. **Visual 2 (Area Chart - Bottom Left)**:
   - X-Axis: `date_table[date]`
   - Y-Axis: `risk_metrics[nifty50_drawdown]` (Underwater drawdown curve from 0% down to -38.44% trough on 2020-03-23).
4. **Visual 3 (Line & Scatter Chart - Bottom Right)**:
   - X-Axis: `date_table[date]`
   - Line: `risk_metrics[nifty50_var_norm_99]` (1-day 99% VaR threshold cutoff).
   - Scatter/Dots: `market_daily[nifty50_log_return]` where return breached VaR cutoff (Exception points highlighted in red).
5. **Backtest Summary Table (Side / Popup Matrix)**:
   - Matrix Visual from `exports/var_backtest.csv`: Columns `Asset`, `Model`, `Confidence`, `Expected Exceptions`, `Actual Exceptions`, `Ratio`, `Kupiec LR`, `p-value`, `Outcome`.

#### Headline Finding (Written strictly from the data):
> **Data Headline:** "Parametric Normal 99% VaR models suffered 50 exceptions versus 26.7 expected (1.87x failure ratio, Kupiec LR = 16.289, $p = 0.0001$), decisively rejecting Gaussian tail assumptions due to fat-tailed crash clustering. The maximum drawdown reached -38.44% on 2020-03-23."

#### What This Cannot Tell You:
> **Limitations Note:** "Value at Risk specifies the minimum threshold loss expected at a given confidence level, but provides zero information about tail severity or maximum loss beyond that threshold (Expected Shortfall). Historical simulation assumes past return distributions repeat."

---

### Page 3: Cross-Market Linkages

#### Layout & Visual Cards:
1. **Slicers**:
   - Date range slicer: `date_table[year_quarter]` or `date_table[date]`.
2. **Visual 1 (Multi-Line Chart - 70% Width)**:
   - Precomputed 60-day rolling correlations from `exports/correlations.csv`:
     - Line 1: `correlations[corr_sp500]` (NIFTY vs S&P 500)
     - Line 2: `correlations[corr_brent]` (NIFTY vs Brent Crude)
     - Line 3: `correlations[corr_usdinr]` (NIFTY vs USD/INR)
     - Line 4: `correlations[corr_us10y]` (NIFTY vs US 10-Year Treasury Yield)
   - Zero Baseline Line: Horizontal reference line at $Y = 0$.
3. **Visual 2 (Summary Table / Card Deck - 30% Width)**:
   - Exact statistics of 60-day rolling correlations:
     - NIFTY vs S&P 500: Mean `+0.216` (minimum `-0.212` on 2025-11-03, peaked at `+0.776` on 2020-03-16)
     - NIFTY vs USD/INR: Mean `-0.146` (reached a minimum of `-0.538` on 2026-03-24, peaked at `+0.478` on 2024-08-28)
     - NIFTY vs Brent Crude: Mean `+0.064` (minimum `-0.532` on 2026-06-24, peaked at `+0.701` on 2020-03-18)
     - NIFTY vs US 10Y Yield: Mean `+0.073` (minimum `-0.294` on 2023-10-19, peaked at `+0.680` on 2020-03-09)

#### Headline Finding (Written strictly from the data):
> **Data Headline:** "NIFTY 50 demonstrates persistent negative co-movement with USD/INR (average correlation -0.146, reaching a minimum of -0.538 on 2026-03-24 and peaking at +0.478 on 2024-08-28), while rolling correlation with the S&P 500 averages +0.216, peaking at +0.776 on 2020-03-16 and reaching a minimum of -0.212 on 2025-11-03."

#### What This Cannot Tell You:
> **Limitations Note:** "Rolling correlations measure statistical co-movement, not economic causality. High correlation with the S&P 500 does not indicate whether Indian markets lead or lag Wall Street, and correlations frequently break down during non-synchronous exchange holidays."

---

### Page 4: Budget Event Study

#### Layout & Visual Cards:
1. **Top Slicers & Filters**:
   - Budget Event Slicer: Dropdown from `budget_events_summary[event_date]` (covers the 9 most recent budgets between `2019-07-05` and `2026-02-01`).
   - Series Filter / Legend: `budget_event_paths[series_label]` (allows selecting individual budget dates or `'Average'` for the cross-event average line).
   - Budget Type Filter: Slicer for `'Union Budget'` vs `'Interim Budget'`.
2. **Header KPI Cards**:
   - Card 1: `Average CAR[-1, +1]`: `+0.71%` (exact mean $+0.7095\%$, $t = +0.842, p = 0.4240$).
   - Card 2: `Average CAR[0, +5]`: `+0.82%` (exact mean $+0.8168\%$, $t = +0.705, p = 0.5006$).
   - Card 3: `Average Day-0 VIX Change`: `-1.13 pts` (exact mean $-1.1311$ points, $t = -3.196, p = 0.0127$).
   - Card 4: `Day-0 Win Rate`: `22.2%` (2 positive abnormal return days out of 9 presentations).
3. **Visual 1 (Event Path Line Chart - 55% Width)**:
   - Source: `exports/budget_event_paths.csv` / `budget_event_paths`
   - X-Axis: `budget_event_paths[tau]` (Relative trading day from $-5$ to $+5$).
   - Y-Axis: `budget_event_paths[nifty_car]` and `budget_event_paths[bank_nifty_car]`.
   - Series / Legend: `budget_event_paths[series_label]` (Plots individual event trajectories alongside the precomputed `'Average'` series).
   - Vertical Reference Line: Red dashed line at $\tau = 0$ (Budget Presentation Day).
4. **Visual 2 (Event Summary Table - 45% Width)**:
   - Table from `exports/budget_events_summary.csv`:
     - Columns: `event_date`, `budget_type`, `finance_minister`, `nifty_day0_ar_pct`, `nifty_car_minus1_plus1_pct`, `nifty_car_0_plus5_pct`, `vix_day0_change`, `notes`.

#### Headline Finding (Written strictly from the data):
> **Data Headline:** "Across the 9 most recent Union Budgets presented between 2019-07-05 and 2026-02-01, India VIX experienced a statistically significant Day-0 volatility drop (mean -1.131 points, $t = -3.196, p = 0.0127$), whereas equity abnormal returns (+0.710% CAR[-1, +1]) remain statistically indistinguishable from zero ($t = +0.842, p = 0.4240$). Day-0 abnormal returns were positive in 2 of 9 events (22.2% win rate)."

#### What This Cannot Tell You:
> **Limitations Note:** "This event study reflects close-to-close price adjustments across only 9 sample events; it cannot capture the violent intraday whipsaws during the 11:00 AM live parliamentary budget speech, nor does it isolate the budget impact from concurrent global macro events."
