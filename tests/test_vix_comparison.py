"""Unit tests for Phase 3 India VIX vs. Realized Volatility module.

Verifies:
1. Trailing realized volatility formula and strictly backward-looking nature.
2. Forward realized volatility strictly using future returns [t+1, ..., t+window].
3. Forward realized volatility returns NaN for the last `window` periods.
4. Volatility spread calculation (VIX - Forward Realized).
5. Data integrity and schema of generated vix_analysis.parquet dataset.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.vix_analysis import (
    ANNUALISATION_FACTOR,
    compute_forward_realized_vol,
    compute_trailing_realized_vol,
    compute_volatility_spread,
)


def test_trailing_realized_vol_hand_calculated() -> None:
    """Verify trailing realized volatility on hand-calculated 3-period series:

    Returns: [0.01, -0.02, 0.04]
    Mean: 0.01, Sum squared dev = 0.0018, ddof=1 sample variance = 0.0009
    Sample std = 0.03
    Annualised = 0.03 * sqrt(252)
    """
    returns = pd.Series([0.01, -0.02, 0.04])
    trailing = compute_trailing_realized_vol(returns, window=3)

    assert pd.isna(trailing.iloc[0])
    assert pd.isna(trailing.iloc[1])

    expected = 0.03 * ANNUALISATION_FACTOR
    assert math.isclose(trailing.iloc[2], expected, abs_tol=1e-10)


def test_forward_realized_vol_hand_calculated() -> None:
    """Verify forward realized volatility on hand-calculated 5-period series with window=2:

    Indices:
    0: forward returns are [r1, r2]
    1: forward returns are [r2, r3]
    2: forward returns are [r3, r4]
    3: forward returns are [r4] (insufficient -> NaN)
    4: no forward returns -> NaN
    """
    returns = pd.Series([0.00, 0.02, -0.02, 0.01, -0.01])
    fwd = compute_forward_realized_vol(returns, window=2)

    # Index 0: forward returns are r[1]=0.02, r[2]=-0.02
    # Mean = 0.0, dev = [0.02, -0.02], sum sq = 0.0008, sample var (N-1=1) = 0.0008
    # std = sqrt(0.0008) = 0.028284271247461902
    expected_0 = np.sqrt(0.0008) * ANNUALISATION_FACTOR
    assert math.isclose(fwd.iloc[0], expected_0, abs_tol=1e-10)

    # Index 1: forward returns are r[2]=-0.02, r[3]=0.01
    # Mean = -0.005, dev = [-0.015, 0.015], sum sq = 0.00045, sample var = 0.00045
    # std = sqrt(0.00045)
    expected_1 = np.sqrt(0.00045) * ANNUALISATION_FACTOR
    assert math.isclose(fwd.iloc[1], expected_1, abs_tol=1e-10)

    # Index 3 and 4 must be NaN (last window=2 rows)
    assert pd.isna(fwd.iloc[3])
    assert pd.isna(fwd.iloc[4])


def test_forward_vol_invariance_to_current_date_return() -> None:
    """Verify that forward realized volatility at date t does NOT use return at date t.

    Forward volatility at t strictly uses returns from t+1 onwards.
    """
    returns_base = pd.Series([0.01, 0.02, -0.01, 0.03, -0.02, 0.01])
    fwd_base = compute_forward_realized_vol(returns_base, window=2)

    # Modify return at index 1
    returns_mod = returns_base.copy()
    returns_mod.iloc[1] = 0.15  # massive shock on date 1

    fwd_mod = compute_forward_realized_vol(returns_mod, window=2)

    # Forward volatility at index 1 evaluates returns at index 2 and 3:
    # Therefore, modifying return at index 1 MUST NOT CHANGE fwd_vol at index 1!
    assert math.isclose(fwd_base.iloc[1], fwd_mod.iloc[1], abs_tol=1e-12)

    # However, forward volatility at index 0 evaluates index 1 and 2, so it MUST change
    assert not math.isclose(fwd_base.iloc[0], fwd_mod.iloc[0], abs_tol=1e-5)


def test_volatility_spread_formula() -> None:
    """Verify spread formula: Spread = VIX - Forward Realized Vol."""
    vix = pd.Series([16.0, 18.5, 20.0])
    fwd_vol = pd.Series([13.5, 22.0, np.nan])

    spread = compute_volatility_spread(vix, fwd_vol)

    assert math.isclose(spread.iloc[0], 2.5, abs_tol=1e-10)  # Positive VRP
    assert math.isclose(spread.iloc[1], -3.5, abs_tol=1e-10)  # Negative VRP
    assert pd.isna(spread.iloc[2])


def test_vix_analysis_dataset_if_present() -> None:
    """Validate data integrity and columns of generated vix_analysis.parquet."""
    parquet_path = Path("data/clean/vix_analysis.parquet")
    if not parquet_path.exists():
        pytest.skip("vix_analysis.parquet not yet generated on disk.")

    df = pd.read_parquet(parquet_path)
    assert not df.empty
    expected_cols = [
        "trailing_vol_21d",
        "fwd_vol_21d_retrospective",
        "vrp_spread_retrospective",
        "india_vix_close",
    ]
    for col in expected_cols:
        assert col in df.columns

    # The last 21 rows of forward realized vol and spread must be NaN
    assert df["fwd_vol_21d_retrospective"].iloc[-21:].isna().all()
    assert df["vrp_spread_retrospective"].iloc[-21:].isna().all()

    # Prior rows must be valid
    valid_fwd = df["fwd_vol_21d_retrospective"].iloc[:-21]
    assert valid_fwd.notna().all()
    assert (valid_fwd > 0).all()
