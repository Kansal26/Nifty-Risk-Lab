"""Data ingestion module for nifty-risk-lab.

Downloads daily OHLCV historical market data from 2015-01-01 to present
for all core asset classes and risk proxies:
1. NIFTY 50 (^NSEI) - Indian benchmark equity index
2. Bank NIFTY (^NSEBANK) - High-beta Indian banking index
3. India VIX (^INDIAVIX) - Indian 30-day implied volatility
4. S&P 500 (^GSPC) - Global equity risk benchmark
5. Brent Crude Oil (BZ=F) - Energy input / macro commodity proxy
6. USD/INR (INR=X) - Foreign exchange / currency risk proxy
7. US 10Y Yield (^TNX) - Global risk-free rate / cost of capital proxy

Rules:
- Never invent, estimate, or substitute data. If a source fails, halt and stop.
- Inspect ^INDIAVIX specifically for failures or large gaps.
- Save raw files untouched in data/raw/.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path("data/raw")
START_DATE = "2015-01-01"

TICKERS: dict[str, str] = {
    "nifty50": "^NSEI",
    "bank_nifty": "^NSEBANK",
    "india_vix": "^INDIAVIX",
    "sp500": "^GSPC",
    "brent_crude": "BZ=F",
    "usdinr": "INR=X",
    "us10y_yield": "^TNX",
}


def download_ticker_data(
    ticker: str, start_date: str = START_DATE, end_date: str | None = None
) -> pd.DataFrame:
    """Download daily historical data for a ticker symbol using yfinance.

    Parameters
    ----------
    ticker : str
        Ticker symbol on Yahoo Finance.
    start_date : str
        Start date in 'YYYY-MM-DD' format.
    end_date : str, optional
        End date in 'YYYY-MM-DD' format. Defaults to None (today).

    Returns
    -------
    pd.DataFrame
        Downloaded raw OHLCV dataframe.

    Raises
    ------
    RuntimeError
        If data download fails or returns an empty dataset.
    """
    logger.info("Downloading '%s' from %s to %s...", ticker, start_date, end_date or "present")
    try:
        df = yf.download(
            tickers=ticker,
            start=start_date,
            end=end_date,
            interval="1d",
            auto_adjust=False,
            progress=False,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Fatal: Failed to connect to Yahoo Finance or download '{ticker}': {exc}"
        ) from exc

    if df is None or df.empty:
        raise RuntimeError(
            f"Fatal: No data returned for ticker '{ticker}' for range [{start_date}, {end_date}]. "
            "Execution halted in accordance with project rules (no synthetic data)."
        )

    # Flatten multi-index columns if returned by yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    df = df.reset_index()
    logger.info("Downloaded %d rows for '%s'.", len(df), ticker)
    return df


def audit_india_vix(df: pd.DataFrame) -> None:
    """Inspect India VIX dataset for missing sections or large unexpected gaps.

    Parameters
    ----------
    df : pd.DataFrame
        Raw India VIX dataset.

    Raises
    ------
    RuntimeError
        If India VIX exhibits critical failures or unexpected prolonged gaps (> 10 calendar days).
    """
    if "Date" not in df.columns:
        raise RuntimeError("Fatal: India VIX dataset missing 'Date' column.")

    dates = pd.to_datetime(df["Date"]).sort_values().reset_index(drop=True)
    calendar_diffs = dates.diff().dt.days

    # Identify any gap strictly greater than 10 calendar days (which would exceed long holidays)
    large_gaps = calendar_diffs[calendar_diffs > 10]
    if not large_gaps.empty:
        gap_indices = large_gaps.index
        gap_details = [
            (
                f"From {dates.iloc[idx - 1].strftime('%Y-%m-%d')} to "
                f"{dates.iloc[idx].strftime('%Y-%m-%d')} ({large_gaps.loc[idx]} days)"
            )
            for idx in gap_indices
        ]
        logger.error(
            "CRITICAL: ^INDIAVIX has large gap(s) exceeding 10 calendar days:\n%s",
            "\n".join(gap_details),
        )
        raise RuntimeError(
            f"^INDIAVIX has large data gaps: {gap_details}. "
            "Execution stopped. Please download India VIX manually from NSE."
        )

    logger.info(
        "^INDIAVIX audit passed: %d observations between %s and %s with no abnormal gaps.",
        len(dates),
        dates.min().strftime("%Y-%m-%d"),
        dates.max().strftime("%Y-%m-%d"),
    )


def save_raw_data(df: pd.DataFrame, file_path: Path) -> None:
    """Save raw data to CSV file untouched.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to save.
    file_path : Path
        Destination file path.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, index=False)
    logger.info("Saved raw dataset to %s", file_path)


def run_pipeline() -> None:
    """Execute download pipeline for all project tickers and save untouched raw files."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    downloaded: dict[str, pd.DataFrame] = {}
    for name, ticker in TICKERS.items():
        df = download_ticker_data(ticker, start_date=START_DATE)
        if name == "india_vix":
            audit_india_vix(df)
        downloaded[name] = df

    for name, df in downloaded.items():
        dest_path = RAW_DATA_DIR / f"{name}_raw.csv"
        save_raw_data(df, dest_path)

    logger.info("All 7 raw market datasets downloaded and saved untouched.")


def main() -> None:
    """Main CLI entry point."""
    try:
        run_pipeline()
    except Exception as err:
        logger.error("Download failed: %s", err)
        sys.exit(1)


if __name__ == "__main__":
    main()
