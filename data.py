from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd
import requests


@dataclass(frozen=True)
class StooqDownloadSpec:
    """
    Stooq CSV endpoint (daily):
      https://stooq.com/q/d/l/?s=<SYMBOL>&i=d

    Example symbol: aapl.us, msft.us, spy.us
    """
    symbol: str
    interval: str = "d"  # d=day, w=week, m=month (if supported)


def stooq_csv_url(spec: StooqDownloadSpec) -> str:
    symbol = spec.symbol.strip().lower()
    return f"https://stooq.com/q/d/l/?s={symbol}&i={spec.interval}"


def download_stooq_ohlcv(
    symbol: str,
    cache_dir: Path,
    force: bool = False,
    timeout_s: int = 20,
) -> Path:
    """
    Downloads daily OHLCV as CSV into cache_dir and returns the local file path.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    out_path = cache_dir / f"{symbol.lower().replace('/', '_')}_stooq_d.csv"
    if out_path.exists() and not force:
        return out_path

    url = stooq_csv_url(StooqDownloadSpec(symbol=symbol))
    resp = requests.get(url, timeout=timeout_s)
    resp.raise_for_status()

    out_path.write_bytes(resp.content)
    return out_path


def load_ohlcv_csv(path: Path) -> pd.DataFrame:
    """
    Loads a Stooq OHLCV CSV into a canonical DataFrame:
      index: pd.DatetimeIndex named 'Date'
      columns: Open, High, Low, Close, Volume (floats/int)
    """
    df = pd.read_csv(path)
    # Stooq typically uses these columns for daily data:
    # Date,Open,High,Low,Close,Volume
    required = {"Date", "Open", "High", "Low", "Close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns {missing}. Got columns: {list(df.columns)}")

    df["Date"] = pd.to_datetime(df["Date"], utc=False)
    df = df.sort_values("Date").set_index("Date")

    # Ensure numeric types
    for c in ["Open", "High", "Low", "Close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if "Volume" in df.columns:
        df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0).astype("int64")
    else:
        df["Volume"] = 0

    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    return df
