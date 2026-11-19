# Data Quality & Integrity Report

This report audits the historical market dataset consolidated from Yahoo Finance
for the period **2015-01-01 to present**, using the **NIFTY 50 trading calendar**
as the master calendar.

## 1. Summary of Data Quality Metrics

| Series | Master Days | Missing (Raw) | Filled 1d | Filled 2d | Filled 3d | Total Filled | Unfilled (>3d) | Non-Positive | Stale (>=3d) | 5-Sigma Moves |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **nifty50** | 2924 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 11 |
| **bank_nifty** | 2924 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 13 |
| **india_vix** | 2924 | 17 | 17 | 0 | 0 | 17 | 0 | 0 | 0 | 9 |
| **sp500** | 2924 | 86 | 86 | 0 | 0 | 86 | 0 | 0 | 0 | 11 |
| **brent_crude** | 2924 | 85 | 85 | 0 | 0 | 85 | 0 | 0 | 1 | 9 |
| **usdinr** | 2924 | 7 | 7 | 0 | 0 | 7 | 0 | 0 | 0 | 8 |
| **us10y_yield** | 2924 | 87 | 87 | 0 | 0 | 87 | 0 | 0 | 1 | 13 |

---

## 2. Methodology & Quality Rules

1. **Master Calendar**: The NIFTY 50 trading calendar is the master reference. Days when NSE was closed (weekends, Indian national holidays) are excluded.
2. **3-Day Forward Fill Limit**: Non-Indian series (S&P 500, Brent crude, US 10Y yield) close on dates when Indian markets trade (e.g., US Thanksgiving, Memorial Day, MLK Day). Values are forward-filled for at most 3 consecutive trading days (`ffill(limit=3)`). Any gap exceeding 3 consecutive days remains unfilled (`NaN`).
3. **Fill Tracking**: Every series includes a `<series>_fill_count` column indicating whether the price was observed (`0`) or carried over (`1`, `2`, or `3` days).
4. **No Silent Modification**: Stale prices, non-positive values, and extreme return moves are explicitly logged and tracked in audit tables rather than smoothed.

---

## 3. Detailed 5-Sigma Outlier Return Events

The following trading sessions recorded daily log return moves exceeding 5 standard deviations ($|r_t - \mu| > 5\sigma$):

| Date | Series | Log Return (%) | Z-Score | Close Price | Context / Notes |
| :--- | :--- | :---: | :---: | :---: | :--- |
| 2015-08-24 | nifty50 | -6.10% | -5.99 | 7809.00 | Global market sell-off / China Black Monday |
| 2019-09-20 | nifty50 | +5.18% | +5.03 | 11274.20 | Extreme market volatility |
| 2020-03-12 | nifty50 | -8.67% | -8.50 | 9590.15 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-16 | nifty50 | -7.92% | -7.77 | 9197.40 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-18 | nifty50 | -5.72% | -5.62 | 8468.80 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-20 | nifty50 | +5.67% | +5.50 | 8745.45 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-23 | nifty50 | -13.90% | -13.62 | 7610.25 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-25 | nifty50 | +6.41% | +6.23 | 8317.85 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-04-07 | nifty50 | +8.40% | +8.17 | 8792.20 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-05-04 | nifty50 | -5.92% | -5.82 | 9293.50 | Extreme market volatility |
| 2024-06-04 | nifty50 | -6.11% | -6.01 | 21884.50 | Indian General Election result counting day volatility |
| 2015-08-24 | bank_nifty | -7.15% | -5.27 | 16811.80 | Global market sell-off / China Black Monday |
| 2019-09-20 | bank_nifty | +7.98% | +5.82 | 28981.55 | Extreme market volatility |
| 2020-03-12 | bank_nifty | -9.98% | -7.35 | 23971.15 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-16 | bank_nifty | -8.56% | -6.31 | 23101.15 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-18 | bank_nifty | -7.37% | -5.44 | 20580.20 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-23 | bank_nifty | -18.31% | -13.46 | 16917.65 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-25 | bank_nifty | +7.72% | +5.63 | 18481.05 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-04-07 | bank_nifty | +10.00% | +7.30 | 19062.50 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-05-04 | bank_nifty | -8.68% | -6.39 | 19743.75 | Extreme market volatility |
| 2020-05-18 | bank_nifty | -6.93% | -5.11 | 17573.20 | Extreme market volatility |
| 2020-05-27 | bank_nifty | +7.03% | +5.12 | 18710.55 | Extreme market volatility |
| 2021-02-01 | bank_nifty | +7.93% | +5.79 | 33089.05 | Extreme market volatility |
| 2024-06-04 | bank_nifty | -8.28% | -6.10 | 46928.60 | Indian General Election result counting day volatility |
| 2015-08-24 | india_vix | +49.72% | +9.41 | 28.13 | Global market sell-off / China Black Monday |
| 2016-09-29 | india_vix | +28.68% | +5.43 | 18.45 | Extreme market volatility |
| 2019-05-23 | india_vix | -35.31% | -6.68 | 19.41 | Extreme market volatility |
| 2020-02-28 | india_vix | +26.84% | +5.08 | 23.24 | Extreme market volatility |
| 2020-03-12 | india_vix | +26.56% | +5.02 | 41.16 | Global COVID-19 pandemic market crash / liquidity shock |
| 2022-02-24 | india_vix | +26.48% | +5.01 | 31.98 | Outbreak of Russia-Ukraine war |
| 2024-06-05 | india_vix | -34.79% | -6.58 | 18.89 | Extreme market volatility |
| 2024-08-05 | india_vix | +35.24% | +6.67 | 20.37 | Extreme market volatility |
| 2025-04-07 | india_vix | +50.46% | +9.55 | 22.79 | Extreme market volatility |
| 2020-03-09 | sp500 | -7.90% | -7.12 | 2746.56 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-12 | sp500 | -9.99% | -9.00 | 2480.64 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-13 | sp500 | +8.88% | +7.93 | 2711.02 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-16 | sp500 | -12.77% | -11.49 | 2386.13 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-17 | sp500 | +5.82% | +5.18 | 2529.19 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-24 | sp500 | +8.97% | +8.00 | 2447.33 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-26 | sp500 | +6.05% | +5.39 | 2630.07 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-04-07 | sp500 | +6.64% | +5.91 | 2659.41 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-06-11 | sp500 | -6.08% | -5.49 | 3002.10 | Extreme market volatility |
| 2025-04-04 | sp500 | -6.16% | -5.56 | 5074.08 | Extreme market volatility |
| 2025-04-09 | sp500 | +9.09% | +8.11 | 5456.90 | Extreme market volatility |
| 2019-09-16 | brent_crude | +13.64% | +5.10 | 69.02 | Extreme market volatility |
| 2020-03-09 | brent_crude | -27.58% | -10.33 | 34.36 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-18 | brent_crude | -14.39% | -5.40 | 24.88 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-19 | brent_crude | +13.48% | +5.04 | 28.47 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-04-03 | brent_crude | +32.12% | +12.02 | 34.11 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-04-15 | brent_crude | -13.65% | -5.12 | 27.69 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-04-21 | brent_crude | -27.98% | -10.49 | 19.33 | Global COVID-19 pandemic market crash / liquidity shock |
| 2022-03-09 | brent_crude | -14.11% | -5.29 | 111.14 | Extreme market volatility |
| 2026-04-08 | brent_crude | -14.26% | -5.35 | 94.75 | Extreme market volatility |
| 2018-09-21 | usdinr | -1.93% | -5.10 | 71.72 | Extreme market volatility |
| 2019-08-06 | usdinr | +2.64% | +6.88 | 71.52 | Extreme market volatility |
| 2020-04-03 | usdinr | +2.38% | +6.20 | 77.14 | Global COVID-19 pandemic market crash / liquidity shock |
| 2023-11-02 | usdinr | +2.28% | +5.93 | 85.19 | Extreme market volatility |
| 2023-11-03 | usdinr | -2.31% | -6.09 | 83.25 | Extreme market volatility |
| 2026-04-13 | usdinr | +2.18% | +5.68 | 94.51 | Extreme market volatility |
| 2026-08-26 | usdinr | -2.30% | -6.06 | 93.55 | Extreme market volatility |
| 2026-08-27 | usdinr | +1.99% | +5.19 | 95.43 | Extreme market volatility |
| 2020-03-06 | us10y_yield | -27.13% | -9.25 | 0.71 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-09 | us10y_yield | -34.70% | -11.83 | 0.50 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-11 | us10y_yield | +49.67% | +16.91 | 0.82 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-16 | us10y_yield | -26.72% | -9.11 | 0.73 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-17 | us10y_yield | +31.44% | +10.70 | 1.00 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-18 | us10y_yield | +23.89% | +8.13 | 1.27 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-20 | us10y_yield | -17.64% | -6.02 | 0.94 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-03-23 | us10y_yield | -20.52% | -7.00 | 0.76 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-04-07 | us10y_yield | +22.62% | +7.69 | 0.74 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-04-15 | us10y_yield | -16.04% | -5.47 | 0.64 | Global COVID-19 pandemic market crash / liquidity shock |
| 2020-05-18 | us10y_yield | +15.06% | +5.12 | 0.74 | Extreme market volatility |
| 2020-09-04 | us10y_yield | +14.77% | +5.02 | 0.72 | Extreme market volatility |
| 2020-11-09 | us10y_yield | +15.55% | +5.29 | 0.96 | Extreme market volatility |

---

## 4. Stale Prices and Gaps Analysis

- **Foreign Holidays**: Gaps in `sp500`, `brent_crude`, and `us10y_yield` on Indian trading days coincide strictly with US federal holidays (Independence Day, Labor Day, Thanksgiving, Christmas). These are fully covered within the 3-day forward-fill window.
- **Bank NIFTY & India VIX**: Co-trade on NSE with NIFTY 50 and exhibit virtually zero alignment gaps.
- **USD/INR**: FX trading sessions closely track Indian banking hours with minimal calendar deviations.