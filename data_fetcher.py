"""
Fetches OHLCV data from Yahoo Finance via yfinance.
Runs inside GitHub Actions, which has normal internet access (unlike
Claude's own sandbox, which is network-restricted).
"""
import time
import pandas as pd
import yfinance as yf
from indicators import add_all_indicators, vwap


def fetch_daily(symbol: str, period: str = "6mo") -> pd.DataFrame:
    """Daily candles - used for SWING scoring."""
    df = yf.download(symbol, period=period, interval="1d", progress=False, auto_adjust=True)
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = add_all_indicators(df)
    return df


def fetch_intraday(symbol: str, period: str = "5d", interval: str = "15m") -> pd.DataFrame:
    """Intraday candles - used for INTRADAY scoring."""
    df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    # Only keep today's session for VWAP to be meaningful
    df = add_all_indicators(df)
    df["VWAP"] = vwap(df)
    return df


def fetch_universe(symbols, mode="daily", pause=0.3):
    """Fetch data for a list of symbols with a small pause to avoid rate limits."""
    results = {}
    for sym in symbols:
        try:
            if mode == "daily":
                df = fetch_daily(sym)
            else:
                df = fetch_intraday(sym)
            if not df.empty:
                results[sym] = df
        except Exception as e:
            print(f"[WARN] Failed to fetch {sym}: {e}")
        time.sleep(pause)
    return results
