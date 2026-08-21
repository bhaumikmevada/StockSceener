"""
Prevents alert spam. Tracks which symbols have already been alerted TODAY
(IST date), so the same stock doesn't get re-sent every 15 minutes just
because it still scores well on the next scan.

State is stored in docs/alert_state.json and committed back to the repo by
the GitHub Actions workflow, so it persists between runs.
"""
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
STATE_PATH = "docs/alert_state.json"

# Hard caps - tune these in one place
MAX_INTRADAY_ALERTS_PER_DAY = 4
MAX_SWING_ALERTS_PER_DAY = 5  # matches "2-5 swing picks" requirement


def _today_str(now=None):
    now = now or datetime.now(IST)
    return now.strftime("%Y-%m-%d")


def load_state():
    if not os.path.exists(STATE_PATH):
        return {"date": _today_str(), "swing_alerted": [], "intraday_alerted": []}
    with open(STATE_PATH, "r") as f:
        state = json.load(f)
    # If it's a new trading day, reset counts
    if state.get("date") != _today_str():
        state = {"date": _today_str(), "swing_alerted": [], "intraday_alerted": []}
    return state


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def filter_new_alerts(setups, already_alerted, max_per_day):
    """
    Given today's scored setups (already sorted best-first) and the list of
    symbols already alerted today, returns only the ones worth sending now:
    - skips symbols already alerted today
    - respects the remaining daily quota
    """
    remaining_quota = max_per_day - len(already_alerted)
    if remaining_quota <= 0:
        return []
    fresh = [s for s in setups if s["symbol"] not in already_alerted]
    return fresh[:remaining_quota]
