# Event-Driven Pairs Trading Backtester

## Overview

This project is an **event-driven backtesting engine** for statistical arbitrage strategies, implemented entirely in Python.  
It simulates a **pairs trading strategy** on historical equity price data and tracks portfolio performance over time.

The system is designed to reflect how real **quantitative trading systems** are structured, separating data handling, strategy logic, execution, and portfolio accounting.

---

## Strategy Description

The implemented strategy is a **mean-reversion pairs trade**:

1. Two correlated stocks are selected (e.g., Coca-Cola and Pepsi).
2. The log-price spread is computed:
   spread_t = log(P_A) − log(P_B)
3. A rolling mean and standard deviation are used to compute the spread’s **z-score**.
4. Trading logic:
   - **Enter positions** when |z| > z_entry  
     - Long the undervalued asset  
     - Short the overvalued asset
   - **Exit positions** when |z| < z_exit
5. Positions are sized using a fixed notional per leg.

---

## Project Structure

```
event-driven-pairs-backtester/
├─ backtest.py
├─ KO.csv
├─ PEP.csv
├─ requirements.txt
├─ .gitignore
└─ README.md
```

---

## Features

- Event-driven simulation (market → signal → order → fill)
- Z-score based statistical arbitrage strategy
- Long/short portfolio tracking
- Equity curve generation
- Performance metrics:
  - Total return
  - Sharpe ratio
  - Maximum drawdown
- Portfolio equity visualization

---

## Requirements

- Python 3.9+
- Dependencies:
  - numpy
  - pandas
  - matplotlib

Install dependencies with:

```
pip install -r requirements.txt
```

---

## Run Instructions

### 1. Clone the repository

```
git clone https://github.com/<your-username>/event-driven-pairs-backtester.git
cd event-driven-pairs-backtester
```

### 2. (Optional) Create a virtual environment

macOS / Linux:
```
python3 -m venv .venv
source .venv/bin/activate
```

Windows:
```
python -m venv .venv
.\.venv\Scripts\activate
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

### 4. Run the backtest

```
python backtest.py
```

---

## Run Example

```
$ python backtest.py
Final equity: 100842.17
Total return: 0.84%
Sharpe ratio: 1.21
Max drawdown: -0.37%
```

A plot of the portfolio equity curve will also be displayed.

---

## Customization

You can adjust strategy parameters directly in `backtest.py`:

```
lookback = 10
entry_z = 1.5
exit_z = 0.5
```

To test different assets, replace `KO.csv` and `PEP.csv` with new CSV files containing `Date` and `Close` columns.

---

## Extensions

Potential future improvements include:

- Transaction costs and slippage modeling
- Multiple trading pairs
- Dynamic position sizing
- Risk limits and leverage constraints
- Additional strategies (momentum, factor models)

---

## Disclaimer

This project is for **educational and research purposes only**.  
It does not constitute financial advice or a recommendation to trade securities.
