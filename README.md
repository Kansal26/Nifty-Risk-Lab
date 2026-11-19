# nifty-risk-lab

A disciplined, reproducible finance analytics and market risk laboratory in Python focusing on the **NIFTY 50** index and **India VIX**.

Built for rigorous equity risk measurement, volatility dynamics, and market regime analysis without look-ahead bias or synthetic data.

---

## Project Structure

```text
nifty-risk-lab/
├── data/
│   ├── raw/                   # Raw downloaded market data (untouched)
│   │   ├── nifty50_raw.csv
│   │   ├── bank_nifty_raw.csv
│   │   ├── india_vix_raw.csv
│   │   ├── sp500_raw.csv
│   │   ├── brent_crude_raw.csv
│   │   ├── usdinr_raw.csv
│   │   ├── us10y_yield_raw.csv
│   │   └── budget_events.csv      # Verified Union Budget presentation dates
│   └── clean/                 # Master aligned dataset & Power BI export
│       ├── market_daily.parquet
│       ├── market_daily.csv
│       ├── risk_metrics.parquet   # Daily risk analytics & VaR forecasts
│       ├── risk_metrics.csv
│       ├── vix_analysis.parquet   # India VIX vs Realized Vol & VRP spread
│       ├── vix_analysis.csv
│       ├── budget_event_study.parquet # Budget abnormal returns & CARs
│       ├── budget_event_study.csv
│       ├── budget_event_trajectories.parquet # Daily event window panel
│       └── budget_event_trajectories.csv
├── docs/
│   ├── figures/               # High-resolution risk distribution & VaR charts
│   │   ├── returns_distribution.png
│   │   ├── rolling_volatility.png
│   │   ├── drawdown_curve.png
│   │   ├── var_exceptions.png
│   │   ├── vix_vs_trailing_vol.png
│   │   ├── volatility_risk_premium_over_time.png
│   │   ├── vix_vs_forward_realized_scatter.png
│   │   ├── atm_option_greeks_surface.png
│   │   └── budget_event_study_car.png
│   ├── METHODS.md             # Mathematical definitions, Black-Scholes & event study formulas
│   ├── DATA_QUALITY.md        # Audit table of missing, filled, stale, and 5-sigma moves
│   ├── RISK_FINDINGS.md       # VaR backtest analysis, VRP breakdown & tail risk findings
│   ├── EVENT_FINDINGS.md      # Union Budget event study empirical findings & limitations
│   └── PHASE_1_REPORT.md      # Phase 1 delivery report
├── notebooks/
│   └── option_greeks_surface.ipynb # ATM NIFTY option pricing & Greeks surface analysis
├── src/
│   ├── __init__.py
│   ├── download_data.py       # Ingests raw market data from Yahoo Finance
│   ├── clean_data.py          # Calendar alignment, 3-day fill limit, and auditing
│   ├── risk.py                # Volatility, drawdowns, VaR models & backtests
│   ├── vix_analysis.py        # India VIX vs realized vol, VRP spread & scatter analysis
│   ├── options.py             # European option pricing, Greeks, and implied vol solver
│   └── event_study.py         # Union Budget event study, CAR analysis & market models
├── tests/
│   ├── test_data_pipeline.py  # Tests for unique dates, sorting, alignment, and fill limit
│   ├── test_risk_metrics.py   # Hand-calculated tests for drawdowns, volatility, and VaR
│   ├── test_vix_comparison.py # Tests for trailing/forward realized volatility and VRP
│   ├── test_options.py        # Tests for Hull benchmark, put-call parity, finite diffs & IV
│   └── test_event_study.py    # Tests for market model OLS, synthetic ARs & calendar roll
├── pyproject.toml             # Ruff and Pytest configurations
├── requirements.txt           # Minimal pinned dependencies
└── README.md
```

---

## Quickstart

```bash
# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run tests & lint checks
ruff check .
pytest -v

# Run complete pipeline
python -m src.download_data
python -m src.clean_data
python -m src.risk
python -m src.vix_analysis
python -m src.event_study
```

For mathematical formulas and assumptions, see [METHODS.md](docs/METHODS.md).  
For the data quality audit, see [DATA_QUALITY.md](docs/DATA_QUALITY.md).  
For risk analytics, VaR backtests & VRP findings, see [RISK_FINDINGS.md](docs/RISK_FINDINGS.md).  
For Union Budget event study findings & limitations, see [EVENT_FINDINGS.md](docs/EVENT_FINDINGS.md).  
For option pricing and Greeks surfaces, see [option_greeks_surface.ipynb](notebooks/option_greeks_surface.ipynb).
