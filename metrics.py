from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PerformanceMetrics:
    cagr: float
    vol: float
    sharpe: float
    max_drawdown: float
    total_return: float


def compute_metrics(equity_curve: pd.DataFrame, trading_days: int = 252) -> PerformanceMetrics:
    eq = equity_curve["Equity"].astype(float)
    rets = eq.pct_change().dropna()

    total_return = (eq.iloc[-1] / eq.iloc[0]) - 1.0
    years = max(1e-9, (eq.index[-1] - eq.index[0]).days / 365.25)
    cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1.0 / years) - 1.0 if years > 0 else 0.0

    vol = float(rets.std(ddof=1) * np.sqrt(trading_days)) if len(rets) > 1 else 0.0
    sharpe = float((rets.mean() / rets.std(ddof=1)) * np.sqrt(trading_days)) if rets.std(ddof=1) > 0 else 0.0

    dd = equity_curve["Drawdown"].astype(float)
    max_dd = float(dd.max()) if len(dd) else 0.0

    return PerformanceMetrics(
        cagr=float(cagr),
        vol=float(vol),
        sharpe=float(sharpe),
        max_drawdown=max_dd,
        total_return=float(total_return),
    )
