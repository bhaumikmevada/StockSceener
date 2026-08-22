"""
Sends formatted alerts to Telegram. Reads BOT_TOKEN and CHAT_ID from
environment variables (set as GitHub Secrets - never hardcoded).
"""
import os
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "")  # e.g. https://username.github.io/repo/


def _format_setup(setup: dict) -> str:
    label = "SWING EQUITY TRADE" if setup["type"] == "SWING" else "INTRADAY TRADE"
    symbol = setup["symbol"].replace(".NS", "")
    lines = [
        f"*{label}*",
        f"BUY {symbol}",
        f"Entry: ₹{setup['entry']}",
        f"Target: ₹{setup['target']}",
        f"SL: ₹{setup['stop_loss']}",
        f"Score: {setup['score']}/100 | Volume: {setup['volume_ratio']}x avg",
    ]
    if setup["type"] == "SWING":
        lines.append(f"Expected: {setup['holding_days']}")
    else:
        lines.append(f"Hold: {setup['holding_days']}")
    return "\n".join(lines)


def send_alert(swing_setups, intraday_setups, run_time_str):
    if not BOT_TOKEN or not CHAT_ID:
        print("[WARN] Telegram credentials not set, skipping notification.")
        return

    parts = []

    for s in swing_setups:
        parts.append(_format_setup(s))

    for s in intraday_setups:
        parts.append(_format_setup(s))

    if not parts:
        return  # nothing new to send

    if DASHBOARD_URL:
        parts.append(f"Full dashboard: {DASHBOARD_URL}")

    message = "\n\n".join(parts)

    # Telegram messages have a 4096 char limit - trim if needed
    if len(message) > 4000:
        message = message[:3950] + "\n\n...(truncated, see dashboard for full list)"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    resp = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    })
    if resp.status_code != 200:
        print(f"[ERROR] Telegram send failed: {resp.status_code} {resp.text}")
    else:
        print("[OK] Telegram alert sent.")
