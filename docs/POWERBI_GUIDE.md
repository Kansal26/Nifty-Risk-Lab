# Power BI Dashboard Architecture & Implementation Guide

This guide details the complete data model, exact DAX formulas, visual page layouts, headline empirical findings, and analytical constraints for constructing the **`nifty-risk-lab`** interactive dashboard in **Power BI on the Web** (Power BI Service) or Power BI Desktop.

---

## 1. Web-Optimized Data Model Architecture

### Design Philosophy
Power BI on the web is optimized for clean star schemas with lightweight data models:
- **Zero Heavy Computations in Power BI**: All intensive mathematical operations (20d/60d realized volatility, 250-day rolling Historical and Normal VaR, Kupiec POF likelihood ratio tests, Black-Scholes Greeks, 60-day rolling Pearson correlations, and OLS market model regressions) are **precomputed in Python** and exported as clean, flat CSVs in `exports/`.
- **Single Date Dimension**: All time-series tables relate to a single standardized `date_table.csv` via 1-to-many relationships on ISO `date` (`YYYY-MM-DD`).
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
```

### Table Dictionary & Entity Relationships
| Table Name | Source File | Type | Primary / Join Key | Relationship Cardinality | Cross-Filter Direction |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`date_table`** | `exports/date_table.csv` | Date Dimension | `date` | Dimension (1) | — |
| **`market_daily`** | `exports/market_daily.csv` | Fact Table | `date` | Many-to-One ($\text{Fact } * \to \text{Date } 1$) | Single (`date_table` filters `market_daily`) |
| **`risk_metrics`** | `exports/risk_metrics.csv` | Fact Table | `date` | Many-to-One ($\text{Fact } * \to \text{Date } 1$) | Single (`date_table` filters `risk_metrics`) |
| **`vol_comparison`** | `exports/vol_comparison.csv` | Fact Table | `date` | Many-to-One ($\text{Fact } * \to \text{Date } 1$) | Single (`date_table` filters `vol_comparison`) |
| **`correlations`** | `exports/correlations.csv` | Fact Table | `date` | Many-to-One ($\text{Fact } * \to \text{Date } 1$) | Single (`date_table` filters `correlations`) |
| **`budget_events_summary`** | `exports/budget_events_summary.csv` | Event Dimension | `event_date` | Dimension (1) | — |
| **`budget_event_paths`** | `exports/budget_event_paths.csv` | Event Trajectory Fact | `event_date` | Many-to-One ($\text{Fact } * \to \text{Summary } 1$) | Single (`summary` filters `paths`) |
| **`var_backtest`** | `exports/var_backtest.csv` | Summary Table | None (Standalone) | Disconnected | — |

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
   - Card 1: `[Latest Nifty Close]` (Formatted as Currency ₹, e.g. `₹25,227.95`).
   - Card 2: `[Daily Return]` (Formatted as Percentage `+0.24%`).
   - Card 3: `[Latest VIX]` (Formatted as Decimal `15.57`).
   - Card 4: `Bank NIFTY Close` (Formatted as Currency ₹, e.g. `₹52,140.00`).
2. **Slicers (Top Left & Side Panel)**:
   - Date Range Slicer: `date_table[date]` (Relative date slider or Year dropdown).
   - Index Slicer: Switch between `NIFTY 50` and `Bank NIFTY`.
3. **Main Visual 1 (Line Chart - 60% Width)**:
   - X-Axis: `date_table[date]`
   - Y-Axis: `market_daily[nifty50_close]` and `market_daily[bank_nifty_close]` (normalized or secondary axis).
   - Tooltips: Date, Close, Daily Log Return.
4. **Main Visual 2 (Area / Line Chart - 40% Width)**:
   - X-Axis: `date_table[date]`
   - Y-Axis: `market_daily[india_vix_close]`
   - Reference Line: Historical median VIX line at `15.2%`.

#### Headline Finding (Written strictly from the data):
> **Data Headline:** "Over the 2015–2026 sample period, the NIFTY 50 compounded from ₹8,284 to ₹25,228 (+204.5%), while India VIX maintained a long-run median of 15.2% with acute volatility spikes reaching 83.6% during the March 2020 COVID shock."

#### What This Cannot Tell You:
> **Limitations Note:** "This page displays historical nominal closing prices. It cannot predict future index direction, execute intraday stop-losses, account for transaction costs/taxes (STT), or capture the cash dividend yield component of total returns."

---

### Page 2: Risk and Volatility

#### Layout & Visual Cards:
1. **Header KPI Cards**:
   - Card 1: `[Annualised Realized Volatility]` (20-day annualized, e.g. `11.8%`).
   - Card 2: `[VIX Minus Realized Volatility]` (VRP spread, e.g. `+3.7 pts`).
   - Card 3: `[Nifty Current Drawdown]` (Current percentage from high water mark).
   - Card 4: `[VaR Exceptions Count]` (Total 99% Normal VaR breaches).
2. **Visual 1 (Dual Line Chart - Top Half)**:
   - X-Axis: `date_table[date]`
   - Y-Axis: `vol_comparison[india_vix_close]` (Implied Volatility) vs `vol_comparison[trailing_vol_21d]` (Realized Volatility).
3. **Visual 2 (Area Chart - Bottom Left)**:
   - X-Axis: `date_table[date]`
   - Y-Axis: `risk_metrics[nifty50_drawdown]` (Underwater drawdown curve from 0% down to -38.4%).
4. **Visual 3 (Line & Scatter Chart - Bottom Right)**:
   - X-Axis: `date_table[date]`
   - Line: `risk_metrics[nifty50_var_norm_99]` (1-day 99% VaR threshold cutoff).
   - Scatter/Dots: `market_daily[nifty50_log_return]` where return breached VaR cutoff (Exception points highlighted in red).
5. **Backtest Summary Table (Side / Popup Matrix)**:
   - Matrix Visual from `exports/var_backtest.csv`: Columns `Asset`, `Model`, `Confidence`, `Expected Exceptions`, `Actual Exceptions`, `Ratio`, `Kupiec LR`, `p-value`, `Outcome`.

#### Headline Finding (Written strictly from the data):
> **Data Headline:** "Parametric Normal 99% VaR models suffered 50 exceptions versus 26.7 expected (1.87x failure ratio, Kupiec $p = 0.0001$), decisively rejecting Gaussian tail assumptions due to fat-tailed crash clustering."

#### What This Cannot Tell You:
> **Limitations Note:** "Value at Risk specifies the minimum threshold loss expected at a given confidence level, but provides zero information about tail severity or maximum loss beyond that threshold (Expected Shortfall). Historical simulation assumes past return distributions repeat."

---

### Page 3: Cross-Market Linkages

#### Layout & Visual Cards:
1. **Slicers**:
   - Date range slicer: `date_table[year_quarter]` or `date_table[date]`.
2. **Visual 1 (Multi-Line Chart - 70% Width)**:
   - Precomputed 60-day rolling correlations from `exports/correlations.csv` (since Power BI has no native rolling correlation calculation):
     - Line 1: `correlations[corr_sp500]` (NIFTY vs S&P 500)
     - Line 2: `correlations[corr_brent]` (NIFTY vs Brent Crude)
     - Line 3: `correlations[corr_usdinr]` (NIFTY vs USD/INR)
     - Line 4: `correlations[corr_us10y]` (NIFTY vs US 10-Year Treasury Yield)
   - Zero Baseline Line: Horizontal reference line at $Y = 0$.
3. **Visual 2 (Summary Table / Card Deck - 30% Width)**:
   - Summary statistics of rolling correlations:
     - NIFTY vs S&P 500: Mean $+0.216$ (Min $-0.21$, Max $+0.78$)
     - NIFTY vs USD/INR: Mean $-0.146$ (Min $-0.54$, Max $+0.48$)
     - NIFTY vs Brent Crude: Mean $+0.064$ (Min $-0.53$, Max $+0.70$)
     - NIFTY vs US 10Y: Mean $+0.073$ (Min $-0.29$, Max $+0.68$)

#### Headline Finding (Written strictly from the data):
> **Data Headline:** "NIFTY 50 demonstrates persistent negative co-movement with USD/INR (average correlation -0.146, reaching -0.538 during capital flight episodes), while global correlation with the S&P 500 averages +0.216 and surges to +0.776 during international liquidity crises."

#### What This Cannot Tell You:
> **Limitations Note:** "Rolling correlations measure statistical co-movement, not economic causality. High correlation with the S&P 500 does not indicate whether Indian markets lead or lag Wall Street, and correlations frequently break down during non-synchronous exchange holidays."

---

### Page 4: Budget Event Study

#### Layout & Visual Cards:
1. **Top Slicers & Filters**:
   - Budget Event Slicer: Dropdown from `budget_events_summary[event_date]` (allows selecting a specific budget or viewing all 9 events).
   - Budget Type Filter: Slicer for `Regular` vs `Interim`.
2. **Header KPI Cards**:
   - Card 1: `Average CAR[-1, +1]`: `+1.53%` (Cross-event mean).
   - Card 2: `Average CAR[0, +5]`: `+1.61%` (Cross-event post-budget drift).
   - Card 3: `Average Day-0 VIX Change`: `-1.67 pts` (Statistically significant at $p = 0.0001$).
   - Card 4: `Day-0 Win Rate`: `55.6%` (5 positive out of 9 budgets).
3. **Visual 1 (Event Path Line Chart - 55% Width)**:
   - Source: `exports/budget_event_paths.csv`
   - X-Axis: `budget_event_paths[tau]` (Relative trading day from $-5$ to $+5$).
   - Y-Axis: `budget_event_paths[nifty_car]` and `budget_event_paths[bank_nifty_car]`.
   - Series / Legend: `budget_event_paths[event_date]` (Displays individual event paths with cross-event average highlighted).
   - Vertical Reference Line: Red dashed line at $\tau = 0$ (Budget Presentation Day).
4. **Visual 2 (Event Summary Table - 45% Width)**:
   - Table from `exports/budget_events_summary.csv`:
     - Columns: `event_date`, `budget_type`, `finance_minister`, `nifty_day0_ar_pct`, `nifty_car_minus1_plus1_pct`, `nifty_car_0_plus5_pct`, `vix_day0_change`, `notes`.

#### Headline Finding (Written strictly from the data):
> **Data Headline:** "Across all 9 Union Budgets (2016–2024), India VIX experienced a universal Day-0 volatility crush (mean -1.67 pts, $t = -6.93, p = 0.0001$, dropping in 100% of events), whereas equity abnormal returns (+1.53% CAR[-1, +1]) remain statistically indistinguishable from zero ($p = 0.108$)."

#### What This Cannot Tell You:
> **Limitations Note:** "This event study reflects close-to-close price adjustments across only 9 sample events; it cannot capture the violent intraday whipsaws during the 11:00 AM live parliamentary budget speech, nor does it isolate the budget impact from concurrent global macro events."
