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
│   │   └── us10y_yield_raw.csv
│   └── clean/                 # Master aligned dataset & Power BI export
│       ├── market_daily.parquet
│       ├── market_daily.csv
│       ├── risk_metrics.parquet   # Daily risk analytics & VaR forecasts
│       └── risk_metrics.csv
├── docs/
│   ├── figures/               # High-resolution risk distribution & VaR charts
│   │   ├── returns_distribution.png
│   │   ├── rolling_volatility.png
│   │   ├── drawdown_curve.png
│   │   └── var_exceptions.png
│   ├── METHODS.md             # Mathematical definitions and econometric formulas
│   ├── DATA_QUALITY.md        # Audit table of missing, filled, stale, and 5-sigma moves
│   ├── RISK_FINDINGS.md       # VaR backtest analysis and tail risk findings
│   └── PHASE_1_REPORT.md      # Phase 1 delivery report
├── src/
│   ├── __init__.py
│   ├── download_data.py       # Ingests raw market data from Yahoo Finance
│   ├── clean_data.py          # Calendar alignment, 3-day fill limit, and auditing
│   └── risk.py                # Volatility, drawdowns, VaR models & backtests
├── tests/
│   ├── test_data_pipeline.py  # Tests for unique dates, sorting, alignment, and fill limit
│   └── test_risk_metrics.py   # Hand-calculated tests for drawdowns, volatility, and VaR
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
```

For mathematical formulas and assumptions, see [METHODS.md](docs/METHODS.md).  
For the data quality audit, see [DATA_QUALITY.md](docs/DATA_QUALITY.md).  
For risk analytics & VaR backtest results, see [RISK_FINDINGS.md](docs/RISK_FINDINGS.md).
