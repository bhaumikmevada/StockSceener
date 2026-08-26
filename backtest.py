"""
Backtests the SWING scoring logic against real historical NSE data.

For every trading day in the lookback window, this checks whether each
stock's data at that point in time would have triggered a swing signal.
If it did, it simulates holding the trade forward (up to 5 trading days)
to see whether the target or stop-loss was hit first.

This answers the real question: "if I had followed every signal this
system generated over the last year, what would my actual win rate and
average return have been?" No more guessing.

Run with: python backtest.py
Takes a few minutes for 50 stocks x 1 year of daily data.
"""
import pandas as pd
import numpy as np
import yfinance as yf
from indicators import add_all_indicators
from scoring import score_swing
from stock_list import NIFTY_50

LOOKBACK_PERIOD = "2y"     # how much history to test over
MAX_HOLD_DAYS = 5          # matches the "max 5 day" swing rule


def backtest_symbol(symbol):
    """Runs a walk-forward backtest for one symbol. Returns a list of trade results."""
    df = yf.download(symbol, period=LOOKBACK_PERIOD, interval="1d", progress=False, auto_adjust=True)
    if df.empty or len(df) < 80:
        return []
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = add_all_indicators(df)
    trades = []

    # Walk forward day by day. At each day, pretend "today" is the latest
    # known data (i.e. only use data up to and including this row) and see
    # if a signal would have fired.
    for i in range(60, len(df) - 1):  # need enough history before, and room to look forward
        window = df.iloc[:i + 1]
        signal = score_swing(window, symbol)
        if not signal:
            continue

        entry = signal["entry"]
        target = signal["target"]
        sl = signal["stop_loss"]
        entry_date = df.index[i]

        # Look forward up to MAX_HOLD_DAYS trading days to see what happens first
        outcome = "TIMEOUT"
        exit_price = None
        exit_day_offset = None
        forward = df.iloc[i + 1: i + 1 + MAX_HOLD_DAYS]
        for offset, (fdate, frow) in enumerate(forward.iterrows(), start=1):
            hit_target = frow["High"] >= target
            hit_sl = frow["Low"] <= sl
            if hit_target and hit_sl:
                # Both touched same day - assume the worse case (SL) for a conservative estimate
                outcome = "SL"
                exit_price = sl
                exit_day_offset = offset
                break
            elif hit_target:
                outcome = "TARGET"
                exit_price = target
                exit_day_offset = offset
                break
            elif hit_sl:
                outcome = "SL"
                exit_price = sl
                exit_day_offset = offset
                break

        if outcome == "TIMEOUT" and len(forward) > 0:
            exit_price = forward.iloc[-1]["Close"]
            exit_day_offset = len(forward)

        if exit_price is None:
            continue  # not enough forward data (near end of dataset)

        pnl_pct = (exit_price - entry) / entry * 100

        trades.append({
            "symbol": symbol,
            "entry_date": str(entry_date.date()),
            "score": signal["score"],
            "entry": entry,
            "target": target,
            "sl": sl,
            "outcome": outcome,
            "exit_price": round(exit_price, 2),
            "days_held": exit_day_offset,
            "pnl_pct": round(pnl_pct, 2),
        })

    return trades


def run_backtest():
    all_trades = []
    for sym in NIFTY_50:
        print(f"[BACKTEST] Testing {sym}...")
        try:
            trades = backtest_symbol(sym)
            all_trades.extend(trades)
            print(f"  -> {len(trades)} historical signals found")
        except Exception as e:
            print(f"  -> [ERROR] {e}")

    if not all_trades:
        print("\nNo trades generated - check data access or scoring thresholds.")
        return

    df_trades = pd.DataFrame(all_trades)

    total = len(df_trades)
    wins = (df_trades["outcome"] == "TARGET").sum()
    losses = (df_trades["outcome"] == "SL").sum()
    timeouts = (df_trades["outcome"] == "TIMEOUT").sum()
    win_rate = wins / total * 100 if total else 0
    avg_pnl = df_trades["pnl_pct"].mean()
    avg_win_pnl = df_trades.loc[df_trades["outcome"] == "TARGET", "pnl_pct"].mean()
    avg_loss_pnl = df_trades.loc[df_trades["outcome"] == "SL", "pnl_pct"].mean()
    avg_hold = df_trades["days_held"].mean()

    print("\n" + "=" * 50)
    print("BACKTEST RESULTS - SWING STRATEGY")
    print("=" * 50)
    print(f"Total signals tested over {LOOKBACK_PERIOD}: {total}")
    print(f"Target hit (win):   {wins}  ({win_rate:.1f}%)")
    print(f"Stop-loss hit:      {losses}  ({losses/total*100:.1f}%)")
    print(f"Timeout (exit at close, day {MAX_HOLD_DAYS}): {timeouts}  ({timeouts/total*100:.1f}%)")
    print(f"Average return per trade: {avg_pnl:.2f}%")
    print(f"Average return on wins:   {avg_win_pnl:.2f}%")
    print(f"Average return on losses: {avg_loss_pnl:.2f}%")
    print(f"Average holding period:   {avg_hold:.1f} days")
    print("=" * 50)

    df_trades.to_csv("backtest_results.csv", index=False)
    print("\nFull trade-by-trade log saved to backtest_results.csv")


if __name__ == "__main__":
    run_backtest()
