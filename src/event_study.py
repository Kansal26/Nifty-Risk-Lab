"""Event study module analyzing market impact of the Union Budget.

Investigates:
1. NIFTY 50 abnormal returns (Constant Mean Return model).
2. Bank NIFTY abnormal returns (Market Model OLS regression on NIFTY 50).
3. India VIX and USD/INR level shifts relative to day -1.
4. Cumulative Abnormal Returns (CAR) for [-1, +1] and [0, +5].
5. Cross-sectional aggregation and Student's t-test.
"""

from __future__ import annotations

import math
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def compute_ols_market_model(
    y: np.ndarray, x: np.ndarray
) -> tuple[float, float, float]:
    """Fit OLS linear regression y = alpha + beta * x.

    Parameters
    ----------
    y : np.ndarray
        Dependent asset returns (e.g., Bank Nifty).
    x : np.ndarray
        Independent benchmark returns (e.g., Nifty 50).

    Returns
    -------
    tuple[float, float, float]
        (alpha, beta, r_squared)
    """
    if len(y) != len(x):
        raise ValueError("Series x and y must have the same length.")
    if len(x) < 3:
        raise ValueError("At least 3 observations required for OLS.")

    x_mean = float(np.mean(x))
    y_mean = float(np.mean(y))

    var_x = float(np.var(x, ddof=1))
    if var_x < 1e-12:
        return y_mean, 0.0, 0.0

    cov_xy = float(np.cov(x, y)[0, 1])
    beta = cov_xy / var_x
    alpha = y_mean - beta * x_mean

    # R-squared
    y_pred = alpha + beta * x
    ss_tot = float(np.sum((y - y_mean) ** 2))
    ss_res = float(np.sum((y - y_pred) ** 2))
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-12 else 0.0

    return alpha, beta, max(0.0, r_squared)


def find_trading_day_index(
    market_dates: pd.Series, target_date: str | pd.Timestamp
) -> tuple[int, bool]:
    """Find the integer index in the trading calendar for a target event date.

    If target date is an exchange holiday or weekend, rolls forward to the
    immediate next trading day.

    Parameters
    ----------
    market_dates : pd.Series
        Series of sorted trading calendar dates (pd.Timestamp).
    target_date : str | pd.Timestamp
        Target event date.

    Returns
    -------
    tuple[int, bool]
        (index, was_closed) where was_closed is True if target was rolled.
    """
    target = pd.to_datetime(target_date)
    exact_match = market_dates[market_dates == target]

    if not exact_match.empty:
        return int(exact_match.index[0]), False

    # Roll forward to the next available trading day
    subsequent = market_dates[market_dates > target]
    if subsequent.empty:
        raise ValueError(f"Target date {target_date} has no subsequent trading days in data.")

    return int(subsequent.index[0]), True


def analyze_single_event(
    df: pd.DataFrame,
    event_date: str | pd.Timestamp,
    budget_type: str,
    notes: str = "",
    estimation_window: tuple[int, int] = (-120, -21),
    event_window: tuple[int, int] = (-5, 5),
) -> dict[str, Any]:
    """Perform event study calculations for a single Union Budget presentation.

    Parameters
    ----------
    df : pd.DataFrame
        Clean market daily dataframe with 'Date', 'nifty50_log_return',
        'bank_nifty_log_return', 'india_vix_close', 'usdinr_close'.
    event_date : str | pd.Timestamp
        Budget presentation date.
    budget_type : str
        'Regular' or 'Interim'.
    notes : str
        Descriptive contextual notes.
    estimation_window : tuple[int, int]
        (start_tau, end_tau) relative trading days, default (-120, -21).
    event_window : tuple[int, int]
        (start_tau, end_tau) relative trading days, default (-5, 5).

    Returns
    -------
    dict[str, Any]
        Dictionary with event metrics and daily abnormal trajectory.
    """
    dates = pd.to_datetime(df["Date"]).reset_index(drop=True)
    day0_idx, was_closed = find_trading_day_index(dates, event_date)
    effective_date = dates.iloc[day0_idx]

    est_start = day0_idx + estimation_window[0]
    est_end = day0_idx + estimation_window[1]

    if est_start < 0:
        raise ValueError(
            f"Insufficient historical data prior to {event_date}. "
            f"Requires at least {-estimation_window[0]} prior trading days."
        )

    ev_start = day0_idx + event_window[0]
    ev_end = day0_idx + event_window[1]

    if ev_end >= len(df):
        raise ValueError(
            f"Insufficient post-event data after {event_date}. "
            f"Requires at least {event_window[1]} subsequent trading days."
        )

    # 1. Estimation window slices
    est_df = df.iloc[est_start : est_end + 1]
    nifty_est_ret = est_df["nifty50_log_return"].to_numpy(dtype=float)
    bn_est_ret = est_df["bank_nifty_log_return"].to_numpy(dtype=float)

    # NIFTY 50 Constant Mean Model
    nifty_normal_mean = float(np.mean(nifty_est_ret))

    # Bank NIFTY Market Model Regression
    bn_alpha, bn_beta, bn_r2 = compute_ols_market_model(bn_est_ret, nifty_est_ret)

    # 2. Event window slice [-5, +5]
    ev_df = df.iloc[ev_start : ev_end + 1].copy()
    taus = np.arange(event_window[0], event_window[1] + 1)
    ev_df["tau"] = taus

    # Nifty Abnormal Returns
    ev_df["nifty_ar"] = ev_df["nifty50_log_return"] - nifty_normal_mean

    # Bank Nifty Abnormal Returns: AR = R_bn - (alpha + beta * R_nifty)
    ev_df["bank_nifty_ar"] = ev_df["bank_nifty_log_return"] - (
        bn_alpha + bn_beta * ev_df["nifty50_log_return"]
    )

    # Day -1 Baseline for VIX and USD/INR level changes
    day_minus_1_row = ev_df[ev_df["tau"] == -1].iloc[0]
    vix_base = float(day_minus_1_row["india_vix_close"])
    usdinr_base = float(day_minus_1_row["usdinr_close"])

    ev_df["vix_level_change"] = ev_df["india_vix_close"] - vix_base
    ev_df["usdinr_level_change"] = ev_df["usdinr_close"] - usdinr_base

    # Cumulative Abnormal Returns
    ev_df["nifty_car"] = ev_df["nifty_ar"].cumsum()
    ev_df["bank_nifty_car"] = ev_df["bank_nifty_ar"].cumsum()

    # Specific CAR windows
    # CAR[-1, +1]
    car_m1_p1_nifty = float(
        ev_df.loc[ev_df["tau"].between(-1, 1), "nifty_ar"].sum()
    )
    car_m1_p1_bn = float(
        ev_df.loc[ev_df["tau"].between(-1, 1), "bank_nifty_ar"].sum()
    )

    # CAR[0, +5]
    car_0_p5_nifty = float(
        ev_df.loc[ev_df["tau"].between(0, 5), "nifty_ar"].sum()
    )
    car_0_p5_bn = float(
        ev_df.loc[ev_df["tau"].between(0, 5), "bank_nifty_ar"].sum()
    )

    day0_row = ev_df[ev_df["tau"] == 0].iloc[0]

    return {
        "event_date": str(pd.to_datetime(event_date).date()),
        "effective_date": str(effective_date.date()),
        "market_closed_on_presentation": was_closed,
        "budget_type": budget_type,
        "nifty_normal_mean_pct": nifty_normal_mean * 100.0,
        "bn_alpha_pct": bn_alpha * 100.0,
        "bn_beta": bn_beta,
        "bn_r2": bn_r2,
        "nifty_day0_ar_pct": float(day0_row["nifty_ar"]) * 100.0,
        "nifty_car_minus1_plus1_pct": car_m1_p1_nifty * 100.0,
        "nifty_car_0_plus5_pct": car_0_p5_nifty * 100.0,
        "bank_nifty_day0_ar_pct": float(day0_row["bank_nifty_ar"]) * 100.0,
        "bank_nifty_car_minus1_plus1_pct": car_m1_p1_bn * 100.0,
        "bank_nifty_car_0_plus5_pct": car_0_p5_bn * 100.0,
        "vix_day0_change": float(day0_row["vix_level_change"]),
        "usdinr_day0_change": float(day0_row["usdinr_level_change"]),
        "notes": notes,
        "trajectory": ev_df[
            [
                "tau",
                "Date",
                "nifty_ar",
                "nifty_car",
                "bank_nifty_ar",
                "bank_nifty_car",
                "vix_level_change",
                "usdinr_level_change",
            ]
        ].copy(),
    }


def student_t_pvalue(t_stat: float, df_freedom: int) -> float:
    """Compute two-sided p-value for Student's t-distribution.

    Uses the exact closed-form trigonometric transformation for integer degrees
    of freedom (Kendall & Stuart), avoiding scipy dependency.

    Parameters
    ----------
    t_stat : float
        Calculated t-statistic.
    df_freedom : int
        Degrees of freedom (N - 1).

    Returns
    -------
    float
        Two-sided p-value in [0, 1].
    """
    if df_freedom <= 0:
        return 1.0

    t = abs(float(t_stat))
    if t < 1e-14:
        return 1.0

    df = int(df_freedom)
    theta = math.atan(t / math.sqrt(df))

    if df % 2 == 0:
        term = math.sin(theta)
        total = term
        cos2 = math.cos(theta) ** 2
        for k in range(1, df // 2):
            term *= ((2.0 * k - 1.0) / (2.0 * k)) * cos2
            total += term
        return max(0.0, min(1.0, 1.0 - total))
    else:
        term = math.sin(theta) * math.cos(theta)
        total = theta
        if df > 1:
            total += term
            cos2 = math.cos(theta) ** 2
            for k in range(1, (df - 1) // 2):
                term *= ((2.0 * k) / (2.0 * k + 1.0)) * cos2
                total += term
        return max(0.0, min(1.0, 1.0 - (2.0 / math.pi) * total))


def run_budget_event_study(
    market_data_path: str = "data/clean/market_daily.parquet",
    budget_events_path: str = "data/raw/budget_events.csv",
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Run full event study on all budget events in budget_events.csv.

    Parameters
    ----------
    market_data_path : str
        Path to aligned clean daily parquet file.
    budget_events_path : str
        Path to raw budget events CSV.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]
        (events_summary_table, trajectory_panel, cross_sectional_stats)
    """
    df_market = pd.read_parquet(market_data_path)
    df_events = pd.read_csv(budget_events_path)

    event_summaries = []
    trajectories = []

    for _, row in df_events.iterrows():
        res = analyze_single_event(
            df_market,
            event_date=row["date"],
            budget_type=str(row["budget_type"]),
            notes=str(row.get("notes", "")),
        )

        traj = res.pop("trajectory")
        traj["event_date"] = row["date"]
        traj["budget_type"] = row["budget_type"]
        trajectories.append(traj)

        event_summaries.append(res)

    summary_df = pd.DataFrame(event_summaries)
    panel_df = pd.concat(trajectories, ignore_index=True)

    # Cross-sectional statistics across events (N = len(summary_df))
    n_events = len(summary_df)
    cols_to_test = [
        "nifty_day0_ar_pct",
        "nifty_car_minus1_plus1_pct",
        "nifty_car_0_plus5_pct",
        "bank_nifty_day0_ar_pct",
        "bank_nifty_car_minus1_plus1_pct",
        "bank_nifty_car_0_plus5_pct",
        "vix_day0_change",
        "usdinr_day0_change",
    ]

    stats: dict[str, Any] = {"n_events": n_events}
    for col in cols_to_test:
        vals = summary_df[col].to_numpy(dtype=float)
        mean_val = float(np.mean(vals))
        std_val = float(np.std(vals, ddof=1))
        se_val = std_val / math.sqrt(n_events)
        t_stat = mean_val / se_val if se_val > 1e-12 else 0.0
        p_val = student_t_pvalue(abs(t_stat), n_events - 1)

        stats[col] = {
            "mean": mean_val,
            "std": std_val,
            "se": se_val,
            "t_stat": t_stat,
            "p_value": p_val,
            "significant_at_05": p_val < 0.05,
        }

    return summary_df, panel_df, stats


def plot_event_study_paths(
    panel_df: pd.DataFrame,
    output_path: str = "docs/figures/budget_event_study_car.png",
) -> None:
    """Plot average abnormal return path with individual event trajectories behind it.

    Parameters
    ----------
    panel_df : pd.DataFrame
        Trajectory panel dataframe across events and relative tau.
    output_path : str
        Filepath to save the PNG figure.
    """
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)

    # Compute mean trajectories across events
    mean_trajectory = (
        panel_df.groupby("tau")[["nifty_car", "bank_nifty_car"]].mean() * 100.0
    )

    events = panel_df["event_date"].unique()

    # Panel 1: NIFTY 50
    for evt in events:
        sub = panel_df[panel_df["event_date"] == evt]
        axes[0].plot(
            sub["tau"],
            sub["nifty_car"] * 100.0,
            color="#a0aec0",
            lw=1.2,
            alpha=0.6,
            label=f"{evt}" if evt == events[0] else None,
        )

    axes[0].plot(
        mean_trajectory.index,
        mean_trajectory["nifty_car"],
        color="#1f77b4",
        lw=3.0,
        marker="o",
        label="Cross-Event Average (CAAR)",
    )
    axes[0].axvline(0, color="red", linestyle="--", alpha=0.8, label="Budget Presentation (Day 0)")
    axes[0].axhline(0, color="black", linestyle=":", alpha=0.6)
    n_evt = len(events)
    axes[0].set_title(
        f"NIFTY 50 CAR [-5, +5]\nMean Model Benchmark (N = {n_evt})",
        fontsize=12,
        fontweight="bold",
    )
    axes[0].set_xlabel("Relative Trading Day (τ)")
    axes[0].set_ylabel("Cumulative Abnormal Return (%)")
    axes[0].legend(loc="upper left")

    # Panel 2: Bank NIFTY
    for evt in events:
        sub = panel_df[panel_df["event_date"] == evt]
        axes[1].plot(
            sub["tau"],
            sub["bank_nifty_car"] * 100.0,
            color="#a0aec0",
            lw=1.2,
            alpha=0.6,
        )

    axes[1].plot(
        mean_trajectory.index,
        mean_trajectory["bank_nifty_car"],
        color="#ff7f0e",
        lw=3.0,
        marker="s",
        label="Cross-Event Average (CAAR)",
    )
    axes[1].axvline(0, color="red", linestyle="--", alpha=0.8, label="Budget Presentation (Day 0)")
    axes[1].axhline(0, color="black", linestyle=":", alpha=0.6)
    axes[1].set_title(
        f"Bank NIFTY CAR [-5, +5]\nMarket Model Benchmark (N = {n_evt})",
        fontsize=12,
        fontweight="bold",
    )
    axes[1].set_xlabel("Relative Trading Day (τ)")
    axes[1].legend(loc="upper left")

    plt.suptitle(
        "Union Budget Event Study: Cumulative Abnormal Return Dynamics (2016 - 2024)",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    import os

    os.makedirs("data/clean", exist_ok=True)
    os.makedirs("docs/figures", exist_ok=True)

    summary_table, trajectory_panel, cross_stats = run_budget_event_study()

    # Save to parquet and csv
    summary_table.to_parquet("data/clean/budget_event_study.parquet", index=False)
    summary_table.to_csv("data/clean/budget_event_study.csv", index=False)

    trajectory_panel.to_parquet("data/clean/budget_event_trajectories.parquet", index=False)
    trajectory_panel.to_csv("data/clean/budget_event_trajectories.csv", index=False)

    # Plot
    plot_event_study_paths(trajectory_panel, "docs/figures/budget_event_study_car.png")

    print(f"Successfully processed {len(summary_table)} Union Budget events.")
    print("Exported data/clean/budget_event_study.parquet and .csv")
    print("Exported docs/figures/budget_event_study_car.png")

