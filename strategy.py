from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class MACrossoverParams:
    fast: int = 20
    slow: int = 100


def generate_ma_crossover_signals(
    ohlcv: pd.DataFrame,
    params: MACrossoverParams,
    long_only: bool = True,
) -> pd.Series:
    """
    Returns a Series of target positions (0 or 1 for long-only).
    Signals are based on close price moving averages.

    Position is applied on the *next bar* by the broker model.
    """
    close = ohlcv["Close"].copy()
    fast_ma = close.rolling(params.fast, min_periods=params.fast).mean()
    slow_ma = close.rolling(params.slow, min_periods=params.slow).mean()

    # signal: 1 when fast > slow else 0 (long-only)
    raw = (fast_ma > slow_ma).astype(int)
    if not long_only:
        # -1 when fast < slow else +1 (ignore equals)
        raw = raw.replace({0: -1})
        raw[fast_ma == slow_ma] = 0

    # target position time series aligned to dates
    raw.name = "target_position"
    return raw
