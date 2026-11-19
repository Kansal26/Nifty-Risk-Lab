# nifty-risk-lab

A disciplined, reproducible finance analytics and market risk laboratory in Python focusing on the **NIFTY 50** index and **India VIX**.

Built for rigorous equity risk measurement, volatility dynamics, and market regime analysis without look-ahead bias or synthetic data.

---

## Project Structure

```text
nifty-risk-lab/
├── data/
│   ├── raw/                   # Raw downloaded market data
│   │   ├── nifty50_raw.csv
│   │   └── india_vix_raw.csv
│   └── clean/                 # Validated datasets with log returns and aligned dates
│       ├── nifty50_clean.csv
│       ├── india_vix_clean.csv
│       └── nifty_vix_daily.csv
├── docs/
│   ├── METHODS.md             # Mathematical definitions and econometric formulas
│   └── PHASE_1_REPORT.md      # Phase 1 delivery report
├── src/
│   ├── __init__.py
│   ├── download_data.py       # Ingests raw market data from Yahoo Finance
│   └── clean_data.py          # Data sanitation, return computation, and alignment
├── tests/
│   └── test_data_pipeline.py  # Automated tests for formulas and data hygiene
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

# Run data pipeline
python -m src.download_data
python -m src.clean_data
```

For mathematical formulas and assumptions, see [METHODS.md](docs/METHODS.md).  
For the Phase 1 report, see [PHASE_1_REPORT.md](docs/PHASE_1_REPORT.md).
