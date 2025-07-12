# app.py
import streamlit as st
import pandas as pd
import datetime
import random

st.set_page_config(layout="wide")
st.title("📈 Option Buy Signal Tracker (Mock Data)")

# Mock symbols for testing
symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY", "RELIANCE", "HDFCBANK", "CRUDEOILM"]

# Simulate 9:30 AM base prices
@st.cache_data(ttl=60*60)
def get_base_prices():
    base_data = []
    for sym in symbols:
        for opt_type in ["CE", "PE"]:
            ltp = round(random.uniform(90, 110), 2)
            base_data.append({
                "Symbol": sym,
                "OptionType": opt_type,
                "StrikePrice": 100,
                "BaseLTP_9_30": ltp
            })
    return pd.DataFrame(base_data)

base_df = get_base_prices()

# Simulate live price check and 10% increase detection
def simulate_current_prices(df):
    signals = []
    for _, row in df.iterrows():
        current_price = round(row["BaseLTP_9_30"] * random.uniform(1.00, 1.15), 2)
        change_pct = round(((current_price - row["BaseLTP_9_30"]) / row["BaseLTP_9_30"]) * 100, 2)
        alert = "✅ BUY" if change_pct >= 10 else ""
        signals.append({
            **row,
            "CurrentLTP": current_price,
            "%Change": change_pct,
            "Signal": alert
        })
    return pd.DataFrame(signals)

signal_df = simulate_current_prices(base_df)

st.dataframe(signal_df, use_container_width=True)

# Show only signals
buy_signals = signal_df[signal_df["Signal"] == "✅ BUY"]

st.subheader("🔔 Buy Alerts")
st.dataframe(buy_signals if not buy_signals.empty else pd.DataFrame([{"Status": "No signals yet"}]))
