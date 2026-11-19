"""Unit tests for Phase 1 Data Ingestion, Cleaning, and Returns Pipeline.

Verifies:
1. Mathematical correctness of log return calculations and time additivity.
2. VIX daily implied volatility formula.
3. Annualisation factor (sqrt(252)).
4. Rejection of invalid/negative price anomalies.
5. Chronological alignment and avoidance of look-ahead leakage.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.clean_data import (
    ANNUALISATION_FACTOR,
    clean_price_series,
    compute_nifty_returns,
    compute_vix_metrics,
    merge_nifty_and_vix,
)


def test_log_return_formula_and_additivity() -> None:
    """Verify log return formula: r_t = ln(P_t) - ln(P_{t-1}) and multi-period additivity."""
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    prices = [100.0, 105.0, 102.9, 110.0]
    df = pd.DataFrame({"Date": dates, "Close": prices})

    res = compute_nifty_returns(df)

    # First return must be NaN
    assert pd.isna(res.loc[0, "log_return"])

    # r_1 = ln(105 / 100)
    expected_r1 = np.log(105.0 / 100.0)
    assert np.isclose(res.loc[1, "log_return"], expected_r1, atol=1e-10)

    # r_2 = ln(102.9 / 105.0)
    expected_r2 = np.log(102.9 / 105.0)
    assert np.isclose(res.loc[2, "log_return"], expected_r2, atol=1e-10)

    # Multi-period additivity check: sum(r_t) == ln(P_T / P_0)
    total_log_return = res["log_return"].dropna().sum()
    expected_cumulative = np.log(prices[-1] / prices[0])
    assert np.isclose(total_log_return, expected_cumulative, atol=1e-10)


def test_vix_daily_implied_formula() -> None:
    """Verify VIX daily implied formula: sigma_daily = (VIX / 100) / sqrt(252)."""
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    # Choose VIX = 100 * sqrt(252) * 0.01 so daily implied is exactly 0.01 (1%)
    target_daily = 0.01
    vix_value = target_daily * 100.0 * ANNUALISATION_FACTOR
    df = pd.DataFrame({"Date": dates, "Close": [vix_value, vix_value + 1.0]})

    res = compute_vix_metrics(df)

    assert np.isclose(res.loc[0, "vix_daily_implied"], target_daily, atol=1e-10)
    assert np.isclose(res.loc[1, "vix_change"], 1.0, atol=1e-10)


def test_annualisation_factor_value() -> None:
    """Verify the annualisation factor sqrt(252) equals ~15.8745."""
    expected = np.sqrt(252)
    assert np.isclose(ANNUALISATION_FACTOR, expected, atol=1e-10)
    assert np.isclose(ANNUALISATION_FACTOR, 15.874507866387544, atol=1e-6)


def test_clean_price_series_validates_positivity() -> None:
    """Verify that non-positive prices trigger a ValueError."""
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    df_invalid = pd.DataFrame({"Date": dates, "Close": [100.0, -5.0, 102.0]})

    with pytest.raises(ValueError, match="non-positive price"):
        clean_price_series(df_invalid, "TEST_TICKER")


def test_clean_price_series_deduplicates_and_sorts() -> None:
    """Verify date deduplication and ascending chronological ordering."""
    dates = [
        pd.Timestamp("2024-01-03"),
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-01"),  # Duplicate
        pd.Timestamp("2024-01-02"),
    ]
    df = pd.DataFrame({"Date": dates, "Close": [103.0, 101.0, 999.0, 102.0]})

    cleaned = clean_price_series(df, "TEST_TICKER")

    assert len(cleaned) == 3
    assert list(cleaned["Date"]) == [
        pd.Timestamp("2024-01-01"),
        pd.Timestamp("2024-01-02"),
        pd.Timestamp("2024-01-03"),
    ]
    # Retained the first occurrence of 2024-01-01
    assert cleaned.loc[0, "Close"] == 101.0


def test_merge_no_lookahead_and_alignment() -> None:
    """Verify inner join on Date with no forward-looking leaks."""
    dates_nifty = pd.date_range("2024-01-01", periods=5, freq="D")
    dates_vix = pd.date_range("2024-01-02", periods=5, freq="D")

    nifty_df = pd.DataFrame({
        "Date": dates_nifty,
        "Open": [100.0] * 5,
        "High": [105.0] * 5,
        "Low": [95.0] * 5,
        "Close": [100.0, 102.0, 101.0, 104.0, 103.0],
        "Volume": [1000] * 5,
    })
    nifty_df = compute_nifty_returns(clean_price_series(nifty_df, "NIFTY"))

    vix_df = pd.DataFrame({
        "Date": dates_vix,
        "Open": [15.0] * 5,
        "High": [16.0] * 5,
        "Low": [14.0] * 5,
        "Close": [15.0, 15.5, 14.8, 15.2, 16.0],
    })
    vix_df = compute_vix_metrics(clean_price_series(vix_df, "VIX"))

    merged = merge_nifty_and_vix(nifty_df, vix_df)

    # Dates should only be the overlapping days where both have valid t and t-1 data
    for d in merged["Date"]:
        assert d in dates_nifty
        assert d in dates_vix

    # Ensure strictly sorted by date ascending
    assert (merged["Date"].diff().dropna() > pd.Timedelta(0)).all()


def test_processed_clean_files_if_present() -> None:
    """Validate data integrity of generated clean datasets if available on disk."""
    from pathlib import Path

    clean_merged_path = Path("data/clean/nifty_vix_daily.csv")
    if not clean_merged_path.exists():
        pytest.skip("Processed dataset not yet generated on disk.")

    df = pd.read_csv(clean_merged_path)
    assert not df.empty
    assert (df["nifty_close"] > 0).all()
    assert (df["vix_close"] > 0).all()
    assert df["Date"].is_monotonic_increasing
    assert df.isna().sum().sum() == 0

