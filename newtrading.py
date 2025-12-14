import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import mplfinance as mpf
from ta.momentum import RSIIndicator

sns.set(style="whitegrid")

st.set_page_config(page_title="Financial Analytics Dashboard", layout="wide")

st.title("📈 Financial Market Analytics Dashboard")
st.write("Analyze stocks, crypto, forex, commodities, and ETFs.")

# ------------------- Tickers -------------------
tickers = {
    "stocks": [
        "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "AMD", "NFLX",
        "JPM", "BAC", "V", "MA", "WMT", "KO", "PEP", "DIS", "HD", "PG", "JNJ", "UNH",
        "PFE", "MRK", "LLY", "ABBV", "CVX", "XOM", "BP", "TMUS", "VZ", "T", "ORCL",
        "IBM", "INTC", "CSCO", "ADBE", "CRM", "PYPL", "QCOM", "TXN", "SQ", "SHOP",
        "TWLO", "ZM", "DOCU", "ROKU", "UBER", "LYFT", "SNAP", "PTON", "PLTR", "CRWD",
        "OKTA", "ZS", "DDOG", "MDB", "NET", "EA", "ATVI", "DKNG", "RBLX", "BYND",
        "TGT", "COST", "LOW", "NKE", "SBUX", "MCD", "YUM", "LULU"
    ],
    "etfs": ["SPY", "QQQ", "VOO", "IWM", "DIA"],
    "crypto": ["BTC-USD", "ETH-USD", "SOL-USD"],
    "forex": ["EURUSD=X", "GBPUSD=X", "USDJPY=X"],
    "commodities": ["GC=F", "CL=F"],
    "indices": ["^GSPC", "^DJI", "^IXIC"]
}

# ------------------- UI -------------------
col1, col2 = st.columns(2)
with col1:
    category = st.selectbox("Select Asset Category:", list(tickers.keys()))
with col2:
    symbol = st.selectbox(f"Select {category.capitalize()} Symbol:", tickers[category])

# ------------------- Fetch max history -------------------
info = yf.Ticker(symbol).history(period="max")
if info.empty:
    st.error("❌ No data retrieved.")
    st.stop()

earliest_date = pd.to_datetime(info.index.min()).date()

col1, col2 = st.columns(2)
with col1:
    user_start_date = st.date_input("Start Date", value=earliest_date)
with col2:
    end_date = st.date_input("End Date", value=pd.to_datetime("today").date())

start_date = max(user_start_date, earliest_date)

if start_date >= end_date:
    st.error("❌ Start date must be earlier than end date.")
    st.stop()

@st.cache_data
def get_data(symbol, start, end):
    return yf.download(symbol, start=start, end=end, progress=False).dropna()

analyze = st.button("🔍 Analyze")

# ------------------- MAIN ANALYSIS -------------------
if analyze:
    data = get_data(symbol, start_date, end_date)

    max_rows = st.slider("Max rows to analyze", 1000, 10000, 2000)

    full_data = data.copy()
    chart_data = full_data.tail(max_rows)

    # ---------------- Closing Price ----------------
    st.subheader(f"📌 {symbol} Closing Price")
    st.line_chart(chart_data["Close"])

    # ---------------- Moving Averages ----------------
    full_data["SMA_50"] = full_data["Close"].rolling(50).mean()
    full_data["SMA_200"] = full_data["Close"].rolling(200).mean()

    st.subheader("📊 Moving Averages (50 & 200 Days)")
    st.line_chart(full_data[["Close", "SMA_50", "SMA_200"]].tail(max_rows))

    # ---------------- SMA Signal ----------------
    if full_data["SMA_50"].iloc[-1] > full_data["SMA_200"].iloc[-1]:
        st.success("✅ Potential Buy Signal: SMA 50 above SMA 200")
    else:
        st.warning("⚠️ Potential Sell Signal: SMA 50 below SMA 200")

    # ---------------- Volatility ----------------
    full_data["Daily Return"] = full_data["Close"].pct_change()
    volatility = full_data["Daily Return"].std() * (252 ** 0.5)

    st.subheader("📌 Annual Volatility")
    st.write(f"**{volatility:.2%}**")

    # ---------------- RSI ----------------
    st.subheader("🔁 Relative Strength Index (RSI)")
    full_data["RSI"] = RSIIndicator(full_data["Close"], window=14).rsi()
    st.line_chart(full_data["RSI"].dropna().tail(max_rows))

    last_rsi = full_data["RSI"].iloc[-1]
    if last_rsi > 70:
        st.warning("⚠️ RSI Overbought")
    elif last_rsi < 30:
        st.success("✅ RSI Oversold")
    else:
        st.info("ℹ️ RSI Neutral")

    # ---------------- Candlestick ----------------
    st.subheader("🕯️ Candlestick Chart")
    days = st.slider("Candlestick Days", 30, 365, 100)

    fig, _ = mpf.plot(
        chart_data.tail(days),
        type="candle",
        style="yahoo",
        volume=True,
        mav=(50, 200),
        returnfig=True
    )
    st.pyplot(fig)

    st.success("✅ Analysis complete!")
