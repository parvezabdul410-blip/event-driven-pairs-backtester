from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import pandas as pd


@dataclass
class RiskLimits:
    max_position_pct: float = 0.25   # max position value as % of equity
    max_drawdown: float = 0.20       # stop trading if peak-to-trough DD exceeds this


@dataclass
class Trade:
    date: pd.Timestamp
    side: str
    qty: int
    price: float
    notional: float
    commission: float


class Portfolio:
    def __init__(self, initial_cash: float, limits: RiskLimits):
        if initial_cash <= 0:
            raise ValueError("initial_cash must be > 0")
        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.position_qty = 0
        self.limits = limits

        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []

        self._peak_equity = self.initial_cash
        self._kill_switch = False

    @property
    def kill_switch(self) -> bool:
        return self._kill_switch

    def mark_to_market(self, date: pd.Timestamp, close_price: float) -> None:
        equity = self.cash + self.position_qty * close_price
        self._peak_equity = max(self._peak_equity, equity)
        dd = 0.0 if self._peak_equity == 0 else (self._peak_equity - equity) / self._peak_equity
        if dd >= self.limits.max_drawdown:
            self._kill_switch = True

        self.equity_curve.append(
            {
                "Date": date,
                "Cash": self.cash,
                "PositionQty": self.position_qty,
                "Close": close_price,
                "Equity": equity,
                "Drawdown": dd,
                "KillSwitch": self._kill_switch,
            }
        )

    def _max_allowed_qty(self, equity: float, price: float) -> int:
        max_pos_value = self.limits.max_position_pct * equity
        return int(max_pos_value // price)

    def rebalance_to_target(
        self,
        date: pd.Timestamp,
        target_position: int,
        open_price: float,
        fill_price: float,
        commission: float,
    ) -> Optional[Trade]:
        """
        Long-only targets: 0 or 1
        Executes trade at fill_price.
        """
        if self._kill_switch:
            return None

        # Equity computed at open (approx): cash + position*open_price
        equity = self.cash + self.position_qty * open_price

        if target_position not in (0, 1):
            raise ValueError("target_position must be 0 or 1 for long-only")

        desired_qty = 0
        if target_position == 1:
            desired_qty = self._max_allowed_qty(equity=equity, price=open_price)

        delta = desired_qty - self.position_qty
        if delta == 0:
            return None

        side = "BUY" if delta > 0 else "SELL"
        qty = abs(delta)
        notional = qty * fill_price

        if side == "BUY":
            total_cost = notional + commission
            if total_cost > self.cash:
                # Clamp buy qty to affordable
                affordable_qty = int((self.cash - commission) // fill_price)
                if affordable_qty <= 0:
                    return None
                qty = affordable_qty
                notional = qty * fill_price
                total_cost = notional + commission
            self.cash -= total_cost
            self.position_qty += qty
        else:
            # SELL
            self.cash += notional - commission
            self.position_qty -= qty

        t = Trade(
            date=date,
            side=side,
            qty=qty,
            price=float(fill_price),
            notional=float(notional),
            commission=float(commission),
        )
        self.trades.append(t)
        return t
