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
    emoji = "🟢" if setup["type"] == "SWING" else "⚡"
    reasons = "\n".join(f"  • {r}" for r in setup["reasons"])
    return (
        f"{emoji} *{setup['symbol'].replace('.NS','')}* — {setup['type']} | Score: {setup['score']}/100\n"
        f"Entry: ₹{setup['entry']}   Target: ₹{setup['target']}   SL: ₹{setup['stop_loss']}\n"
        f"Risk: {setup['risk_pct']}%   Reward: {setup['reward_pct']}%   R:R: {setup['rr_ratio']}\n"
        f"Hold: {setup['holding_days']}   RSI: {setup['rsi']}   Vol: {setup['volume_ratio']}x\n"
        f"{reasons}"
    )


def send_alert(swing_setups, intraday_setups, run_time_str):
    if not BOT_TOKEN or not CHAT_ID:
        print("[WARN] Telegram credentials not set, skipping notification.")
        return

    parts = [f"📊 *Market Scan — {run_time_str}*\n"]

    if swing_setups:
        parts.append("*SWING PICKS (2-3 day hold)*")
        for s in swing_setups:
            parts.append(_format_setup(s))
    else:
        parts.append("_No high-quality swing setups right now._")

    if intraday_setups:
        parts.append("\n*INTRADAY PICKS*")
        for s in intraday_setups:
            parts.append(_format_setup(s))
    else:
        parts.append("_No high-quality intraday setups right now._")

    if DASHBOARD_URL:
        parts.append(f"\n📈 Full dashboard: {DASHBOARD_URL}")

    parts.append(
        "\n⚠️ Educational signals only, not investment advice. "
        "No system is 90%+ accurate — always size positions responsibly."
    )

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
