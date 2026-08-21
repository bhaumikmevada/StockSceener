# NSE Swing + Intraday Screener → Telegram + Dashboard

Automated stock screener for NSE (Nifty 50). Runs on a schedule during Indian
market hours (9:15 AM – 3:30 PM IST), scores stocks for SWING (2-3 day hold,
max 5 picks) and INTRADAY setups, sends you a Telegram alert, and updates a
live mobile dashboard you can open from the alert.

**Honesty note:** No screener is "90% accurate." This system ranks setups by
how many favorable technical conditions align right now (trend, momentum,
volume, breakout proximity). Treat the score as setup quality, not a
guarantee. Historical backtesting (not included here) is the only way to
estimate a real win rate for this logic on Nifty 50 — do that before risking
real capital, and always respect the stop-loss.

---

## What you get

- `main.py` — orchestrator, run by GitHub Actions on schedule
- `data_fetcher.py` — pulls OHLCV data from Yahoo Finance
- `indicators.py` — RSI, EMA, ATR, MACD, VWAP, volume ratio
- `scoring.py` — swing & intraday scoring + entry/target/SL calculation
- `telegram_alert.py` — sends formatted Telegram messages
- `docs/index.html` — the mobile dashboard (hosted free via GitHub Pages)
- `.github/workflows/scanner.yml` — the automation (free, runs on GitHub's servers)

You do **not** need your laptop running. GitHub's servers run this for you.

---

## Setup steps

### 1. Create a GitHub account (if you don't have one)
Go to https://github.com and sign up — it's free.

### 2. Create a new repository
- Click **New repository**
- Name it e.g. `stock-screener`
- Set it to **Public** (required for free GitHub Pages) or Private + GitHub Pro
- Don't initialize with a README (we already have files)

### 3. Upload these files
Easiest way: on the new repo page, click **uploading an existing file**, then
drag in all the files/folders from this project (keep the folder structure:
`docs/`, `.github/workflows/`, and the `.py` files at the root).

### 4. Add your Telegram credentials as Secrets (NOT in code)
In your repo: **Settings → Secrets and variables → Actions → New repository secret**

Add two secrets:
- `TELEGRAM_BOT_TOKEN` → the token from @BotFather (the **new**, non-exposed one)
- `TELEGRAM_CHAT_ID` → see step 5 below for how to get this

### 5. Get your Telegram Chat ID
1. Message your bot on Telegram (search the username you created, tap **Start**)
2. In a browser, open:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   (replace `<YOUR_TOKEN>` with your bot token)
3. Look for `"chat":{"id": 123456789, ...}` in the response — that number is your Chat ID
4. Add it as the `TELEGRAM_CHAT_ID` secret

### 6. Enable GitHub Pages (this powers the dashboard link)
**Settings → Pages** → under "Build and deployment":
- Source: **Deploy from a branch**
- Branch: `main`, folder: `/docs`
- Save

After a minute, GitHub will show your live URL, like:
`https://yourusername.github.io/stock-screener/`

### 7. Add the dashboard URL as a repo Variable
**Settings → Secrets and variables → Actions → Variables tab → New repository variable**
- Name: `DASHBOARD_URL`
- Value: the URL from step 6

This makes the Telegram alert include a tappable dashboard link.

### 8. Test it manually
Go to the **Actions** tab → **Market Scanner** workflow → **Run workflow**
button → Run. This forces an immediate run regardless of market hours, so you
can confirm everything works. Check:
- Did you get a Telegram message?
- Does the dashboard URL show your picks?

### 9. You're done
From now on, GitHub Actions automatically runs the scan every 15 minutes
during market hours (9:15 AM – 3:30 PM IST, Mon-Fri) — no laptop needed.
Every run sends a Telegram alert, and tapping the dashboard link in that
alert opens your live, mobile-friendly dashboard with full details.

---

## Adjusting things later

- **Change scan frequency:** edit the `cron` line in `.github/workflows/scanner.yml`
- **Change stock universe:** edit `stock_list.py`
- **Change scoring strictness:** edit the `if score < 55` thresholds in `scoring.py`
- **Change swing pick count (2-5):** edit `MAX_SWING_PICKS` in `main.py`
- **Add to Nifty 200 instead of Nifty 50:** expand the list in `stock_list.py`

## Security

- Never paste your bot token in chat, code, or commit it to the repo.
- It only ever lives in GitHub's encrypted Secrets — `telegram_alert.py` reads
  it from an environment variable, never hardcoded.
- If a token is ever exposed, revoke it immediately via @BotFather → `/mybots`
  → your bot → API Token → Revoke, then generate a new one and update the secret.
