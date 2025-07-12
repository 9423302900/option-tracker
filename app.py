# app.py – now with NSE option chain scraping for indices
import streamlit as st
import pandas as pd
import requests
import datetime
import random
import time

st.set_page_config(layout="wide")
st.title("📈 Option Buy Signal Tracker – NSE Live Data")

# Define index symbols supported by NSE option chain
nse_indices = ["NIFTY", "BANKNIFTY", "FINNIFTY"]

# NSE headers to mimic browser
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.nseindia.com"
}

# Function to get option chain data from NSE
@st.cache_data(ttl=300)
def fetch_nse_option_chain(symbol):
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    session = requests.Session()
    try:
        # First request to set cookies
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
        response = session.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {e}")
        return None

# Process and filter CE/PE near ₹100
@st.cache_data(ttl=300)
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

# Fetch base prices at 9:30 (simulated)
option_frames = []
for sym in nse_indices:
    raw = fetch_nse_option_chain(sym)
    opt_df = extract_options_near_100(raw, sym)
    option_frames.append(opt_df)

base_df = pd.concat(option_frames, ignore_index=True)

# Simulate current prices and check +10% alert
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

# Filter BUY alerts
buy_df = signal_df[signal_df["Signal"] == "✅ BUY"]

st.subheader("🔔 Buy Alerts")
st.dataframe(buy_df if not buy_df.empty else pd.DataFrame([{"Status": "No signals yet"}]))
