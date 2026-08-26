"""
Scoring engine for SWING (2-3 day hold) and INTRADAY setups.

IMPORTANT HONESTY NOTE (kept in code deliberately):
No score here claims or guarantees any "accuracy %". A score is a relative
ranking of how many favorable technical conditions align RIGHT NOW. It is
NOT a probability of profit. Treat scores as "how clean does this setup
look", not "how sure are we this will win".
"""
import numpy as np
import pandas as pd


def _clip(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def score_swing(df, symbol):
    """
    Swing setup: designed for a 2-3 day (max ~5 day) hold.
    Looks for: established uptrend + healthy (not overbought) momentum +
    volume confirmation + proximity to a breakout level.
    Returns None if data is insufficient or conditions are weak.
    """
    if len(df) < 55 or df[["EMA20", "EMA50", "RSI14", "ATR14"]].iloc[-1].isna().any():
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]
    close = last["Close"]

    reasons = []
    score = 0

    # 1) Trend filter (30 pts) - price above both EMAs, EMA20 above EMA50 (uptrend structure)
    trend_pts = 0
    if close > last["EMA20"] > last["EMA50"]:
        trend_pts = 30
        reasons.append("Uptrend: price > EMA20 > EMA50")
    elif close > last["EMA20"]:
        trend_pts = 15
        reasons.append("Above EMA20 but EMA structure not fully aligned")
    else:
        return None  # no counter-trend swing longs
    score += trend_pts

    # 2) Momentum filter (25 pts) - RSI in the "healthy" 45-65 zone, not overbought, not weak
    rsi_val = last["RSI14"]
    if 45 <= rsi_val <= 65:
        mom_pts = 25
        reasons.append(f"RSI {rsi_val:.0f} in healthy momentum zone")
    elif 40 <= rsi_val < 45 or 65 < rsi_val <= 72:
        mom_pts = 14
        reasons.append(f"RSI {rsi_val:.0f} acceptable but not ideal")
    else:
        mom_pts = 0
    score += mom_pts
    if mom_pts == 0:
        return None

    # 3) MACD confirmation (15 pts)
    macd_pts = 0
    if last["MACD_hist"] > 0 and last["MACD_hist"] >= prev["MACD_hist"]:
        macd_pts = 15
        reasons.append("MACD histogram positive and rising")
    elif last["MACD_hist"] > 0:
        macd_pts = 8
    score += macd_pts

    # 4) Volume confirmation (20 pts)
    vol_ratio = last["VolRatio20"]
    if vol_ratio >= 1.5:
        vol_pts = 20
        reasons.append(f"Volume {vol_ratio:.1f}x the 20-day average")
    elif vol_ratio >= 1.15:
        vol_pts = 12
        reasons.append(f"Volume {vol_ratio:.1f}x average (mild pickup)")
    else:
        vol_pts = 0
    score += vol_pts

    # 5) Breakout proximity (10 pts) - close to or above prior 20-day high
    high20 = last["High20"]
    if not np.isnan(high20):
        pct_from_high = (close - high20) / high20 * 100
        if close >= high20:
            score += 10
            reasons.append("Breaking above 20-day high")
        elif -2 <= pct_from_high < 0:
            score += 6
            reasons.append("Within 2% of 20-day high (breakout watch)")

    if score < 55:
        return None

    # --- Trade plan ---
    atr_val = last["ATR14"]
    entry = round(close, 2)
    sl = round(entry - 1.5 * atr_val, 2)               # wider SL: 1.5x ATR
    target = round(entry + 3.0 * atr_val, 2)            # 2:1 reward:risk, bigger move
    risk_pct = round((entry - sl) / entry * 100, 2)
    reward_pct = round((target - entry) / entry * 100, 2)
    rr_ratio = round((target - entry) / (entry - sl), 2) if entry > sl else None

    # Skip setups where the target move is too small to matter in rupee terms,
    # even if the R:R ratio looks fine on paper.
    if reward_pct < 3.5:
        return None

    return {
        "symbol": symbol,
        "type": "SWING",
        "score": round(score, 1),
        "close": entry,
        "entry": entry,
        "target": target,
        "stop_loss": sl,
        "risk_pct": risk_pct,
        "reward_pct": reward_pct,
        "rr_ratio": rr_ratio,
        "holding_days": "2-3 days (max 5)",
        "rsi": round(rsi_val, 1),
        "volume_ratio": round(vol_ratio, 2),
        "atr": round(atr_val, 2),
        "reasons": reasons,
    }


def score_intraday(df, symbol, daily_df=None):
    """
    Intraday setup: uses recent intraday bars (5m/15m). Looks for opening
    range strength, VWAP position, RSI momentum, and relative volume.

    daily_df (optional): the stock's daily-chart data. When provided, this
    adds a multi-timeframe filter - only intraday longs that also align
    with a healthy daily trend are allowed. This cuts down on setups that
    look strong for an hour but are fighting the bigger trend.
    """
    if len(df) < 30 or df[["EMA9", "EMA20", "RSI14", "ATR14"]].iloc[-1].isna().any():
        return None

    last = df.iloc[-1]
    close = last["Close"]
    reasons = []
    score = 0

    # 0) Skip the opening 30 minutes - the most erratic, least reliable window
    last_time = df.index[-1]
    if hasattr(last_time, "time"):
        market_open_plus_30 = last_time.replace(hour=9, minute=45, second=0, microsecond=0)
        if last_time < market_open_plus_30:
            return None

    # 0b) Multi-timeframe filter - daily trend should not be against us
    if daily_df is not None and len(daily_df) >= 55:
        d_last = daily_df.iloc[-1]
        if not pd.isna(d_last.get("EMA50", float("nan"))):
            if d_last["Close"] < d_last["EMA50"]:
                return None  # daily downtrend - skip intraday longs regardless of 15m picture

    # 1) VWAP position (25 pts)
    vwap_val = last.get("VWAP", np.nan)
    if not np.isnan(vwap_val):
        if close > vwap_val:
            score += 25
            reasons.append("Trading above VWAP")
        else:
            return None  # skip intraday longs below VWAP

    # 2) Short-term trend (25 pts)
    if close > last["EMA9"] > last["EMA20"]:
        score += 25
        reasons.append("Price > EMA9 > EMA20 (short-term uptrend)")
    elif close > last["EMA9"]:
        score += 12

    # 3) RSI momentum (20 pts) - tightened band, avoid late/overbought entries
    rsi_val = last["RSI14"]
    if 52 <= rsi_val <= 68:
        score += 20
        reasons.append(f"RSI {rsi_val:.0f} shows active bullish momentum")
    elif 48 <= rsi_val < 52:
        score += 8

    # 4) Relative volume (20 pts) - raised bar, needs real participation
    vol_ratio = last["VolRatio20"]
    if vol_ratio >= 2.5:
        score += 20
        reasons.append(f"Relative volume {vol_ratio:.1f}x - strong participation")
    elif vol_ratio >= 1.6:
        score += 10

    # 5) MACD confirmation (10 pts)
    if last["MACD_hist"] > 0:
        score += 10
        reasons.append("MACD histogram positive")

    if score < 65:  # raised from 55 - only cleaner setups pass now
        return None

    atr_val = last["ATR14"]
    entry = round(close, 2)
    sl = round(entry - 1.0 * atr_val, 2)      # slightly wider SL for intraday
    target = round(entry + 2.0 * atr_val, 2)  # 2:1, bigger move
    risk_pct = round((entry - sl) / entry * 100, 2)
    reward_pct = round((target - entry) / entry * 100, 2)
    rr_ratio = round((target - entry) / (entry - sl), 2) if entry > sl else None

    # Skip setups with too small an absolute move to be worth the trade
    if reward_pct < 1.0:
        return None

    return {
        "symbol": symbol,
        "type": "INTRADAY",
        "score": round(score, 1),
        "close": entry,
        "entry": entry,
        "target": target,
        "stop_loss": sl,
        "risk_pct": risk_pct,
        "reward_pct": reward_pct,
        "rr_ratio": rr_ratio,
        "holding_days": "Same day (exit by 3:15 PM)",
        "rsi": round(rsi_val, 1),
        "volume_ratio": round(vol_ratio, 2),
        "atr": round(atr_val, 2),
        "reasons": reasons,
    }
