# Phase 1 Completion Report: Data Ingestion, Cleaning & Log Returns

## 1. What Was Built
- **`src/download_data.py`**:
  - Ingestion module that fetches daily historical OHLCV data for NIFTY 50 (`^NSEI`) and India VIX (`^INDIAVIX`) via `yfinance`.
  - Halts execution with explicit errors if remote sources fail or deliver empty records (enforcing Rule 1: No synthetic data).
  - Executable standalone via `python -m src.download_data`.
- **`src/clean_data.py`**:
  - Sanitizes timestamps to normalized calendar dates (`YYYY-MM-DD`).
  - Audits for price positivity ($P_t > 0$) and deduplicates non-unique timestamps.
  - Computes daily continuously compounded log returns: $r_t = \ln(P_t) - \ln(P_{t-1})$.
  - Computes daily implied volatility for India VIX: $\sigma_{\text{daily, implied}} = \frac{\text{VIX}_t}{100 \times \sqrt{252}}$.
  - Joins both series on aligned trading dates using an inner join without look-ahead interpolation or future-filling.
  - Stores outputs in `data/clean/nifty50_clean.csv`, `data/clean/india_vix_clean.csv`, and `data/clean/nifty_vix_daily.csv`.
  - Executable standalone via `python -m src.clean_data`.
- **`tests/test_data_pipeline.py`**:
  - 7 unit tests verifying log return calculations, time additivity, VIX daily implied conversions, annualisation factor ($\sqrt{252}$), rejection of negative prices, sorting/deduplication, point-in-time date alignment, and dataset hygiene.
- **`docs/METHODS.md`**:
  - Detailed documentation of all mathematical definitions, return conventions, and anti-lookahead rules.

---

## 2. Data Sources & Summary Statistics

- **Index Ticker**: `^NSEI` (National Stock Exchange of India, NIFTY 50 Index).
- **Volatility Ticker**: `^INDIAVIX` (India Volatility Index).
- **Download Horizon**: `2015-01-01` to `2026-11-18`.
- **Clean Overlapping Observations**: **2,906 trading days** (zero missing/null entries).

### Clean Series Summary
| Metric | NIFTY 50 Close | NIFTY 50 Daily Log Return | India VIX Close |
| :--- | :--- | :--- | :--- |
| **Count** | 2,906 | 2,906 | 2,906 |
| **Mean** | — | +0.0371% (3.71 bps/day) | 16.54 |
| **Std Dev** | — | 1.025% (~16.27% p.a.) | 6.03 |
| **Min** | 6,869.80 | -13.90% (2020-03-23) | 9.15 |
| **25%** | 10,740.34 | -0.44% | 13.15 |
| **50% (Median)**| 14,755.80 | +0.05% | 15.30 |
| **75%** | 18,349.70 | +0.58% | 18.27 |
| **Max** | 26,216.05 | +8.40% (2020-04-07) | 83.61 (2020-03-24) |

---

## 3. Assumptions
1. **Trading Year Length**: 252 trading days per calendar year for annualising daily volatility ($\sqrt{252} \approx 15.8745$).
2. **Log Return Additivity**: Multi-day compounded return equals the sum of intermediate daily log returns ($\sum r_t = \ln(P_T / P_0)$).
3. **Point-in-Time Alignment**: A trading date $t$ reflects market close at date $t$. Only date-matched pairs are merged; missing days in either series are excluded without forward-filling.

---

## 4. Known Limitations
1. **Third-Party API Nuances**: Yahoo Finance serves daily end-of-day quotes which may exhibit occasional restatements or slight settlement differences compared to official NSE end-of-day bhavcopy files.
2. **Historical Corporate Actions**: NIFTY 50 index prices reflect divisor adjustments performed by the index provider; dividends are not reinvested in the benchmark index price series (NIFTY 50 Total Return Index / TRI would be needed for total return dividend inclusion).

---

## 5. Commands to Reproduce Phase 1 From Scratch

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Run linting & code formatting checks
ruff check .

# 3. Run unit and pipeline tests
pytest -v

# 4. Ingest raw data from Yahoo Finance
python -m src.download_data

# 5. Clean, validate, and compute log returns
python -m src.clean_data
```
