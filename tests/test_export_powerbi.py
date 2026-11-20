"""Unit tests for Power BI tidy CSV export pipeline and Excel workbook.

Validates:
1. Generation and integrity of all 9 tidy CSV tables and Excel workbook in exports/.
2. ISO date format validation (YYYY-MM-DD) and Excel real date types.
3. Dimension and column structure correctness including rebased indices and average paths.
4. Completeness and absence of merged or blank header rows.
5. KPI summary table structure and Excel table definitions.
"""

from __future__ import annotations

import datetime
import os
import re

import openpyxl
import pandas as pd

from src.export_powerbi import export_all_powerbi_tables

ISO_DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def test_export_all_powerbi_tables(tmp_path):
    """Verify export_all_powerbi_tables generates all required CSVs and Excel workbook."""
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
        "kpi_summary",
        "nifty_risk_lab_excel",
    }
    assert set(exported_files.keys()) == expected_tables

    for _, file_path in exported_files.items():
        assert os.path.exists(file_path), f"File {file_path} was not created."
        assert os.path.getsize(file_path) > 0, f"File {file_path} is empty."


def test_market_daily_and_date_table_structure(tmp_path):
    """Verify market_daily.csv and date_table.csv schemas, rebasing, and ISO date format."""
    out_dir = str(tmp_path / "exports")
    export_all_powerbi_tables(output_dir=out_dir)

    # 1. market_daily.csv
    df_market = pd.read_csv(os.path.join(out_dir, "market_daily.csv"))
    assert "date" in df_market.columns
    assert "nifty50_close" in df_market.columns
    assert "nifty50_idx100" in df_market.columns
    assert "bank_nifty_close" in df_market.columns
    assert "bank_nifty_idx100" in df_market.columns
    assert "india_vix_close" in df_market.columns
    assert len(df_market) > 2500

    # Verify rebasing to 100 on first date
    assert abs(df_market["nifty50_idx100"].iloc[0] - 100.0) < 1e-6
    assert abs(df_market["bank_nifty_idx100"].iloc[0] - 100.0) < 1e-6

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
    """Verify budget_events_summary.csv and budget_event_paths.csv with average rows."""
    out_dir = str(tmp_path / "exports")
    export_all_powerbi_tables(output_dir=out_dir)

    # Summary table: 9 rows
    df_summary = pd.read_csv(os.path.join(out_dir, "budget_events_summary.csv"))
    assert len(df_summary) == 9
    assert "event_date" in df_summary.columns
    assert "nifty_car_minus1_plus1_pct" in df_summary.columns
    assert "vix_day0_change" in df_summary.columns

    # Paths table: 9 events * 11 days = 99 rows + 11 average rows = 110 rows
    df_paths = pd.read_csv(os.path.join(out_dir, "budget_event_paths.csv"))
    assert len(df_paths) == 110
    assert "tau" in df_paths.columns
    assert "series_label" in df_paths.columns
    assert set(df_paths["tau"].unique()) == set(range(-5, 6))

    # Check Average rows
    avg_rows = df_paths[df_paths["series_label"] == "Average"]
    assert len(avg_rows) == 11
    assert avg_rows["event_date"].isna().all()
    assert set(avg_rows["tau"].unique()) == set(range(-5, 6))


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


def test_kpi_summary_structure(tmp_path):
    """Verify kpi_summary.csv has all required metrics and columns."""
    out_dir = str(tmp_path / "exports")
    export_all_powerbi_tables(output_dir=out_dir)

    df_kpi = pd.read_csv(os.path.join(out_dir, "kpi_summary.csv"))
    assert list(df_kpi.columns) == ["metric", "value", "as_of_date", "source_file"]
    assert len(df_kpi) == 12

    metrics = set(df_kpi["metric"].tolist())
    expected_metrics = {
        "latest_nifty_close",
        "latest_daily_log_return",
        "latest_india_vix",
        "latest_trailing_20d_realized_volatility",
        "current_drawdown",
        "var_exceptions_99_normal",
        "expected_exceptions_99_normal",
        "kupiec_p_value_99_normal",
        "average_car_minus1_plus1",
        "average_car_0_plus5",
        "day0_win_rate",
        "average_day0_vix_change",
    }
    assert metrics == expected_metrics


def test_excel_workbook_structure(tmp_path):
    """Verify exports/nifty_risk_lab.xlsx has native tables, real dates, and matching sheets."""
    out_dir = str(tmp_path / "exports")
    export_all_powerbi_tables(output_dir=out_dir)

    xlsx_path = os.path.join(out_dir, "nifty_risk_lab.xlsx")
    assert os.path.exists(xlsx_path)

    wb = openpyxl.load_workbook(xlsx_path)
    expected_sheets = [
        "date_table",
        "market_daily",
        "risk_metrics",
        "vol_comparison",
        "correlations",
        "budget_events_summary",
        "budget_event_paths",
        "var_backtest",
        "kpi_summary",
    ]
    assert wb.sheetnames == expected_sheets

    for sheet_name in expected_sheets:
        ws = wb[sheet_name]
        # Verify exactly one table per sheet, named identically
        assert len(ws.tables) == 1, f"Sheet {sheet_name} does not have exactly 1 table"
        assert (
            list(ws.tables.keys())[0] == sheet_name
        ), f"Table name mismatch in {sheet_name}"

        # No merged cells
        assert (
            len(ws.merged_cells.ranges) == 0
        ), f"Sheet {sheet_name} has merged cells"

        # Headers in row 1
        headers = [c.value for c in ws[1]]
        assert None not in headers, f"Sheet {sheet_name} has empty header cell"

        # Row 2 exists
        assert ws.max_row >= 2, f"Sheet {sheet_name} has no data rows"

    # Verify real date cells in market_daily
    ws_market = wb["market_daily"]
    date_val = ws_market["A2"].value
    assert isinstance(date_val, (datetime.date, datetime.datetime))
    assert ws_market["A2"].data_type == "d"

