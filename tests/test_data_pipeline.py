"""Unit and integration tests for Phase 1 Data Pipeline.

Verifies:
1. No duplicate dates in cleaned or aligned datasets.
2. Strictly sorted chronological index.
3. Absence of negative prices / validation of price positivity.
4. Calendar alignment with NIFTY 50 master trading calendar.
5. Strict 3-day forward-fill limit (unfilled beyond 3 days).
6. Mathematical accuracy of log returns and additivity.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.clean_data import (
    align_series_with_fill_limit,
    audit_series_quality,
    clean_raw_series,
)


def test_no_duplicate_dates() -> None:
    """Ensure duplicate dates are eliminated and preserved uniquely."""
    dates = [
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-01"),  # Duplicate
        pd.Timestamp("2024-01-03"),
    ]
    raw = pd.DataFrame({"Date": dates, "Close": [102.0, 100.0, 999.0, 103.0]})
    cleaned = clean_raw_series(raw, "test_dup")

    assert cleaned["Date"].is_unique
    assert len(cleaned) == 3
    # Keeps first occurrence
    assert cleaned.loc[cleaned["Date"] == pd.Timestamp("2024-01-01"), "Close"].iloc[0] == 100.0


def test_sorted_index() -> None:
    """Ensure cleaned series and master calendar are strictly monotonically increasing."""
    dates = [
        pd.Timestamp("2024-01-05"),
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-03"),
    ]
    raw = pd.DataFrame({"Date": dates, "Close": [105.0, 102.0, 103.0]})
    cleaned = clean_raw_series(raw, "test_sort")

    assert cleaned["Date"].is_monotonic_increasing
    assert list(cleaned["Date"]) == [
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-03"),
        pd.Timestamp("2024-01-05"),
    ]


def test_no_negative_prices() -> None:
    """Ensure non-positive prices are detected and flagged in audit."""
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    df = pd.DataFrame({
        "Date": dates,
        "test_asset_close": [100.0, -5.0, 0.0, 105.0],
        "test_asset_log_return": [0.0, np.nan, np.nan, 0.05],
    })

    stats, _ = audit_series_quality(df, "test_asset")
    assert stats["non_positive_count"] == 2


def test_calendar_alignment() -> None:
    """Ensure series aligns strictly to master calendar dates without foreign day leakage."""
    # Master calendar has 5 Indian trading days
    master_dates = pd.date_range("2024-01-01", periods=5, freq="B")

    # Foreign series has some overlapping days, some missing, and some extra foreign-only days
    foreign_dates = [
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-06"),  # Saturday (not in master)
        pd.Timestamp("2024-01-07"),  # Sunday (not in master)
    ]
    foreign_df = pd.DataFrame({"Date": foreign_dates, "Close": [100.0, 102.0, 104.0, 105.0]})

    aligned, _ = align_series_with_fill_limit(
        foreign_df, pd.Series(master_dates), "foreign_asset", max_fill_limit=3
    )

    # Dates in aligned dataset must exactly match master calendar
    assert len(aligned) == len(master_dates)
    assert (aligned["Date"] == master_dates).all()
    # Foreign weekend dates must not be present
    assert pd.Timestamp("2024-01-06") not in aligned["Date"].values


def test_fill_limit_max_3_days() -> None:
    """Verify that forward-filling strictly stops after 3 consecutive days."""
    master_dates = pd.date_range("2024-01-01", periods=6, freq="D")

    # Foreign series only observed on Day 0 (2024-01-01)
    # Days 1, 2, 3 should be forward-filled (fill_count = 1, 2, 3)
    # Days 4, 5 must remain NaN (unfilled, fill_count > 3)
    foreign_df = pd.DataFrame({
        "Date": [pd.Timestamp("2024-01-01")],
        "Close": [200.0],
    })

    aligned, summary = align_series_with_fill_limit(
        foreign_df, pd.Series(master_dates), "test_fill", max_fill_limit=3
    )

    # Day 0: observed
    assert aligned.loc[0, "test_fill_close"] == 200.0
    assert aligned.loc[0, "test_fill_fill_count"] == 0

    # Day 1: filled 1 day
    assert aligned.loc[1, "test_fill_close"] == 200.0
    assert aligned.loc[1, "test_fill_fill_count"] == 1

    # Day 2: filled 2 days
    assert aligned.loc[2, "test_fill_close"] == 200.0
    assert aligned.loc[2, "test_fill_fill_count"] == 2

    # Day 3: filled 3 days
    assert aligned.loc[3, "test_fill_close"] == 200.0
    assert aligned.loc[3, "test_fill_fill_count"] == 3

    # Day 4: exceeds limit -> NaN
    assert pd.isna(aligned.loc[4, "test_fill_close"])
    assert aligned.loc[4, "test_fill_fill_count"] == 4

    # Day 5: exceeds limit -> NaN
    assert pd.isna(aligned.loc[5, "test_fill_close"])
    assert aligned.loc[5, "test_fill_fill_count"] == 5

    assert summary["filled_1d"] == 1
    assert summary["filled_2d"] == 1
    assert summary["filled_3d"] == 1
    assert summary["unfilled_after_limit"] == 2


def test_log_return_and_additivity() -> None:
    """Verify log return formula: r_t = ln(P_t) - ln(P_{t-1}) and additivity."""
    prices = [100.0, 105.0, 102.9]
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    df = pd.DataFrame({"Date": dates, "Close": prices})

    aligned, _ = align_series_with_fill_limit(df, pd.Series(dates), "asset", max_fill_limit=3)

    # First return is NaN
    assert pd.isna(aligned.loc[0, "asset_log_return"])

    # r_1 = ln(105 / 100)
    expected_r1 = np.log(105.0 / 100.0)
    assert np.isclose(aligned.loc[1, "asset_log_return"], expected_r1, atol=1e-10)

    # Cumulative return additivity: sum(r_t) == ln(P_T / P_0)
    cum_ret = aligned["asset_log_return"].dropna().sum()
    expected_cum = np.log(prices[-1] / prices[0])
    assert np.isclose(cum_ret, expected_cum, atol=1e-10)


def test_market_daily_clean_files_if_present() -> None:
    """Validate data integrity of generated clean files if present on disk."""
    parquet_path = Path("data/clean/market_daily.parquet")
    csv_path = Path("data/clean/market_daily.csv")

    if not parquet_path.exists():
        pytest.skip("market_daily.parquet not yet generated on disk.")

    df = pd.read_parquet(parquet_path)
    assert not df.empty
    assert "Date" in df.columns
    assert df["Date"].is_monotonic_increasing
    assert df["Date"].is_unique

    # Verify Nifty 50 close price is positive and has no fills (master calendar)
    assert (df["nifty50_close"] > 0).all()
    assert (df["nifty50_fill_count"] == 0).all()

    # Verify fill limit: any filled price has fill_count <= 3
    for series in ["sp500", "brent_crude", "usdinr", "us10y_yield"]:
        fill_col = f"{series}_fill_count"
        close_col = f"{series}_close"
        if fill_col in df.columns:
            # If close is not null, fill_count must be <= 3
            filled_rows = df[df[close_col].notna()]
            assert (filled_rows[fill_col] <= 3).all()

    if csv_path.exists():
        df_csv = pd.read_csv(csv_path)
        assert len(df_csv) == len(df)
