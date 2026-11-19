"""Unit tests for Power BI tidy CSV export pipeline.

Validates:
1. Generation and integrity of all 8 tidy CSV tables in exports/.
2. ISO date format validation (YYYY-MM-DD).
3. Dimension and column structure correctness.
4. Completeness and absence of merged or blank header rows.
"""

from __future__ import annotations

import os
import re

import pandas as pd

from src.export_powerbi import export_all_powerbi_tables

ISO_DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def test_export_all_powerbi_tables(tmp_path):
    """Verify export_all_powerbi_tables generates all 8 required tidy CSV files."""
    out_dir = str(tmp_path / "exports")
    exported_files = export_all_powerbi_tables(output_dir=out_dir)

    expected_tables = {
        "market_daily",
        "risk_metrics",
        "vol_comparison",
        "var_backtest",
        "budget_events_summary",
        "budget_event_paths",
        "correlations",
        "date_table",
    }
    assert set(exported_files.keys()) == expected_tables

    for _, file_path in exported_files.items():
        assert os.path.exists(file_path), f"File {file_path} was not created."
        assert os.path.getsize(file_path) > 0, f"File {file_path} is empty."


def test_market_daily_and_date_table_structure(tmp_path):
    """Verify market_daily.csv and date_table.csv schemas and ISO date format."""
    out_dir = str(tmp_path / "exports")
    export_all_powerbi_tables(output_dir=out_dir)

    # 1. market_daily.csv
    df_market = pd.read_csv(os.path.join(out_dir, "market_daily.csv"))
    assert "date" in df_market.columns
    assert "nifty50_close" in df_market.columns
    assert "bank_nifty_close" in df_market.columns
    assert "india_vix_close" in df_market.columns
    assert len(df_market) > 2500

    # Verify all dates are valid ISO format YYYY-MM-DD
    assert df_market["date"].str.match(ISO_DATE_REGEX).all()

    # 2. date_table.csv
    df_date = pd.read_csv(os.path.join(out_dir, "date_table.csv"))
    required_date_cols = [
        "date",
        "year",
        "quarter",
        "quarter_number",
        "month",
        "month_number",
        "year_month",
        "day_of_week",
        "is_trading_day",
        "is_budget_presentation_date",
        "budget_type",
    ]
    for col in required_date_cols:
        assert col in df_date.columns, f"Missing date table column: {col}"

    assert df_date["date"].str.match(ISO_DATE_REGEX).all()
    # Check that budget presentations are flagged
    assert df_date["is_budget_presentation_date"].sum() == 9


def test_budget_exports_structure(tmp_path):
    """Verify budget_events_summary.csv and budget_event_paths.csv."""
    out_dir = str(tmp_path / "exports")
    export_all_powerbi_tables(output_dir=out_dir)

    # Summary table: 9 rows
    df_summary = pd.read_csv(os.path.join(out_dir, "budget_events_summary.csv"))
    assert len(df_summary) == 9
    assert "event_date" in df_summary.columns
    assert "nifty_car_minus1_plus1_pct" in df_summary.columns
    assert "vix_day0_change" in df_summary.columns

    # Paths table: 9 events * 11 days = 99 rows
    df_paths = pd.read_csv(os.path.join(out_dir, "budget_event_paths.csv"))
    assert len(df_paths) == 99
    assert "tau" in df_paths.columns
    assert set(df_paths["tau"].unique()) == set(range(-5, 6))


def test_var_backtest_and_correlations_structure(tmp_path):
    """Verify var_backtest.csv and correlations.csv."""
    out_dir = str(tmp_path / "exports")
    export_all_powerbi_tables(output_dir=out_dir)

    # VaR backtest: 8 rows (2 assets * 2 conf levels * 2 models)
    df_backtest = pd.read_csv(os.path.join(out_dir, "var_backtest.csv"))
    assert len(df_backtest) == 8
    assert set(df_backtest["asset"].unique()) == {"NIFTY 50", "Bank NIFTY"}
    assert set(df_backtest["model"].unique()) == {
        "Historical Simulation",
        "Parametric Normal",
    }
    assert "kupiec_lr_stat" in df_backtest.columns
    assert "p_value" in df_backtest.columns

    # Correlations table: 60d rolling correlations
    df_corr = pd.read_csv(os.path.join(out_dir, "correlations.csv"))
    assert "date" in df_corr.columns
    assert "corr_sp500" in df_corr.columns
    assert "corr_brent" in df_corr.columns
    assert "corr_usdinr" in df_corr.columns
    assert "corr_us10y" in df_corr.columns

    # Values must be within [-1, 1] for non-nulls
    for col in ["corr_sp500", "corr_brent", "corr_usdinr", "corr_us10y"]:
        valid_vals = df_corr[col].dropna()
        assert (valid_vals >= -1.0 - 1e-6).all()
        assert (valid_vals <= 1.0 + 1e-6).all()
