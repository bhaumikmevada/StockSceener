"""
Main entry point. This is what GitHub Actions runs on a schedule.

Flow:
1. Check it's a market day/hour (IST 9:15 - 15:30, Mon-Fri). Skip otherwise.
2. Fetch daily data for SWING scoring, intraday data for INTRADAY scoring.
3. Score every stock in the universe, rank, keep the best.
4. Write results to docs/data.json (powers the GitHub Pages dashboard).
5. Send a Telegram alert with the top picks + dashboard link.
"""
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from stock_list import NIFTY_50, INTRADAY_UNIVERSE
from data_fetcher import fetch_universe
from scoring import score_swing, score_intraday
from telegram_alert import send_alert
from state_manager import (
    load_state, save_state, filter_new_alerts,
    MAX_INTRADAY_ALERTS_PER_DAY, MAX_SWING_ALERTS_PER_DAY,
)

IST = ZoneInfo("Asia/Kolkata")

MAX_SWING_PICKS = 5           # how many shown on dashboard at once
MIN_SWING_PICKS_TO_SHOW = 2
MAX_INTRADAY_PICKS = 6        # how many shown on dashboard at once


def is_market_open(now=None):
    now = now or datetime.now(IST)
    if now.weekday() >= 5:  # Sat/Sun
        return False
    open_t = now.replace(hour=9, minute=15, second=0, microsecond=0)
    close_t = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return open_t <= now <= close_t


def run_swing_scan():
    data = fetch_universe(NIFTY_50, mode="daily")
    setups = []
    for sym, df in data.items():
        result = score_swing(df, sym)
        if result:
            setups.append(result)
    setups.sort(key=lambda x: x["score"], reverse=True)
    # Only keep 2-5 as requested - if fewer than 2 good ones exist, show what we have
    return setups[:MAX_SWING_PICKS]


def run_intraday_scan():
    intraday_data = fetch_universe(INTRADAY_UNIVERSE, mode="intraday")
    daily_data = fetch_universe(INTRADAY_UNIVERSE, mode="daily")  # for multi-timeframe filter
    setups = []
    for sym, df in intraday_data.items():
        daily_df = daily_data.get(sym)
        result = score_intraday(df, sym, daily_df=daily_df)
        if result:
            setups.append(result)
    setups.sort(key=lambda x: x["score"], reverse=True)
    return setups[:MAX_INTRADAY_PICKS]


def write_dashboard_data(swing, intraday, run_time):
    os.makedirs("docs", exist_ok=True)
    payload = {
        "generated_at": run_time.isoformat(),
        "generated_at_display": run_time.strftime("%d %b %Y, %I:%M %p IST"),
        "swing": swing,
        "intraday": intraday,
    }
    with open("docs/data.json", "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"[OK] Wrote docs/data.json with {len(swing)} swing + {len(intraday)} intraday picks.")


def main():
    now = datetime.now(IST)
    force_run = os.environ.get("FORCE_RUN", "false").lower() == "true"

    if not is_market_open(now) and not force_run:
        print(f"[SKIP] Market closed at {now.strftime('%Y-%m-%d %H:%M %Z')}. Exiting.")
        return

    print(f"[RUN] Starting scan at {now.strftime('%Y-%m-%d %H:%M %Z')}")

    swing_setups = run_swing_scan()
    intraday_setups = run_intraday_scan()

    # Dashboard always shows the current best picks, every run.
    write_dashboard_data(swing_setups, intraday_setups, now)

    # But Telegram only fires for symbols not already alerted today, and
    # respects a hard daily cap - no spam every 15 minutes.
    state = load_state()
    new_swing = filter_new_alerts(swing_setups, state["swing_alerted"], MAX_SWING_ALERTS_PER_DAY)
    new_intraday = filter_new_alerts(intraday_setups, state["intraday_alerted"], MAX_INTRADAY_ALERTS_PER_DAY)

    if new_swing or new_intraday:
        send_alert(new_swing, new_intraday, now.strftime("%d %b %Y, %I:%M %p IST"))
        state["swing_alerted"].extend([s["symbol"] for s in new_swing])
        state["intraday_alerted"].extend([s["symbol"] for s in new_intraday])
        save_state(state)
        print(f"[ALERT] Sent {len(new_swing)} swing + {len(new_intraday)} intraday alerts.")
    else:
        print("[SKIP-ALERT] No new qualifying setups since last alert, or daily cap reached.")

    print("[DONE]")


if __name__ == "__main__":
    main()
