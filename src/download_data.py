"""Data ingestion module for nifty-risk-lab.

Downloads daily OHLCV historical market data for NIFTY 50 (^NSEI)
and India VIX (^INDIAVIX) from Yahoo Finance.

Rule Compliance:
- Never invents, estimates, or substitutes data. If the download fails or returns empty data,
  it halts execution with an explicit error.
- Pure raw ingestion; no forward-looking calculations applied at this stage.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path("data/raw")
TICKERS = {
    "nifty50": "^NSEI",
    "india_vix": "^INDIAVIX",
}
START_DATE = "2015-01-01"


def download_ticker_data(
    ticker: str, start_date: str = START_DATE, end_date: str | None = None
) -> pd.DataFrame:
    """Download daily historical data for a ticker symbol using yfinance.

    Parameters
    ----------
    ticker : str
        Ticker symbol on Yahoo Finance (e.g., '^NSEI', '^INDIAVIX').
    start_date : str
        Start date in 'YYYY-MM-DD' format.
    end_date : str, optional
        End date in 'YYYY-MM-DD' format. Defaults to None (today).

    Returns
    -------
    pd.DataFrame
        Downloaded OHLCV historical dataframe.

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


def save_raw_data(df: pd.DataFrame, file_path: Path) -> None:
    """Save raw data to CSV file.

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
    """Execute ingestion pipeline for all project tickers."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    for name, ticker in TICKERS.items():
        df = download_ticker_data(ticker, start_date=START_DATE)
        dest_path = RAW_DATA_DIR / f"{name}_raw.csv"
        save_raw_data(df, dest_path)

    logger.info("Data ingestion completed successfully.")


def main() -> None:
    """Main CLI entry point."""
    try:
        run_pipeline()
    except Exception as err:
        logger.error("Download failed: %s", err)
        sys.exit(1)


if __name__ == "__main__":
    main()
