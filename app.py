# app.py – NSE scraping for indices + F&O stocks (mock intraday LTP)
import streamlit as st
import pandas as pd
import requests
import datetime
import random
import time

st.set_page_config(layout="wide")
st.title("📈 Option Buy Signal Tracker – NSE Live Data")

# NSE-supported symbols (indices + F&O stocks)
symbols = [
    ("NIFTY", True),
    ("BANKNIFTY", True),
    ("FINNIFTY", True),
    ("RELIANCE", False),
    ("HDFCBANK", False)
]

# NSE headers to mimic browser
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.nseindia.com"
}

# Get NSE option chain data (index or stock)
def fetch_nse_option_chain(symbol, is_index):
    url = f"https://www.nseindia.com/api/option-chain-{'indices' if is_index else 'equities'}?symbol={symbol}"
    session = requests.Session()
    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
        response = session.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.warning(f"Error fetching data for {symbol}: {e}")
    return None

# Select CE/PE with LTP closest to ₹100
def extract_options_near_100(data, symbol):
    base_data = []
    if not data:
        return pd.DataFrame()

    spot_price = data.get("records", {}).get("underlyingValue", 0)
    all_options = data.get("records", {}).get("data", [])

    for opt_type in ["CE", "PE"]:
        closest = None
        min_diff = float("inf")
        for item in all_options:
            strike = item.get("strikePrice")
            option = item.get(opt_type)
            if option and "lastPrice" in option:
                ltp = option["lastPrice"]
                diff = abs(ltp - 100)
                if diff < min_diff:
                    min_diff = diff
                    closest = {
                        "Symbol": symbol,
                        "OptionType": opt_type,
                        "StrikePrice": strike,
                        "BaseLTP_9_30": ltp
                    }
        if closest:
            base_data.append(closest)

    return pd.DataFrame(base_data)

# Pull & process for all symbols
frames = []
for symbol, is_index in symbols:
    raw = fetch_nse_option_chain(symbol, is_index)
    df = extract_options_near_100(raw, symbol)
    frames.append(df)

base_df = pd.concat(frames, ignore_index=True)

# Simulate current prices and detect BUY alerts
def simulate_live_prices(df):
    signals = []
    for _, row in df.iterrows():
        current_price = round(row["BaseLTP_9_30"] * random.uniform(1.00, 1.15), 2)
        change_pct = round(((current_price - row["BaseLTP_9_30"]) / row["BaseLTP_9_30"]) * 100, 2)
        signal = "✅ BUY" if change_pct >= 10 else ""
        signals.append({
            **row,
            "CurrentLTP": current_price,
            "%Change": change_pct,
            "Signal": signal
        })
    return pd.DataFrame(signals)

signal_df = simulate_live_prices(base_df)

st.dataframe(signal_df, use_container_width=True)

# Show buy signals only
buy_df = signal_df[signal_df["Signal"] == "✅ BUY"]

st.subheader("🔔 Buy Alerts")
st.dataframe(buy_df if not buy_df.empty else pd.DataFrame([{"Status": "No signals yet"}]))
