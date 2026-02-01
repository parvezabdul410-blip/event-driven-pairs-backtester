from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple
import math


@dataclass(frozen=True)
class ExecutionModel:
    """
    Simple execution model:
    - Fills at next bar OPEN price
    - Applies slippage in basis points (bps) on notional
    - Applies fixed commission per trade
    """
    slippage_bps: float = 2.0
    commission: float = 1.0


def apply_slippage(price: float, side: int, slippage_bps: float) -> float:
    """
    side: +1 buy, -1 sell
    """
    if price <= 0:
        raise ValueError("Price must be > 0")
    slip = slippage_bps / 10000.0
    # buys pay up, sells receive less
    return price * (1.0 + slip * side)


def simulate_fill(
    open_price_next: float,
    side: int,
    qty: int,
    model: ExecutionModel,
) -> Tuple[float, float]:
    """
    Returns (fill_price, total_costs) where total_costs includes commission.
    Slippage is embedded into fill_price via apply_slippage.
    """
    if qty <= 0:
        raise ValueError("qty must be positive")
    fill_px = apply_slippage(open_price_next, side=side, slippage_bps=model.slippage_bps)
    costs = model.commission
    return fill_px, costs
