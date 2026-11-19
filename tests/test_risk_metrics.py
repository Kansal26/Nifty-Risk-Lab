"""Unit tests for Phase 2 Risk Metrics module.

Verifies:
1. Running maximum drawdown and discrete episode identification using hand-calculated examples.
2. Rolling realized volatility with sqrt(252) annualisation against hand-calculated values.
3. Parametric Normal VaR against hand-calculated formulas.
4. Historical Simulation VaR quantile calculation.
5. Strict zero look-ahead bias (VaR at t is completely invariant to return at t).
6. VaR backtest exception counting and breach ratios.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.risk import (
    ANNUALISATION_FACTOR,
    Z_95,
    Z_99,
    backtest_var,
    compute_drawdown_series,
    compute_rolling_realized_volatility,
    compute_rolling_var,
    identify_top_drawdowns,
)


def test_drawdown_hand_calculated() -> None:
    """Verify drawdown calculation on a hand-calculated 5-day series:

    Prices: [100.0, 120.0, 90.0, 108.0, 130.0]
    Peak:   [100.0, 120.0, 120.0, 120.0, 130.0]
    DD:     [0.0,   0.0,   -0.25, -0.10, 0.0]
    """
    prices = pd.Series([100.0, 120.0, 90.0, 108.0, 130.0])
    peak, dd = compute_drawdown_series(prices)

    expected_peaks = [100.0, 120.0, 120.0, 120.0, 130.0]
    expected_dds = [0.0, 0.0, -0.25, -0.10, 0.0]

    np.testing.assert_allclose(peak.to_numpy(), expected_peaks, atol=1e-10)
    np.testing.assert_allclose(dd.to_numpy(), expected_dds, atol=1e-10)


def test_identify_top_drawdowns_hand_calculated() -> None:
    """Verify discrete drawdown episode identification from peak to recovery:

    Cycle: Peak at Day 1 (120), Trough at Day 2 (90), Recovery at Day 4 (130).
    Depth = (90 - 120) / 120 = -0.25 (-25%).
    """
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    prices = pd.Series([100.0, 120.0, 90.0, 108.0, 130.0])

    episodes = identify_top_drawdowns(dates.to_series(), prices, top_n=1)
    assert len(episodes) == 1

    ep = episodes[0]
    assert ep["peak_date"] == "2024-01-02"
    assert ep["trough_date"] == "2024-01-03"
    assert ep["recovery_date"] == "2024-01-05"
    assert math.isclose(ep["drawdown_pct"], -0.25, abs_tol=1e-10)
    assert ep["peak_price"] == 120.0
    assert ep["trough_price"] == 90.0
    assert ep["days_to_trough"] == 1
    assert ep["total_days"] == 3


def test_rolling_volatility_hand_calculated() -> None:
    """Verify rolling volatility on hand-calculated 3-period window:

    Returns: [0.01, -0.02, 0.04]
    Mean: 0.01
    Deviations: [0.0, -0.03, 0.03]
    Sum squared dev: 0.0018
    Sample variance (N-1=2): 0.0009
    Sample std: 0.03
    Annualised vol: 0.03 * sqrt(252)
    """
    returns = pd.Series([0.01, -0.02, 0.04])
    vol = compute_rolling_realized_volatility(returns, window=3)

    assert pd.isna(vol.iloc[0])
    assert pd.isna(vol.iloc[1])

    expected_ann_vol = 0.03 * ANNUALISATION_FACTOR
    assert math.isclose(vol.iloc[2], expected_ann_vol, abs_tol=1e-10)


def test_parametric_var_hand_calculated() -> None:
    """Verify parametric normal VaR formula:

    mu = 0.01, sigma = 0.03
    VaR_95 = mu + Z_95 * sigma = 0.01 - 1.6448536... * 0.03
    VaR_99 = mu + Z_99 * sigma = 0.01 - 2.3263478... * 0.03
    """
    returns = pd.Series([0.01, -0.02, 0.04, 0.00])
    # window = 3
    # Rolling window shifted by 1 means at index 3, it sees returns from index [0, 1, 2]
    _, _, vn95, vn99 = compute_rolling_var(returns, window=3)

    expected_95 = 0.01 + Z_95 * 0.03
    expected_99 = 0.01 + Z_99 * 0.03

    assert math.isclose(vn95.iloc[3], expected_95, abs_tol=1e-10)
    assert math.isclose(vn99.iloc[3], expected_99, abs_tol=1e-10)


def test_var_zero_lookahead_bias() -> None:
    """Verify that VaR at date t is strictly invariant to the realized return at date t."""
    # Base series
    np.random.seed(42)
    r_base = pd.Series(np.random.normal(0.001, 0.01, 300))
    vh95_base, _, vn95_base, _ = compute_rolling_var(r_base, window=250)

    # Modify return on day 260
    r_modified = r_base.copy()
    r_modified.iloc[260] = -0.20  # catastrophic crash on day 260

    vh95_mod, _, vn95_mod, _ = compute_rolling_var(r_modified, window=250)

    # VaR on day 260 MUST BE IDENTICAL because day 260 forecast only uses data up to day 259
    assert math.isclose(vh95_base.iloc[260], vh95_mod.iloc[260], abs_tol=1e-12)
    assert math.isclose(vn95_base.iloc[260], vn95_mod.iloc[260], abs_tol=1e-12)

    # VaR on day 261 SHOULD change because day 260's crash now enters the rolling lookback
    assert not math.isclose(vh95_base.iloc[261], vh95_mod.iloc[261], abs_tol=1e-5)
    assert not math.isclose(vn95_base.iloc[261], vn95_mod.iloc[261], abs_tol=1e-5)


def test_backtest_var_hand_calculated() -> None:
    """Verify backtesting exception count on hand-calculated numbers:

    Actual:    [-0.04, -0.01, -0.06,  0.02]
    Threshold: [-0.03, -0.03, -0.03, -0.03]
    Breaches: Day 0 (-0.04 < -0.03) and Day 2 (-0.06 < -0.03) -> 2 breaches
    Total days = 4 -> Exception rate = 50%
    """
    actual = pd.Series([-0.04, -0.01, -0.06, 0.02])
    threshold = pd.Series([-0.03, -0.03, -0.03, -0.03])

    res = backtest_var(actual, threshold, confidence_level=0.95)

    assert res["n_eval"] == 4
    assert res["exceptions"] == 2
    assert math.isclose(res["exception_rate"], 50.0, abs_tol=1e-2)
    assert math.isclose(res["expected_exceptions"], 4 * 0.05, abs_tol=1e-2)


def test_risk_metrics_dataset_if_present() -> None:
    """Validate data integrity and column existence of generated risk_metrics.parquet."""
    parquet_path = Path("data/clean/risk_metrics.parquet")
    if not parquet_path.exists():
        pytest.skip("risk_metrics.parquet not yet generated on disk.")

    df = pd.read_parquet(parquet_path)
    assert not df.empty
    expected_cols = [
        "nifty50_vol_20d",
        "nifty50_vol_60d",
        "nifty50_drawdown",
        "nifty50_var_hist_95",
        "nifty50_var_hist_99",
        "nifty50_var_norm_95",
        "nifty50_var_norm_99",
        "bank_nifty_vol_20d",
        "bank_nifty_vol_60d",
        "bank_nifty_drawdown",
        "bank_nifty_var_hist_95",
        "bank_nifty_var_hist_99",
        "bank_nifty_var_norm_95",
        "bank_nifty_var_norm_99",
    ]
    for col in expected_cols:
        assert col in df.columns

    # Drawdown is strictly <= 0
    assert (df["nifty50_drawdown"] <= 1e-10).all()
    assert (df["bank_nifty_drawdown"] <= 1e-10).all()

    # Volatility is strictly positive (where not NaN)
    assert (df["nifty50_vol_20d"].dropna() > 0).all()
    assert (df["bank_nifty_vol_20d"].dropna() > 0).all()
