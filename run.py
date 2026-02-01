from __future__ import annotations

import argparse
from pathlib import Path
import json

import matplotlib.pyplot as plt
import pandas as pd

from .data import download_stooq_ohlcv, load_ohlcv_csv
from .strategy import MACrossoverParams, generate_ma_crossover_signals
from .broker import ExecutionModel, simulate_fill
from .portfolio import Portfolio, RiskLimits
from .metrics import compute_metrics


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Event-driven backtester using Stooq CSV (daily OHLCV).")
    p.add_argument("--ticker", required=True, help="Stooq symbol e.g. aapl.us, msft.us, spy.us")
    p.add_argument("--start", default=None, help="Start date YYYY-MM-DD")
    p.add_argument("--end", default=None, help="End date YYYY-MM-DD")

    p.add_argument("--fast", type=int, default=20, help="Fast MA window")
    p.add_argument("--slow", type=int, default=100, help="Slow MA window")
    p.add_argument("--cash", type=float, default=100000, help="Initial cash")

    p.add_argument("--slippage-bps", type=float, default=2.0, help="Slippage in basis points")
    p.add_argument("--commission", type=float, default=1.0, help="Fixed commission per trade")

    p.add_argument("--max-position-pct", type=float, default=0.25, help="Max position value as % of equity")
    p.add_argument("--max-dd", type=float, default=0.20, help="Max drawdown before kill switch")

    p.add_argument("--cache-dir", default="data", help="Local cache directory for downloaded CSV")
    p.add_argument("--out-dir", default="outputs", help="Output directory")
    p.add_argument("--force-download", action="store_true", help="Force re-download CSV even if cached")

    return p.parse_args()


def main() -> None:
    args = parse_args()
    cache_dir = Path(args.cache_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = download_stooq_ohlcv(args.ticker, cache_dir=cache_dir, force=args.force_download)
    ohlcv = load_ohlcv_csv(csv_path)

    if args.start:
        ohlcv = ohlcv.loc[pd.to_datetime(args.start):]
    if args.end:
        ohlcv = ohlcv.loc[:pd.to_datetime(args.end)]

    if len(ohlcv) < max(args.fast, args.slow) + 2:
        raise ValueError("Not enough data for the chosen MA windows.")

    params = MACrossoverParams(fast=args.fast, slow=args.slow)
    targets = generate_ma_crossover_signals(ohlcv, params=params, long_only=True)

    exec_model = ExecutionModel(slippage_bps=args.slippage_bps, commission=args.commission)
    limits = RiskLimits(max_position_pct=args.max_position_pct, max_drawdown=args.max_dd)
    portfolio = Portfolio(initial_cash=args.cash, limits=limits)

    # Event-driven loop (daily bars):
    # - Mark portfolio at today's close
    # - If a target exists today, place order to be filled next day's open
    # - Fill happens next day open
    dates = ohlcv.index
    pending_target = None  # target_position to execute at next open

    for i in range(len(dates)):
        dt = dates[i]
        row = ohlcv.iloc[i]

        # Mark-to-market at close
        portfolio.mark_to_market(date=dt, close_price=float(row["Close"]))

        # Execute pending target at today's OPEN
        if pending_target is not None and not portfolio.kill_switch:
            open_px = float(row["Open"])
            # Determine trade (delta) and fill
            # Side depends on whether we need to buy or sell
            # We simulate the fill price with slippage; commission comes from model
            # We call rebalance_to_target with both open_price (for sizing) and fill_price (for execution).
            # We don't know the side upfront; portfolio figures delta internally.
            # So we compute a "neutral" fill by applying slippage in the correct direction once delta is known.
            # Easiest: compute desired_qty first via portfolio's sizing logic by calling rebalance with a fill
            # that assumes worst-case? Instead: we approximate using fill at open, and portfolio will compute delta.
            # Then we apply slippage per delta direction.
            # Two-step: compute delta implied by target_position vs current.
            equity = portfolio.cash + portfolio.position_qty * open_px
            max_qty = int((limits.max_position_pct * equity) // open_px)
            desired_qty = max_qty if pending_target == 1 else 0
            delta = desired_qty - portfolio.position_qty
            if delta != 0:
                side = 1 if delta > 0 else -1
                fill_px, comm = simulate_fill(open_px, side=side, qty=abs(delta), model=exec_model)
                portfolio.rebalance_to_target(
                    date=dt,
                    target_position=int(pending_target),
                    open_price=open_px,
                    fill_price=fill_px,
                    commission=comm,
                )

        # Create next day's pending order based on today's target (signal)
        pending_target = int(targets.loc[dt]) if pd.notna(targets.loc[dt]) else 0

    eq_df = pd.DataFrame(portfolio.equity_curve).set_index("Date")
    trades_df = pd.DataFrame([t.__dict__ for t in portfolio.trades])

    # Save outputs
    eq_path = out_dir / "equity_curve.csv"
    tr_path = out_dir / "trades.csv"
    eq_df.to_csv(eq_path)
    trades_df.to_csv(tr_path, index=False) if len(trades_df) else tr_path.write_text("", encoding="utf-8")

    perf = compute_metrics(eq_df)
    metrics_path = out_dir / "metrics.json"
    metrics_path.write_text(json.dumps(perf.__dict__, indent=2), encoding="utf-8")

    # Plot
    plt.figure()
    eq_df["Equity"].plot()
    plt.title(f"Equity Curve: {args.ticker.upper()} | MA({args.fast},{args.slow})")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.tight_layout()
    fig_path = out_dir / "equity_curve.png"
    plt.savefig(fig_path)

    print("Done.")
    print(f"Data:      {csv_path}")
    print(f"Equity:    {eq_path}")
    print(f"Trades:    {tr_path}")
    print(f"Metrics:   {metrics_path}")
    print(f"Plot:      {fig_path}")
    print(f"KillSwitch triggered? {bool(eq_df['KillSwitch'].iloc[-1])}")


if __name__ == "__main__":
    main()
