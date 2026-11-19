"""Module to export tidy, analytical CSV datasets for Power BI reporting.

Produces standardized CSV tables in exports/ with ISO dates (YYYY-MM-DD),
clean column names, and zero blank/merged rows:
1. market_daily.csv
2. risk_metrics.csv
3. vol_comparison.csv
4. var_backtest.csv
5. budget_events_summary.csv
6. budget_event_paths.csv
7. correlations.csv
8. date_table.csv
"""

from __future__ import annotations

import os

import pandas as pd

from src.risk import backtest_var


def generate_market_daily_export(
    market_daily_df: pd.DataFrame,
) -> pd.DataFrame:
    """Format market daily series into a tidy export table.

    Parameters
    ----------
    market_daily_df : pd.DataFrame
        Input cleaned market daily dataframe.

    Returns
    -------
    pd.DataFrame
        Tidy export dataframe.
    """
    df = market_daily_df.copy()
    df["date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

    cols = [
        "date",
        "nifty50_close",
        "nifty50_log_return",
        "bank_nifty_close",
        "bank_nifty_log_return",
        "india_vix_close",
        "india_vix_log_return",
        "sp500_close",
        "sp500_log_return",
        "brent_crude_close",
        "brent_crude_log_return",
        "usdinr_close",
        "usdinr_log_return",
        "us10y_yield_close",
        "us10y_yield_log_return",
    ]
    return df[cols].copy()


def generate_risk_metrics_export(
    risk_metrics_df: pd.DataFrame,
) -> pd.DataFrame:
    """Format risk metrics and binary exception flags into a tidy export table.

    Parameters
    ----------
    risk_metrics_df : pd.DataFrame
        Input risk metrics dataframe.

    Returns
    -------
    pd.DataFrame
        Tidy export dataframe.
    """
    df = risk_metrics_df.copy()
    df["date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

    # Add binary exception indicator columns (1 if return < VaR cutoff, else 0)
    for prefix in ["nifty50", "bank_nifty"]:
        ret = df[f"{prefix}_log_return"]
        for suff in ["hist_95", "hist_99", "norm_95", "norm_99"]:
            var_thresh = df[f"{prefix}_var_{suff}"]
            df[f"{prefix}_exc_{suff}"] = (
                (ret < var_thresh).astype(int).where(var_thresh.notna(), None)
            )

    cols = [
        "date",
        "nifty50_vol_20d",
        "nifty50_vol_60d",
        "nifty50_peak",
        "nifty50_drawdown",
        "nifty50_var_hist_95",
        "nifty50_var_hist_99",
        "nifty50_var_norm_95",
        "nifty50_var_norm_99",
        "nifty50_exc_hist_95",
        "nifty50_exc_hist_99",
        "nifty50_exc_norm_95",
        "nifty50_exc_norm_99",
        "bank_nifty_vol_20d",
        "bank_nifty_vol_60d",
        "bank_nifty_peak",
        "bank_nifty_drawdown",
        "bank_nifty_var_hist_95",
        "bank_nifty_var_hist_99",
        "bank_nifty_var_norm_95",
        "bank_nifty_var_norm_99",
        "bank_nifty_exc_hist_95",
        "bank_nifty_exc_hist_99",
        "bank_nifty_exc_norm_95",
        "bank_nifty_exc_norm_99",
    ]
    return df[cols].copy()


def generate_vol_comparison_export(
    vix_df: pd.DataFrame,
) -> pd.DataFrame:
    """Format volatility comparison series into a tidy export table.

    Parameters
    ----------
    vix_df : pd.DataFrame
        Input VIX analysis dataframe.

    Returns
    -------
    pd.DataFrame
        Tidy export dataframe.
    """
    df = vix_df.copy()
    df["date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

    cols = [
        "date",
        "india_vix_close",
        "trailing_vol_21d",
        "fwd_vol_21d_retrospective",
        "vrp_spread_retrospective",
    ]
    return df[cols].copy()


def generate_var_backtest_export(
    risk_metrics_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute and format VaR backtest results into a tidy summary table.

    Parameters
    ----------
    risk_metrics_df : pd.DataFrame
        Input risk metrics dataframe.

    Returns
    -------
    pd.DataFrame
        Tidy backtest summary dataframe.
    """
    df = risk_metrics_df
    rows = []

    configs = [
        ("NIFTY 50", "nifty50_log_return", "nifty50"),
        ("Bank NIFTY", "bank_nifty_log_return", "bank_nifty"),
    ]

    for asset, ret_col, prefix in configs:
        ret = df[ret_col]
        for conf, suff in [(0.95, "95"), (0.99, "99")]:
            for model, col_name in [
                ("Historical Simulation", f"{prefix}_var_hist_{suff}"),
                ("Parametric Normal", f"{prefix}_var_norm_{suff}"),
            ]:
                b = backtest_var(ret, df[col_name], conf)
                rows.append(
                    {
                        "asset": asset,
                        "model": model,
                        "confidence_level": conf,
                        "total_eval_days": b["n_eval"],
                        "expected_exceptions": round(b["expected_exceptions"], 1),
                        "actual_exceptions": b["exceptions"],
                        "exception_ratio": round(b["ratio"], 3),
                        "kupiec_lr_stat": round(b["kupiec_lr"], 3),
                        "p_value": round(b["p_value"], 4),
                        "outcome": "Pass" if b["p_value"] >= 0.05 else "Reject",
                    }
                )

    return pd.DataFrame(rows)


def generate_budget_summary_export(
    budget_study_df: pd.DataFrame,
    budget_raw_df: pd.DataFrame,
) -> pd.DataFrame:
    """Format Union Budget event summary into a tidy export table.

    Parameters
    ----------
    budget_study_df : pd.DataFrame
        Event study results dataframe.
    budget_raw_df : pd.DataFrame
        Raw budget events dataframe with minister details.

    Returns
    -------
    pd.DataFrame
        Tidy export dataframe.
    """
    df = budget_study_df.copy()
    # Merge finance minister if available
    if "finance_minister" in budget_raw_df.columns:
        df = df.merge(
            budget_raw_df[["date", "finance_minister"]],
            left_on="event_date",
            right_on="date",
            how="left",
        )
        df = df.drop(columns=["date"])
    else:
        df["finance_minister"] = ""

    cols = [
        "event_date",
        "effective_date",
        "market_closed_on_presentation",
        "budget_type",
        "finance_minister",
        "nifty_day0_ar_pct",
        "nifty_car_minus1_plus1_pct",
        "nifty_car_0_plus5_pct",
        "bank_nifty_day0_ar_pct",
        "bank_nifty_car_minus1_plus1_pct",
        "bank_nifty_car_0_plus5_pct",
        "vix_day0_change",
        "usdinr_day0_change",
        "notes",
    ]
    return df[cols].copy()


def generate_budget_paths_export(
    trajectory_panel_df: pd.DataFrame,
) -> pd.DataFrame:
    """Format daily event study trajectory panel into a tidy export table.

    Parameters
    ----------
    trajectory_panel_df : pd.DataFrame
        Trajectory panel dataframe across events and relative tau.

    Returns
    -------
    pd.DataFrame
        Tidy export dataframe.
    """
    df = trajectory_panel_df.copy()
    df["date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

    cols = [
        "event_date",
        "budget_type",
        "tau",
        "date",
        "nifty_ar",
        "nifty_car",
        "bank_nifty_ar",
        "bank_nifty_car",
        "vix_level_change",
        "usdinr_level_change",
    ]
    return df[cols].copy()


def generate_correlations_export(
    market_daily_df: pd.DataFrame,
    window: int = 60,
) -> pd.DataFrame:
    """Compute rolling correlations of NIFTY 50 with global assets.

    Parameters
    ----------
    market_daily_df : pd.DataFrame
        Input cleaned market daily dataframe.
    window : int
        Rolling window in trading days (default 60).

    Returns
    -------
    pd.DataFrame
        Tidy export dataframe.
    """
    df = market_daily_df.copy()
    nifty_ret = df["nifty50_log_return"]

    corr_df = pd.DataFrame(
        {"date": pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")}
    )

    pairs = [
        ("sp500_log_return", "corr_sp500"),
        ("brent_crude_log_return", "corr_brent"),
        ("usdinr_log_return", "corr_usdinr"),
        ("us10y_yield_log_return", "corr_us10y"),
    ]

    for ret_col, out_col in pairs:
        corr_df[out_col] = (
            nifty_ret.rolling(window=window, min_periods=window).corr(df[ret_col])
        )

    return corr_df


def generate_date_table(
    market_daily_df: pd.DataFrame,
    budget_raw_df: pd.DataFrame,
) -> pd.DataFrame:
    """Generate calendar date dimension table for Power BI.

    Parameters
    ----------
    market_daily_df : pd.DataFrame
        Master market daily dataframe.
    budget_raw_df : pd.DataFrame
        Budget presentation dates dataframe.

    Returns
    -------
    pd.DataFrame
        Date dimension table.
    """
    start_date = pd.to_datetime(market_daily_df["Date"]).min()
    end_date = pd.to_datetime(market_daily_df["Date"]).max()

    full_calendar = pd.date_range(start_date, end_date, freq="D")
    df_date = pd.DataFrame({"date_ts": full_calendar})

    df_date["date"] = df_date["date_ts"].dt.strftime("%Y-%m-%d")
    df_date["year"] = df_date["date_ts"].dt.year
    df_date["quarter_number"] = df_date["date_ts"].dt.quarter
    df_date["quarter"] = "Q" + df_date["quarter_number"].astype(str)
    df_date["year_quarter"] = (
        df_date["year"].astype(str) + "-Q" + df_date["quarter_number"].astype(str)
    )
    df_date["month_number"] = df_date["date_ts"].dt.month
    df_date["month"] = df_date["date_ts"].dt.strftime("%B")
    df_date["year_month"] = df_date["date_ts"].dt.strftime("%Y-%m")
    df_date["day_of_month"] = df_date["date_ts"].dt.day
    df_date["day_of_week"] = df_date["date_ts"].dt.strftime("%A")

    trading_dates = set(
        pd.to_datetime(market_daily_df["Date"]).dt.strftime("%Y-%m-%d")
    )
    df_date["is_trading_day"] = df_date["date"].isin(trading_dates).astype(int)

    # Budget presentation flag
    budget_dates_map = dict(
        zip(
            pd.to_datetime(budget_raw_df["date"]).dt.strftime("%Y-%m-%d"),
            budget_raw_df["budget_type"],
            strict=False,
        )
    )
    df_date["is_budget_presentation_date"] = (
        df_date["date"].isin(budget_dates_map).astype(int)
    )
    df_date["budget_type"] = (
        df_date["date"].map(budget_dates_map).fillna("None")
    )

    df_date = df_date.drop(columns=["date_ts"])
    return df_date


def export_all_powerbi_tables(
    output_dir: str = "exports",
    market_daily_path: str = "data/clean/market_daily.parquet",
    risk_metrics_path: str = "data/clean/risk_metrics.parquet",
    vix_analysis_path: str = "data/clean/vix_analysis.parquet",
    budget_study_path: str = "data/clean/budget_event_study.parquet",
    budget_traj_path: str = "data/clean/budget_event_trajectories.parquet",
    budget_raw_path: str = "data/raw/budget_events.csv",
) -> dict[str, str]:
    """Run all exports and generate tidy CSVs in the specified directory.

    Parameters
    ----------
    output_dir : str
        Directory to write CSVs to (default 'exports').
    market_daily_path, risk_metrics_path, vix_analysis_path, budget_study_path,
    budget_traj_path, budget_raw_path : str
        Source paths.

    Returns
    -------
    dict[str, str]
        Dictionary mapping table name to exported filepath.
    """
    os.makedirs(output_dir, exist_ok=True)

    df_market = pd.read_parquet(market_daily_path)
    df_risk = pd.read_parquet(risk_metrics_path)
    df_vix = pd.read_parquet(vix_analysis_path)
    df_budget_study = pd.read_parquet(budget_study_path)
    df_budget_traj = pd.read_parquet(budget_traj_path)
    df_budget_raw = pd.read_csv(budget_raw_path)

    exports = {}

    # 1. market_daily.csv
    exp_market = generate_market_daily_export(df_market)
    p = os.path.join(output_dir, "market_daily.csv")
    exp_market.to_csv(p, index=False)
    exports["market_daily"] = p

    # 2. risk_metrics.csv
    exp_risk = generate_risk_metrics_export(df_risk)
    p = os.path.join(output_dir, "risk_metrics.csv")
    exp_risk.to_csv(p, index=False)
    exports["risk_metrics"] = p

    # 3. vol_comparison.csv
    exp_vol = generate_vol_comparison_export(df_vix)
    p = os.path.join(output_dir, "vol_comparison.csv")
    exp_vol.to_csv(p, index=False)
    exports["vol_comparison"] = p

    # 4. var_backtest.csv
    exp_backtest = generate_var_backtest_export(df_risk)
    p = os.path.join(output_dir, "var_backtest.csv")
    exp_backtest.to_csv(p, index=False)
    exports["var_backtest"] = p

    # 5. budget_events_summary.csv
    exp_budget_summary = generate_budget_summary_export(
        df_budget_study, df_budget_raw
    )
    p = os.path.join(output_dir, "budget_events_summary.csv")
    exp_budget_summary.to_csv(p, index=False)
    exports["budget_events_summary"] = p

    # 6. budget_event_paths.csv
    exp_budget_paths = generate_budget_paths_export(df_budget_traj)
    p = os.path.join(output_dir, "budget_event_paths.csv")
    exp_budget_paths.to_csv(p, index=False)
    exports["budget_event_paths"] = p

    # 7. correlations.csv
    exp_corr = generate_correlations_export(df_market, window=60)
    p = os.path.join(output_dir, "correlations.csv")
    exp_corr.to_csv(p, index=False)
    exports["correlations"] = p

    # 8. date_table.csv
    exp_date = generate_date_table(df_market, df_budget_raw)
    p = os.path.join(output_dir, "date_table.csv")
    exp_date.to_csv(p, index=False)
    exports["date_table"] = p

    return exports


if __name__ == "__main__":
    files = export_all_powerbi_tables()
    for name, path in files.items():
        print(f"Exported {name} -> {path}")
