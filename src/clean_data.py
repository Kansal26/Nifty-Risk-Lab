"""Data cleaning and return computation module for nifty-risk-lab.

Transforms raw historical daily data for NIFTY 50 and India VIX into
clean, validated, analysis-ready time series.

Key Rules & Methodologies:
- Log Returns: r_t = ln(P_t / P_{t-1}) = ln(P_t) - ln(P_{t-1})
- Annualisation: Volatility annualised with factor sqrt(252).
- VIX Daily Implied: sigma_daily = VIX_t / (100 * sqrt(252))
- Zero Look-Ahead Bias: Metrics at date t strictly depend on information at or before date t.
- Alignment: Datasets merged strictly on point-in-time trading dates (inner join, no forward fill).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path("data/raw")
CLEAN_DATA_DIR = Path("data/clean")
ANNUALISATION_FACTOR = np.sqrt(252)


def load_raw_dataset(file_path: Path) -> pd.DataFrame:
    """Load raw CSV dataset and validate presence.

    Parameters
    ----------
    file_path : Path
        Path to raw CSV file.

    Returns
    -------
    pd.DataFrame
        Loaded raw DataFrame.

    Raises
    ------
    FileNotFoundError
        If raw file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"Required raw data file not found at: {file_path}. "
            "Please run 'python -m src.download_data' first."
        )
    return pd.read_csv(file_path)


def clean_price_series(df: pd.DataFrame, ticker_name: str) -> pd.DataFrame:
    """Clean date format, check validity, and sort chronologically.

    Parameters
    ----------
    df : pd.DataFrame
        Raw dataframe containing Date, Open, High, Low, Close, etc.
    ticker_name : str
        Descriptive ticker name for logging.

    Returns
    -------
    pd.DataFrame
        Cleaned, validated, and sorted DataFrame indexed by Date.

    Raises
    ------
    ValueError
        If required columns are missing or price anomalies (<=0) exist.
    """
    logger.info("Cleaning '%s' series...", ticker_name)

    if "Date" not in df.columns:
        raise ValueError(f"Missing required 'Date' column in {ticker_name}")

    # Standardize Date to datetime and normalize to YYYY-MM-DD
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.normalize()

    # Drop invalid dates if any
    null_dates = df["Date"].isna().sum()
    if null_dates > 0:
        logger.warning("Dropping %d rows with invalid dates in %s", null_dates, ticker_name)
        df = df.dropna(subset=["Date"])

    # Remove duplicate dates, keeping the first occurrence
    dup_count = df.duplicated(subset=["Date"]).sum()
    if dup_count > 0:
        logger.warning("Found %d duplicate dates in %s; retaining first.", dup_count, ticker_name)
        df = df.drop_duplicates(subset=["Date"], keep="first")

    # Sort chronologically (earliest to latest)
    df = df.sort_values(by="Date").reset_index(drop=True)

    # Standardize column names
    col_map = {c: c.strip().replace(" ", "_") for c in df.columns}
    df = df.rename(columns=col_map)

    # Validate essential price column
    target_col = "Close" if "Close" in df.columns else "Adj_Close"
    if target_col not in df.columns:
        raise ValueError(f"Neither 'Close' nor 'Adj_Close' found in {ticker_name} dataset")

    # Drop null price rows (e.g. trading holidays where exchange reported empty session)
    df = df.dropna(subset=[target_col]).reset_index(drop=True)

    # Sanity check: prices must be strictly positive
    if (df[target_col] <= 0).any():
        raise ValueError(f"Found non-positive price values in {ticker_name} column '{target_col}'")

    return df


def compute_nifty_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Compute simple and log returns for NIFTY 50 index series.

    Formulas:
    - Log Return: r_t = ln(P_t / P_{t-1}) = ln(P_t) - ln(P_{t-1})
    - Simple Return: R_t = (P_t - P_{t-1}) / P_{t-1}

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned NIFTY 50 DataFrame with strictly chronological 'Date' and 'Close'.

    Returns
    -------
    pd.DataFrame
        DataFrame with added 'log_return' and 'simple_return' columns.
    """
    df = df.copy()

    # Log returns: r_t = ln(Close_t) - ln(Close_{t-1})
    # Strictly backward-looking: uses Close at t and Close at t-1 (no look-ahead)
    df["log_return"] = np.log(df["Close"]) - np.log(df["Close"].shift(1))

    # Simple percentage return for comparison / verification: (Close_t - Close_{t-1}) / Close_{t-1}
    df["simple_return"] = df["Close"].pct_change(1)

    return df


def compute_vix_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute daily implied volatility and changes for India VIX series.

    Formulas:
    - Daily Implied Volatility: sigma_daily_implied = VIX_t / (100 * sqrt(252))
    - Daily VIX Absolute Change: Delta_VIX_t = VIX_t - VIX_{t-1}
    - Daily VIX Log Return: r_vix_t = ln(VIX_t) - ln(VIX_{t-1})

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned India VIX DataFrame with chronological 'Date' and 'Close'.

    Returns
    -------
    pd.DataFrame
        DataFrame with added VIX risk metrics.
    """
    df = df.copy()

    # India VIX is quoted as an annualized volatility percentage (e.g. 15.0 = 15% p.a.)
    # Daily implied volatility = (VIX / 100) / sqrt(252)
    df["vix_daily_implied"] = (df["Close"] / 100.0) / ANNUALISATION_FACTOR

    # Day-over-day changes
    df["vix_change"] = df["Close"] - df["Close"].shift(1)
    df["vix_log_return"] = np.log(df["Close"]) - np.log(df["Close"].shift(1))

    return df


def merge_nifty_and_vix(nifty_df: pd.DataFrame, vix_df: pd.DataFrame) -> pd.DataFrame:
    """Merge Nifty 50 and India VIX on aligned trading calendar dates.

    Preserves strict point-in-time integrity via an inner join.
    No future values or look-ahead interpolation is used.

    Parameters
    ----------
    nifty_df : pd.DataFrame
        Cleaned Nifty 50 DataFrame.
    vix_df : pd.DataFrame
        Cleaned India VIX DataFrame.

    Returns
    -------
    pd.DataFrame
        Merged dataset containing aligned NIFTY 50 and India VIX metrics.
    """
    nifty_sub = nifty_df[
        ["Date", "Open", "High", "Low", "Close", "Volume", "log_return", "simple_return"]
    ].rename(
        columns={
            "Open": "nifty_open",
            "High": "nifty_high",
            "Low": "nifty_low",
            "Close": "nifty_close",
            "Volume": "nifty_volume",
            "log_return": "nifty_log_return",
            "simple_return": "nifty_simple_return",
        }
    )

    vix_cols = [
        "Date",
        "Open",
        "High",
        "Low",
        "Close",
        "vix_daily_implied",
        "vix_change",
        "vix_log_return",
    ]
    vix_sub = vix_df[vix_cols].rename(
        columns={
            "Open": "vix_open",
            "High": "vix_high",
            "Low": "vix_low",
            "Close": "vix_close",
        }
    )

    merged = pd.merge(nifty_sub, vix_sub, on="Date", how="inner")
    merged = merged.sort_values(by="Date").reset_index(drop=True)

    # First row will have NaN for returns (as t-1 does not exist in dataset)
    # We drop the very first row so that all retained rows have valid returns
    clean_merged = merged.dropna(subset=["nifty_log_return", "vix_change"]).reset_index(drop=True)
    logger.info("Merged NIFTY 50 and India VIX: %d common trading sessions.", len(clean_merged))
    return clean_merged


def run_pipeline() -> None:
    """Execute end-to-end cleaning and feature derivation pipeline."""
    CLEAN_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load raw data
    nifty_raw = load_raw_dataset(RAW_DATA_DIR / "nifty50_raw.csv")
    vix_raw = load_raw_dataset(RAW_DATA_DIR / "india_vix_raw.csv")

    # 2. Clean individual series
    nifty_clean = clean_price_series(nifty_raw, "NIFTY 50")
    vix_clean = clean_price_series(vix_raw, "India VIX")

    # 3. Compute returns & risk metrics
    nifty_returns = compute_nifty_returns(nifty_clean)
    vix_metrics = compute_vix_metrics(vix_clean)

    # 4. Align & merge datasets on trading dates
    merged_daily = merge_nifty_and_vix(nifty_returns, vix_metrics)

    # 5. Export clean datasets
    nifty_returns.to_csv(CLEAN_DATA_DIR / "nifty50_clean.csv", index=False)
    vix_metrics.to_csv(CLEAN_DATA_DIR / "india_vix_clean.csv", index=False)
    merged_daily.to_csv(CLEAN_DATA_DIR / "nifty_vix_daily.csv", index=False)

    logger.info("Data cleaning completed. Output saved to %s", CLEAN_DATA_DIR)


def main() -> None:
    """Main CLI entry point."""
    try:
        run_pipeline()
    except Exception as err:
        logger.error("Cleaning failed: %s", err)
        sys.exit(1)


if __name__ == "__main__":
    main()
