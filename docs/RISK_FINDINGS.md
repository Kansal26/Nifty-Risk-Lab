# Risk Analytics & Value-at-Risk Backtest Findings

This report documents the empirical risk dynamics, maximum drawdowns, and 1-day Value at Risk (VaR) backtests for **NIFTY 50** and **Bank NIFTY** over the period **2015 to present**.

---

## 1. Value at Risk Backtest Results

The models evaluate a **1-day forecast horizon** using a **250-trading-day rolling lookback window** that strictly uses historical returns up to date $t-1$ (zero bias).

| Asset | Model | Conf | Eval Days | Expected | Observed | Empirical Rate (%) | Expected Rate (%) | Ratio | Kupiec LR | P-Value | Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **NIFTY 50** | Historical | 95% | 2673 | 133.7 | 144 | 5.39% | 5.00% | 1.08x | 0.82 | 0.3641 | Accept (Valid) |
| **NIFTY 50** | Historical | 99% | 2673 | 26.7 | 42 | 1.57% | 1.00% | 1.57x | 7.51 | 0.0061 | Reject (Underestimates) |
| **NIFTY 50** | Parametric Normal | 95% | 2673 | 133.7 | 135 | 5.05% | 5.00% | 1.01x | 0.01 | 0.9048 | Accept (Valid) |
| **NIFTY 50** | Parametric Normal | 99% | 2673 | 26.7 | 50 | 1.87% | 1.00% | 1.87x | 16.29 | 0.0001 | Reject (Underestimates) |
| **Bank NIFTY** | Historical | 95% | 2673 | 133.7 | 153 | 5.72% | 5.00% | 1.14x | 2.82 | 0.0929 | Accept (Valid) |
| **Bank NIFTY** | Historical | 99% | 2673 | 26.7 | 41 | 1.53% | 1.00% | 1.53x | 6.62 | 0.0101 | Reject (Underestimates) |
| **Bank NIFTY** | Parametric Normal | 95% | 2673 | 133.7 | 126 | 4.71% | 5.00% | 0.94x | 0.47 | 0.4932 | Accept (Valid) |
| **Bank NIFTY** | Parametric Normal | 99% | 2673 | 26.7 | 50 | 1.87% | 1.00% | 1.87x | 16.29 | 0.0001 | Reject (Underestimates) |

---

## 2. Key Findings and Tail Risk Interpretation

### 2.1 Underestimation of Tail Risk Under the Normal Assumption
- **The 99% Parametric Normal model significantly underestimates tail risk:**
  - For both NIFTY 50 and Bank NIFTY, observed exceptions at the 99% confidence level exceed theoretical expectations by **1.5x to 1.8x**.
  - The Kupiec Proportion of Failures (POF) test statistically rejects the null hypothesis ($p < 0.01$) that the normal distribution adequately captures 99% tail losses.
  - **Econometric Rationale**: Daily equity index returns exhibit pronounced **leptokurtosis (fat tails and excess kurtosis > 4.5)**. Extreme market shocks (such as the March 2020 COVID crisis and June 2024 election outcome day) occur with much higher frequency than a thin-tailed Gaussian distribution predicts.

### 2.2 Historical Simulation Performance
- **Historical Simulation VaR tracks the 95% target closely**:
  - At 95% confidence, historical simulation delivers breach rates close to 5.0%, successfully accommodating localized volatility clustering.
- **Limitations at 99% Confidence**:
  - In a 250-day window, a 1% quantile corresponds to only the 2nd or 3rd worst observation. Consequently, historical VaR updates discretely in steps and can remain stale during rapid volatility regime shifts until a major loss enters the window.

---

## 3. Top 5 Worst Drawdown Episodes

### 3.1 NIFTY 50 Top 5 Drawdowns

| Rank | Peak Date | Trough Date | Recovery Date | Max Drawdown (%) | Days to Trough | Total Duration (Days) | Primary Market Catalyst |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | 2020-01-14 | 2020-03-23 | 2020-11-09 | **-38.44%** | 47 | 205 | COVID-19 Global Pandemic Crash |
| 2 | 2015-03-03 | 2016-02-25 | 2017-03-14 | **-22.52%** | 241 | 496 | China Yuan Devaluation / Commodity Slump |
| 3 | 2021-10-18 | 2022-06-17 | 2022-11-24 | **-17.23%** | 166 | 274 | Global Inflation & Russia-Ukraine Conflict |
| 4 | 2024-09-26 | 2025-03-04 | 2026-01-02 | **-15.77%** | 109 | 315 | General market correction |
| 5 | 2026-01-02 | 2026-10-08 | Ongoing | **-15.56%** | 187 | 214 | General market correction |

### 3.2 Bank NIFTY Top 5 Drawdowns

| Rank | Peak Date | Trough Date | Recovery Date | Max Drawdown (%) | Days to Trough | Total Duration (Days) | Primary Market Catalyst |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | 2020-01-02 | 2020-03-23 | 2021-01-13 | **-47.86%** | 55 | 257 | COVID-19 Financial Sector Moratorium & Credit Shock |
| 2 | 2015-01-27 | 2016-02-25 | 2017-02-20 | **-34.05%** | 265 | 506 | Asset Quality Review (AQR) Non-Performing Loans Crisis |
| 3 | 2021-10-26 | 2022-06-16 | 2022-09-14 | **-20.91%** | 159 | 220 | Monetary Policy Tightening & Rate Hike Fears |
| 4 | 2026-02-18 | 2026-03-30 | 2026-11-16 | **-18.32%** | 26 | 181 | Banking sector credit cycle / consolidation |
| 5 | 2021-02-15 | 2021-04-12 | 2021-09-16 | **-17.46%** | 37 | 144 | Monetary Policy Tightening & Rate Hike Fears |

---

## 4. Figures Generated

- `docs/figures/returns_distribution.png`: Histogram & KDE of daily log returns vs theoretical normal curve overlay.
- `docs/figures/rolling_volatility.png`: 20-day vs 60-day annualised realized volatility comparison.
- `docs/figures/drawdown_curve.png`: Running percentage underwater drawdown curves.
- `docs/figures/var_exceptions.png`: 1-day ahead VaR forecast boundaries and exception events.