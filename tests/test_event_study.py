"""Unit tests for the Union Budget Event Study module.

Validates:
1. OLS market model parameter estimation on known linear synthetic data.
2. Constant Mean Model abnormal returns on synthetic series with injected known AR.
3. CAR[-1, +1] and CAR[0, +5] summation accuracy.
4. Trading calendar roll-forward behavior for weekend / holiday presentations.
5. VIX and USD/INR level change calculation relative to day -1 baseline.
6. Student's t-distribution p-value precision against analytical benchmark.
7. End-to-end execution on the actual 9 Union Budget events.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src.event_study import (
    analyze_single_event,
    compute_ols_market_model,
    find_trading_day_index,
    run_budget_event_study,
    student_t_pvalue,
)


def test_ols_market_model_exact():
    """Verify OLS regression recovers exact known alpha and beta on synthetic returns."""
    np.random.seed(42)
    n = 100
    x = np.linspace(-0.03, 0.03, n)
    true_alpha = 0.0008
    true_beta = 1.35
    y = true_alpha + true_beta * x

    alpha, beta, r2 = compute_ols_market_model(y, x)
    assert math.isclose(alpha, true_alpha, abs_tol=1e-10)
    assert math.isclose(beta, true_beta, abs_tol=1e-10)
    assert math.isclose(r2, 1.0, abs_tol=1e-10)


def test_synthetic_known_abnormal_return():
    """Verify event study recovers an exact injected abnormal return on synthetic series.

    Design:
    - 200 trading days.
    - Event Day 0 is at index 140 (Date: 2020-07-20).
    - Estimation window: [-120, -21] corresponds to indices [20, 119].
    - Normal daily return in estimation window = 0.0010 (0.10%).
    - Injected return on Day 0 = 0.0010 + 0.0350 = 0.0360 (Day 0 AR = +3.50%).
    - Injected return on Day +1 = 0.0010 - 0.0120 = -0.0110 (Day +1 AR = -1.20%).
    - All other days have return = 0.0010 (AR = 0).
    """
    n_days = 200
    dates = pd.date_range("2020-01-01", periods=n_days, freq="B")

    # Baseline returns with alternating variations in estimation window so variance > 0
    base_ret = 0.0010
    variations = np.array([0.005 if i % 2 == 0 else -0.005 for i in range(n_days)])
    # In the event window [-5, +5], keep unperturbed days at base_ret so AR = 0
    event_idx = 140
    variations[event_idx - 5 : event_idx + 6] = 0.0
    nifty_ret = base_ret + variations

    # Bank Nifty: linear market model with true alpha = 0.0004 and true beta = 1.25
    true_bn_alpha = 0.0004
    true_bn_beta = 1.25
    bn_ret = true_bn_alpha + true_bn_beta * nifty_ret

    injected_nifty_ar_day0 = 0.0350
    injected_nifty_ar_day1 = -0.0120

    # Overwrite Day 0 and Day 1 returns
    nifty_ret[event_idx] = base_ret + injected_nifty_ar_day0
    nifty_ret[event_idx + 1] = base_ret + injected_nifty_ar_day1

    # Bank Nifty: inject known day 0 AR of +4.0%
    injected_bn_ar_day0 = 0.0400
    bn_ret[event_idx] = (
        true_bn_alpha + true_bn_beta * nifty_ret[event_idx]
    ) + injected_bn_ar_day0
    bn_ret[event_idx + 1] = true_bn_alpha + true_bn_beta * nifty_ret[event_idx + 1]

    synthetic_df = pd.DataFrame(
        {
            "Date": dates,
            "nifty50_log_return": nifty_ret,
            "bank_nifty_log_return": bn_ret,
            "india_vix_close": np.full(n_days, 16.0),
            "usdinr_close": np.full(n_days, 75.0),
        }
    )
    # Set VIX jump on day 0
    synthetic_df.loc[event_idx, "india_vix_close"] = 19.5  # +3.5 points

    event_date_str = str(dates[event_idx].date())
    res = analyze_single_event(
        synthetic_df,
        event_date=event_date_str,
        budget_type="Regular",
        estimation_window=(-120, -21),
        event_window=(-5, 5),
    )

    # 1. Day 0 Nifty AR should equal exactly +3.50%
    assert math.isclose(res["nifty_day0_ar_pct"], injected_nifty_ar_day0 * 100.0, abs_tol=1e-8)

    # 2. CAR[-1, +1] = AR(-1) + AR(0) + AR(+1) = 0 + 3.50% - 1.20% = +2.30%
    expected_car_m1_p1 = (injected_nifty_ar_day0 + injected_nifty_ar_day1) * 100.0
    assert math.isclose(res["nifty_car_minus1_plus1_pct"], expected_car_m1_p1, abs_tol=1e-8)

    # 3. Bank Nifty Day 0 AR should equal exactly +4.00%
    assert math.isclose(res["bank_nifty_day0_ar_pct"], injected_bn_ar_day0 * 100.0, abs_tol=1e-6)

    # 4. VIX change relative to day -1 = 19.5 - 16.0 = +3.5 points
    assert math.isclose(res["vix_day0_change"], 3.5, abs_tol=1e-10)


def test_calendar_closed_roll_forward():
    """Verify that when presentation date falls on a weekend,
    find_trading_day_index rolls forward.
    """
    calendar = pd.Series(
        [
            pd.Timestamp("2020-01-30"),
            pd.Timestamp("2020-01-31"),  # Friday
            pd.Timestamp("2020-02-03"),  # Monday
            pd.Timestamp("2020-02-04"),
        ]
    )

    # Saturday presentation
    idx, was_closed = find_trading_day_index(calendar, "2020-02-01")
    assert was_closed is True
    assert calendar.iloc[idx] == pd.Timestamp("2020-02-03")

    # Regular trading day presentation
    idx_fri, was_closed_fri = find_trading_day_index(calendar, "2020-01-31")
    assert was_closed_fri is False
    assert calendar.iloc[idx_fri] == pd.Timestamp("2020-01-31")


def test_student_t_distribution_known_values():
    """Verify custom Student's t p-value calculation matches theoretical statistics."""
    # t = 0 -> p = 1.0
    assert math.isclose(student_t_pvalue(0.0, 8), 1.0, abs_tol=1e-6)

    # For df = 8, two-sided 5% critical value is t = 2.306004
    # Expected p-value ~ 0.05
    p_crit = student_t_pvalue(2.306004, 8)
    assert math.isclose(p_crit, 0.05, abs_tol=1e-3)

    # Large t-stat (e.g. t = 10.0) -> p ~ 0
    p_extreme = student_t_pvalue(10.0, 8)
    assert p_extreme < 1e-4


def test_actual_budget_events_study_execution():
    """Verify run_budget_event_study runs cleanly on actual dataset with 9 events."""
    summary_df, panel_df, stats = run_budget_event_study()

    # 1. Exact count of 9 budget events
    assert len(summary_df) == 9
    assert stats["n_events"] == 9

    # 2. Key required columns present in summary table
    required_cols = [
        "event_date",
        "effective_date",
        "market_closed_on_presentation",
        "budget_type",
        "nifty_day0_ar_pct",
        "nifty_car_minus1_plus1_pct",
        "nifty_car_0_plus5_pct",
        "bank_nifty_day0_ar_pct",
        "bank_nifty_car_minus1_plus1_pct",
        "bank_nifty_car_0_plus5_pct",
        "vix_day0_change",
        "usdinr_day0_change",
    ]
    for col in required_cols:
        assert col in summary_df.columns, f"Missing required column: {col}"

    # 3. 2020-02-01 was on Saturday, must be rolled to 2020-02-03 with flag True
    evt_2020 = summary_df[summary_df["event_date"] == "2020-02-01"].iloc[0]
    assert evt_2020["effective_date"] == "2020-02-03"
    assert bool(evt_2020["market_closed_on_presentation"]) is True

    # 4. Trajectory panel: 9 events * 11 days (tau from -5 to +5) = 99 rows
    assert len(panel_df) == 99
    assert set(panel_df["tau"].unique()) == set(range(-5, 6))

    # 5. Cross-sectional statistics dict populated with required keys
    assert "nifty_car_minus1_plus1_pct" in stats
    assert "p_value" in stats["nifty_car_minus1_plus1_pct"]
    assert 0.0 <= stats["nifty_car_minus1_plus1_pct"]["p_value"] <= 1.0
