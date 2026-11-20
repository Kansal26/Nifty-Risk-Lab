# Data Dictionary: Nifty Risk Lab Exports

This document specifies the exact schema, data types, physical units, and analytical definitions for every column across all datasets in `exports/` (both the multi-sheet Excel workbook `exports/nifty_risk_lab.xlsx` and individual tidy CSV files).

---

## 1. `date_table`

**Purpose**: Master calendar dimension table providing continuous date mapping from 2015 through 2026 for slicers, quarter/month aggregations, and budget event filtering.

| Column Name | Data Type | Excel Type | Physical Unit | Description & Formula |
|:---|:---|:---|:---|:---|
| `date` | String / ISO Date | Date (`d`, `yyyy-mm-dd`) | Calendar Day | ISO-8601 calendar date (`YYYY-MM-DD`). |
| `year` | Integer | Number | Year (YYYY) | Calendar year (e.g., 2015 to 2026). |
| `quarter` | String | Text | Category | Formatted quarter label (`Q1`, `Q2`, `Q3`, `Q4`). |
| `quarter_number` | Integer | Number | Integer (1–4) | Numeric quarter of year (used for natural sorting). |
| `year_quarter` | String | Text | Category | Combined year and quarter label (e.g., `2024-Q1`). |
| `month` | String | Text | Category | Full English calendar month name (`January` to `December`). |
| `month_number` | Integer | Number | Integer (1–12) | Numeric month of year (used for natural sorting). |
| `year_month` | String | Text | Category | Formatted year-month string (`YYYY-MM`). |
| `day_of_month` | Integer | Number | Integer (1–31) | Calendar day of month. |
| `day_of_week` | String | Text | Category | Full English day name (`Monday` to `Sunday`). |
| `is_trading_day` | Integer | Number | Binary Flag (0 or 1) | `1` if date is an active NSE trading day for NIFTY 50; `0` for weekends and NSE holidays. |
| `is_budget_presentation_date` | Integer | Number | Binary Flag (0 or 1) | `1` if date corresponds to a Union or Interim Budget presentation; `0` otherwise. |
| `budget_type` | String | Text | Category | Classification: `'Union Budget'`, `'Interim Budget'`, or `'None'`. |

---

## 2. `market_daily`

**Purpose**: Master daily market pricing and continuously compounded (log) return time series for Indian indices and international macro benchmarks.

| Column Name | Data Type | Excel Type | Physical Unit | Description & Formula |
|:---|:---|:---|:---|:---|
| `date` | String / ISO Date | Date (`d`, `yyyy-mm-dd`) | Trading Day | ISO-8601 NSE trading date (`YYYY-MM-DD`). |
| `nifty50_close` | Float | Number | Index Points (INR) | Official daily closing level of the NIFTY 50 Index. |
| `nifty50_idx100` | Float | Number | Rebased Index Points | NIFTY 50 close rebased to `100.00` on first date `2015-01-02`: $(P_t / P_0) \times 100$. |
| `nifty50_log_return` | Float | Number | Decimal Fraction | Daily log return: $r_t = \ln(P_t / P_{t-1})$. E.g., `+0.0125` represents $+1.25\%$. |
| `bank_nifty_close` | Float | Number | Index Points (INR) | Official daily closing level of the Nifty Bank Index. |
| `bank_nifty_idx100` | Float | Number | Rebased Index Points | Bank Nifty close rebased to `100.00` on first date `2015-01-02`: $(P_t / P_0) \times 100$. |
| `bank_nifty_log_return` | Float | Number | Decimal Fraction | Daily log return: $r_t = \ln(P_t / P_{t-1})$ as a decimal fraction. |
| `india_vix_close` | Float | Number | Points / % Volatility | India VIX closing level. Expressed in annualised percentage volatility points (e.g., `15.57` represents $15.57\%$ annualized implied vol). |
| `india_vix_log_return` | Float | Number | Decimal Fraction | Daily log return of the India VIX index level: $\ln(VIX_t / VIX_{t-1})$. |
| `sp500_close` | Float | Number | Index Points (USD) | S&P 500 Index closing level (forward-filled up to 3 days for calendar alignment). |
| `sp500_log_return` | Float | Number | Decimal Fraction | Daily log return of S&P 500 as a decimal fraction. |
| `brent_crude_close` | Float | Number | USD per Barrel ($/bbl) | Brent crude oil futures continuous settlement price in USD/bbl (max 3-day ffill). |
| `brent_crude_log_return` | Float | Number | Decimal Fraction | Daily log return of Brent crude as a decimal fraction. |
| `usdinr_close` | Float | Number | INR per 1 USD (₹/$) | USD/INR spot currency exchange rate (Indian Rupees per 1 US Dollar, max 3-day ffill). |
| `usdinr_log_return` | Float | Number | Decimal Fraction | Daily log return of USD/INR exchange rate as a decimal fraction. |
| `us10y_yield_close` | Float | Number | Percentage Points (%) | US 10-Year Treasury note nominal constant maturity yield per annum (e.g., `4.45` is $4.45\%$). |
| `us10y_yield_log_return` | Float | Number | Decimal Fraction | Daily log change of the yield level: $\ln(Y_t / Y_{t-1})$. |

---

## 3. `risk_metrics`

**Purpose**: Rolling annualized volatility, running peak-to-trough drawdowns, 1-day 95% and 99% Value at Risk thresholds, and binary breach flags.

| Column Name | Data Type | Excel Type | Physical Unit | Description & Formula |
|:---|:---|:---|:---|:---|
| `date` | String / ISO Date | Date (`d`, `yyyy-mm-dd`) | Trading Day | ISO-8601 NSE trading date. |
| `nifty50_vol_20d` | Float | Number | Decimal Fraction (Annualised) | 20-trading-day rolling sample standard deviation of daily log returns: $\sigma_{20} \times \sqrt{252}$. E.g., `0.1406` is $14.06\%$ annualized. |
| `nifty50_vol_60d` | Float | Number | Decimal Fraction (Annualised) | 60-trading-day rolling annualised volatility: $\sigma_{60} \times \sqrt{252}$. |
| `nifty50_peak` | Float | Number | Index Points (INR) | Running cumulative maximum closing level up to date $t$: $M_t = \max_{s \le t}(P_s)$. |
| `nifty50_drawdown` | Float | Number | Decimal Fraction | Peak-to-current drawdown: $(P_t - M_t) / M_t$. Non-positive decimal (e.g., `-0.0418` is $-4.18\%$). |
| `nifty50_var_hist_95` | Float | Number | Decimal Return Cutoff | 1-day 95% Historical Simulation VaR cutoff (5th percentile of past 250 daily returns). E.g., `-0.0125`. |
| `nifty50_var_hist_99` | Float | Number | Decimal Return Cutoff | 1-day 99% Historical Simulation VaR cutoff (1st percentile of past 250 daily returns). |
| `nifty50_var_norm_95` | Float | Number | Decimal Return Cutoff | 1-day 95% Parametric Normal VaR cutoff: $\hat{\mu}_{250} - 1.644853 \hat{\sigma}_{250}$. |
| `nifty50_var_norm_99` | Float | Number | Decimal Return Cutoff | 1-day 99% Parametric Normal VaR cutoff: $\hat{\mu}_{250} - 2.326348 \hat{\sigma}_{250}$. |
| `nifty50_exc_hist_95` | Integer / Null | Number / Blank | Binary Flag (0 or 1) | `1` if actual return $r_t < \text{VaR}$; `0` otherwise; blank/null during 250-day rolling warmup. |
| `nifty50_exc_hist_99` | Integer / Null | Number / Blank | Binary Flag (0 or 1) | `1` if breach; `0` otherwise; blank/null during warmup. |
| `nifty50_exc_norm_95` | Integer / Null | Number / Blank | Binary Flag (0 or 1) | `1` if breach; `0` otherwise; blank/null during warmup. |
| `nifty50_exc_norm_99` | Integer / Null | Number / Blank | Binary Flag (0 or 1) | `1` if breach; `0` otherwise; blank/null during warmup. |
| `bank_nifty_vol_20d` | Float | Number | Decimal Fraction (Annualised) | Bank Nifty 20-trading-day annualised volatility ($\sigma_{20} \times \sqrt{252}$). |
| `bank_nifty_vol_60d` | Float | Number | Decimal Fraction (Annualised) | Bank Nifty 60-trading-day annualised volatility ($\sigma_{60} \times \sqrt{252}$). |
| `bank_nifty_peak` | Float | Number | Index Points (INR) | Running cumulative maximum closing level for Bank Nifty. |
| `bank_nifty_drawdown` | Float | Number | Decimal Fraction | Bank Nifty peak-to-current drawdown: $(P_t - M_t) / M_t$. |
| `bank_nifty_var_hist_95`| Float | Number | Decimal Return Cutoff | Bank Nifty 1-day 95% Historical VaR cutoff over past 250 days. |
| `bank_nifty_var_hist_99`| Float | Number | Decimal Return Cutoff | Bank Nifty 1-day 99% Historical VaR cutoff over past 250 days. |
| `bank_nifty_var_norm_95`| Float | Number | Decimal Return Cutoff | Bank Nifty 1-day 95% Parametric Normal VaR cutoff over past 250 days. |
| `bank_nifty_var_norm_99`| Float | Number | Decimal Return Cutoff | Bank Nifty 1-day 99% Parametric Normal VaR cutoff over past 250 days. |
| `bank_nifty_exc_hist_95`| Integer / Null | Number / Blank | Binary Flag (0 or 1) | Bank Nifty 95% Historical VaR breach flag (null during warmup). |
| `bank_nifty_exc_hist_99`| Integer / Null | Number / Blank | Binary Flag (0 or 1) | Bank Nifty 99% Historical VaR breach flag (null during warmup). |
| `bank_nifty_exc_norm_95`| Integer / Null | Number / Blank | Binary Flag (0 or 1) | Bank Nifty 95% Parametric Normal VaR breach flag (null during warmup). |
| `bank_nifty_exc_norm_99`| Integer / Null | Number / Blank | Binary Flag (0 or 1) | Bank Nifty 99% Parametric Normal VaR breach flag (null during warmup). |

---

## 4. `vol_comparison`

**Purpose**: Comparison of implied volatility (India VIX) with trailing realized volatility and retrospective forward realized volatility to analyze the Volatility Risk Premium (VRP).

| Column Name | Data Type | Excel Type | Physical Unit | Description & Formula |
|:---|:---|:---|:---|:---|
| `date` | String / ISO Date | Date (`d`, `yyyy-mm-dd`) | Trading Day | ISO-8601 NSE trading date. |
| `india_vix_close` | Float | Number | Annualised Points (%) | India VIX closing level ($IV_t$), representing 30-day implied volatility in annualized percentage points (e.g., `15.57`%). |
| `trailing_vol_21d` | Float | Number | Annualised Points (%) | Trailing 21-trading-day annualised realized volatility scaled to percentage points: $100 \times \sigma_{[t-20, t]} \times \sqrt{252}$. |
| `fwd_vol_21d_retrospective` | Float / Null | Number / Blank | Annualised Points (%) | **Retrospective Measure**: Future 21-day realized volatility: $100 \times \sigma_{[t+1, t+21]} \times \sqrt{252}$. Null for the last 21 trading days. |
| `vrp_spread_retrospective` | Float / Null | Number / Blank | Percentage Spread (%) | **Retrospective Measure**: Implied minus future realized volatility spread: $\text{India VIX}_t - \text{fwd\_vol\_21d}_t$. |

---

## 5. `correlations`

**Purpose**: Rolling 60-trading-day Pearson correlation coefficients of NIFTY 50 daily log returns against global benchmarks.

| Column Name | Data Type | Excel Type | Physical Unit | Description & Formula |
|:---|:---|:---|:---|:---|
| `date` | String / ISO Date | Date (`d`, `yyyy-mm-dd`) | Trading Day | ISO-8601 NSE trading date. |
| `corr_sp500` | Float / Null | Number / Blank | Dimensionless $[-1.0, +1.0]$ | Rolling 60-day Pearson correlation between NIFTY 50 and S&P 500 daily log returns. Null during initial 60-day warmup. |
| `corr_brent` | Float / Null | Number / Blank | Dimensionless $[-1.0, +1.0]$ | Rolling 60-day Pearson correlation between NIFTY 50 and Brent crude daily log returns. Null during warmup. |
| `corr_usdinr` | Float / Null | Number / Blank | Dimensionless $[-1.0, +1.0]$ | Rolling 60-day Pearson correlation between NIFTY 50 and USD/INR exchange rate daily log returns. Null during warmup. |
| `corr_us10y` | Float / Null | Number / Blank | Dimensionless $[-1.0, +1.0]$ | Rolling 60-day Pearson correlation between NIFTY 50 and US 10Y Treasury yield daily log changes. Null during warmup. |

---

## 6. `budget_events_summary`

**Purpose**: Event study summary for 9 verified Union and Interim Budgets presented between 2016 and 2024.

| Column Name | Data Type | Excel Type | Physical Unit | Description & Formula |
|:---|:---|:---|:---|:---|
| `event_date` | String / ISO Date | Date (`d`, `yyyy-mm-dd`) | Calendar Date | Calendar date on which the Budget was presented to Parliament. |
| `effective_date` | String / ISO Date | Date (`d`, `yyyy-mm-dd`) | Trading Date | First active NSE trading date on or following the presentation (used as Day 0). |
| `market_closed_on_presentation` | Integer | Number | Binary Flag (0 or 1) | `1` if markets were closed on scheduled date; `0` if market was open. |
| `budget_type` | String | Text | Category | Type of presentation: `'Union Budget'` or `'Interim Budget'`. |
| `finance_minister` | String | Text | Entity Name | Name of the Union Finance Minister presenting the budget. |
| `nifty_day0_ar_pct` | Float | Number | Percentage Points (%) | Day 0 NIFTY 50 Abnormal Return: $AR_{0} = R_0 - \bar{R}_{\text{est}}$. Expressed in percentage points (e.g., `+0.520`). |
| `nifty_car_minus1_plus1_pct` | Float | Number | Percentage Points (%) | Cumulative Abnormal Return over event window $[-1, +1]$: $\sum_{\tau=-1}^{+1} AR_\tau$. Expressed in percentage points. |
| `nifty_car_0_plus5_pct` | Float | Number | Percentage Points (%) | Cumulative Abnormal Return over post-budget drift window $[0, +5]$: $\sum_{\tau=0}^{+5} AR_\tau$. Expressed in percentage points. |
| `bank_nifty_day0_ar_pct` | Float | Number | Percentage Points (%) | Day 0 Bank Nifty Abnormal Return relative to OLS market model: $AR_{0} = R_0 - (\hat{\alpha} + \hat{\beta} R_{m,0})$. Expressed in percentage points. |
| `bank_nifty_car_minus1_plus1_pct` | Float | Number | Percentage Points (%) | Bank Nifty Cumulative Abnormal Return over $[-1, +1]$ in percentage points. |
| `bank_nifty_car_0_plus5_pct` | Float | Number | Percentage Points (%) | Bank Nifty Cumulative Abnormal Return over $[0, +5]$ in percentage points. |
| `vix_day0_change` | Float | Number | Index Points (Net Change) | Change in India VIX closing level from Day -1 close to Day 0 close: $VIX_0 - VIX_{-1}$. E.g., `-1.67` points. |
| `usdinr_day0_change` | Float | Number | INR per USD (Net Change) | Change in USD/INR spot exchange rate from Day -1 to Day 0: $USDINR_0 - USDINR_{-1}$. |
| `notes` | String | Text | Description | Factual notes regarding trading session, timing, or market context. |

---

## 7. `budget_event_paths`

**Purpose**: Granular daily trajectory panel tracking abnormal returns and level changes from $\tau = -5$ to $\tau = +5$ for individual events and the cross-event average.

| Column Name | Data Type | Excel Type | Physical Unit | Description & Formula |
|:---|:---|:---|:---|:---|
| `event_date` | String / Null | Date (`d`) / Blank | Calendar Date | Calendar presentation date for individual events; blank/empty for cross-event `'Average'` rows. |
| `budget_type` | String | Text | Category | Classification: `'Union Budget'`, `'Interim Budget'`, or `'Average'`. |
| `tau` | Integer | Number | Trading Days (Relative) | Relative event day index ranging from `-5` to `+5`, where `0` is the effective event day. |
| `date` | String / Null | Date (`d`) / Blank | Trading Date | Actual calendar date corresponding to relative day $\tau$; blank/empty for `'Average'` rows. |
| `series_label` | String | Text | Legend Label | Series grouping label: event presentation date as text (e.g., `'2016-02-29'`) or `'Average'`. |
| `nifty_ar` | Float | Number | Decimal Fraction | Daily abnormal return for NIFTY 50 on relative day $\tau$: $r_\tau - \bar{r}_{\text{est}}$. E.g., `+0.0052` is $+0.52\%$. |
| `nifty_car` | Float | Number | Decimal Fraction | Cumulative abnormal return for NIFTY 50 from day $-5$ to day $\tau$: $\sum_{s=-5}^{\tau} AR_s$. |
| `bank_nifty_ar` | Float | Number | Decimal Fraction | Daily abnormal return for Bank Nifty from OLS market model regression on day $\tau$. |
| `bank_nifty_car` | Float | Number | Decimal Fraction | Cumulative abnormal return for Bank Nifty from day $-5$ to day $\tau$. |
| `vix_level_change` | Float | Number | Index Points (Net Change) | India VIX index level change relative to Day -1 baseline close: $VIX_\tau - VIX_{-1}$. |
| `usdinr_level_change` | Float | Number | INR per USD (Net Change) | USD/INR exchange rate change relative to Day -1 baseline close: $USDINR_\tau - USDINR_{-1}$. |

---

## 8. `var_backtest`

**Purpose**: Formal regulatory backtest evaluation results for 1-day 95% and 99% Value at Risk models using Kupiec's Proportion of Failures likelihood-ratio test.

| Column Name | Data Type | Excel Type | Physical Unit | Description & Formula |
|:---|:---|:---|:---|:---|
| `asset` | String | Text | Index Name | Asset tested: `'NIFTY 50'` or `'Bank NIFTY'`. |
| `model` | String | Text | VaR Methodology | Risk estimation methodology: `'Historical Simulation'` or `'Parametric Normal'`. |
| `confidence_level` | Float | Number | Probability Fraction | Targeted VaR coverage confidence level: `0.95` ($95\%$) or `0.99` ($99\%$). |
| `total_eval_days` | Integer | Number | Trading Days | Number of out-of-sample evaluation trading days in backtest window ($N = 2,673$). |
| `expected_exceptions` | Float | Number | Count (Expected) | Theoretical expected breach count: $N \times (1 - \alpha)$. E.g., `26.7` days for 99% VaR. |
| `actual_exceptions` | Integer | Number | Count (Observed) | Empirical count of days where actual negative return exceeded the estimated VaR threshold ($x$). |
| `exception_ratio` | Float | Number | Ratio (Dimensionless) | Ratio of actual breaches to expected breaches: $x / [N(1 - \alpha)]$. E.g., `1.873`. |
| `kupiec_lr_stat` | Float | Number | Test Statistic ($\chi^2_1$) | Kupiec unconditional coverage likelihood-ratio statistic: $-2 \ln [ (1-p)^{N-x} p^x / ( (1-\hat{p})^{N-x} \hat{p}^x ) ]$. |
| `p_value` | Float | Number | Probability $[0, 1]$ | Asymptotic p-value from chi-square distribution with 1 degree of freedom: $\mathbb{P}(\chi^2_1 \ge \text{LR})$. |
| `outcome` | String | Text | Hypothesis Decision | Regulatory decision at $\alpha = 0.05$: `'Pass'` if $p \ge 0.05$; `'Reject'` if $p < 0.05$ (indicating underestimation of tail risk). |

---

## 9. `kpi_summary`

**Purpose**: Curated executive summary table of key risk, return, and event performance indicators for instant card visuals in Power BI.

| Column Name | Data Type | Excel Type | Physical Unit | Description & Formula |
|:---|:---|:---|:---|:---|
| `metric` | String | Text | Metric Identifier | Programmatic metric identifier key (e.g., `latest_nifty_close`). |
| `value` | Float | Number | Mixed Units | Numeric value of the metric (see detailed unit per metric in table below). |
| `as_of_date` | String / ISO Date | Date (`d`, `yyyy-mm-dd`) | Calendar Date | Effective as-of date for the metric observation (`2026-11-18` for market data, `2026-02-01` for event data). |
| `source_file` | String | Text | Filename | Primary tidy CSV export file containing the underlying observations. |

### Summary of KPI Metrics and Individual Units

| Metric Identifier | Value in Data | Metric Physical Unit | Source Table | Description |
|:---|:---|:---|:---|:---|
| `latest_nifty_close` | `25227.95` | Index Points (INR) | `market_daily.csv` | Most recent NIFTY 50 closing price level. |
| `latest_daily_log_return` | `-0.006301` | Decimal Fraction | `market_daily.csv` | Most recent single-day continuously compounded log return ($-0.6301\%$). |
| `latest_india_vix` | `15.57` | Points / % Volatility | `market_daily.csv` | Most recent India VIX implied volatility level ($15.57\%$). |
| `latest_trailing_20d_realized_volatility` | `0.1406` | Decimal Fraction (Annualised) | `risk_metrics.csv` | Trailing 20-day annualized realized volatility ($14.06\%$). |
| `current_drawdown` | `-0.0418` | Decimal Fraction | `risk_metrics.csv` | Current percentage decline from all-time cumulative peak ($-4.18\%$). |
| `var_exceptions_99_normal` | `50.0` | Integer Count | `var_backtest.csv` | Total observed exceptions for 99% Parametric Normal VaR on NIFTY 50. |
| `expected_exceptions_99_normal` | `26.7` | Float Count | `var_backtest.csv` | Expected number of exceptions for 99% VaR over 2,673 evaluation days. |
| `kupiec_p_value_99_normal` | `0.0001` | Probability $[0, 1]$ | `var_backtest.csv` | Kupiec POF p-value for 99% Normal VaR ($p < 0.05$ demonstrates normality assumption failure). |
| `average_car_minus1_plus1` | `0.7095` | Percentage Points (%) | `budget_events_summary.csv` | Mean NIFTY 50 Cumulative Abnormal Return across the 9 recent Budgets over $[-1, +1]$. |
| `average_car_0_plus5` | `0.8168` | Percentage Points (%) | `budget_events_summary.csv` | Mean NIFTY 50 Cumulative Abnormal Return across the 9 recent Budgets over $[0, +5]$. |
| `day0_win_rate` | `0.2222` | Decimal Fraction | `budget_events_summary.csv` | Proportion of Budget presentations with positive Day 0 abnormal return (2 of 9 events = $22.2\%$). |
| `average_day0_vix_change` | `-1.1311` | Index Points (Net Change) | `budget_events_summary.csv` | Mean Day 0 change in India VIX closing level (systematic post-event volatility compression). |

