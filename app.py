# app.py
import streamlit as st
import pandas as pd
import datetime
import random

st.set_page_config(layout="wide")
st.title("📈 Option Buy Signal Tracker – Select CE/PE near ₹100")

# Mock spot prices for underlying symbols
spot_prices = {
    "NIFTY": 23500,
    "BANKNIFTY": 49500,
    "FINNIFTY": 21500,
    "RELIANCE": 2900,
    "HDFCBANK": 1680,
    "CRUDEOILM": 6600
}

# Simulate full option chain near spot prices
@st.cache_data(ttl=60*60)
def generate_option_chain():
    option_data = []
    for symbol, spot in spot_prices.items():
        for offset in range(-5, 6):
            strike = int(round(spot / 100.0)) * 100 + offset * 100
            for option_type in ["CE", "PE"]:
                ltp = round(random.uniform(60, 160), 2)
                option_data.append({
                    "Symbol": symbol,
                    "OptionType": option_type,
                    "StrikePrice": strike,
                    "LTP": ltp
                })
    return pd.DataFrame(option_data)

option_chain_df = generate_option_chain()

# Filter to select CE/PE closest to ₹100 for each symbol
def select_near_100_options(df):
    selected = []
    for symbol in df["Symbol"].unique():
        for opt_type in ["CE", "PE"]:
            sub_df = df[(df["Symbol"] == symbol) & (df["OptionType"] == opt_type)]
            sub_df["Diff"] = abs(sub_df["LTP"] - 100)
            best = sub_df.sort_values("Diff").iloc[0]
            selected.append({
                "Symbol": best.Symbol,
                "OptionType": best.OptionType,
                "StrikePrice": best.StrikePrice,
                "BaseLTP_9_30": best.LTP
            })
    return pd.DataFrame(selected)

base_df = select_near_100_options(option_chain_df)

# Simulate live price and signal
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

