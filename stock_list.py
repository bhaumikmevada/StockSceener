"""NSE stock universe. Symbols use the .NS suffix required by Yahoo Finance."""

NIFTY_50 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "BAJFINANCE.NS",
    "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS",
    "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "NESTLEIND.NS", "WIPRO.NS",
    "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "M&M.NS", "TATAMOTORS.NS",
    "TATASTEEL.NS", "JSWSTEEL.NS", "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS",
    "HCLTECH.NS", "TECHM.NS", "BAJAJFINSV.NS", "INDUSINDBK.NS", "GRASIM.NS",
    "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "EICHERMOT.NS", "HEROMOTOCO.NS",
    "BAJAJ-AUTO.NS", "BRITANNIA.NS", "APOLLOHOSP.NS", "HDFCLIFE.NS", "SBILIFE.NS",
    "UPL.NS", "SHREECEM.NS", "HINDALCO.NS", "BPCL.NS", "LTIM.NS",
]

# Smaller, more liquid subset - good default for intraday (tighter spreads)
INTRADAY_UNIVERSE = NIFTY_50  # keep same universe; liquidity is already high in Nifty50
