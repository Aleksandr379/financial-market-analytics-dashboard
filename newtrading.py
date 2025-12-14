import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import mplfinance as mpf
from ta.momentum import RSIIndicator

# Set Seaborn style
sns.set(style="whitegrid")

# Streamlit page config
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
    "etfs": [
        "SPY", "QQQ", "VOO", "IWM", "DIA", "XLK", "XLE", "XLF", "XLY", "XLP",
        "XLV", "XLC", "XLI", "XLB", "XLRE", "ARKK", "ARKG", "ARKQ", "ARKW",
        "ARKF", "TLT", "HYG", "LQD", "EEM", "EFA", "VNQ", "GLD", "SLV", "USO", "UNG"
    ],
    "crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD",
               "BNB-USD", "AVAX-USD", "DOT-USD", "MATIC-USD"],
    "forex": ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X",
              "NZDUSD=X", "USDCAD=X", "USDCHF=X", "EURGBP=X", "EURJPY=X"],
    "commodities": ["GC=F", "SI=F", "CL=F", "NG=F", "HG=F", "ZC=F", "ZW=F", "ZS=F",
                    "KC=F", "SB=F", "LE=F", "HE=F"],
    "indices": ["^GSPC", "^DJI", "^IXIC", "^RUT", "^FTSE", "^N225", "^HSI"]
}
# ------------------- UI -------------------
col1, col2 = st.columns(2)
with col1:
    category = st.selectbox("Select Asset Category:", list(tickers.keys()))
with col2:
    symbol = st.selectbox(f"Select {category.capitalize()} Symbol:", tickers[category])

# ------------------- Fetch max history safely -------------------
info = yf.Ticker(symbol).history(period="max")
if info.empty:
    st.error("❌ No data retrieved — YFinance may be blocked or the symbol is invalid.")
    st.stop()

earliest_date = pd.to_datetime(info.index.min()).date()

# ------------------- Date selection -------------------
col1, col2 = st.columns(2)
with col1:
    user_start_date = st.date_input(
        "Start Date",
        value=earliest_date,
        min_value=pd.to_datetime("1900-01-01").date(),
        max_value=pd.to_datetime("today").date()
    )
with col2:
    end_date = st.date_input(
        "End Date",
        value=pd.to_datetime("today").date(),
        min_value=pd.to_datetime("1900-01-01").date(),
        max_value=pd.to_datetime("today").date()
    )
# Prevent selecting dates before actual trading history
if user_start_date >= end_date:
    st.error("❌ Start date must be earlier than the end date.")
    st.stop()

# Maximum allowed range in days (10 years)
max_range_days = 365 * 10
allowed_start_date = end_date - timedelta(days = max_range_days)

# Final start date considering earliest available date and 10-year limit
start_date = max(user_start_date, earliest_date, allowed_start_date)

# Adjust start_date if the range exceeds 10 years
if start_date > user_start_date:
    st.warning(
        f"⚠️ Date range limited to 10 years for performance. Start date adjusted to {start_date}."
    )

# Inform the user of the selected date range (adjusted or not)
st.info(f"Selected date range: {start_date} to {end_date}")

# ------------------- Cached downloader -------------------
@st.cache_data(ttl=3600)
def get_data(symbol, start, end):
    data = yf.download(symbol, start=start, end=end, progress=False)
    return data.dropna()

# ------------------- Flatten MultiIndex columns -------------------
def flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if c[0] else c[1] for c in df.columns]
    df.columns = [str(col).strip() for col in df.columns]
    return df

# ------------------- Analyze Button -------------------
analyze = st.button("🔍 Analyze")

if analyze:
    data = get_data(symbol, start_date, end_date)
    data = flatten_columns(data)

    # Keep full data for indicators
    full_data = data.copy()

    # ---------------- Closing Price ----------------
    st.subheader(f"📌 {symbol} Closing Price")
    st.line_chart(full_data["Close"])

    # ---------------- Moving Averages ----------------
    full_data["SMA_50"] = full_data["Close"].rolling(window=50, min_periods=1).mean()
    full_data["SMA_200"] = full_data["Close"].rolling(window=200, min_periods=1).mean()

    st.subheader("📊 Moving Averages (50 & 200 Days)")
    st.line_chart(full_data[["Close", "SMA_50", "SMA_200"]])

    # ---------------- SMA-based Buy/Sell Signal ----------------
    last50 = full_data["SMA_50"].iloc[-1]
    last200 = full_data["SMA_200"].iloc[-1]

    if pd.notna(last50) and pd.notna(last200):
        if last50 > last200:
            st.success("✅ Potential Buy Signal: SMA 50 is above SMA 200")
        elif last50 < last200:
            st.warning("⚠️ Potential Sell Signal: SMA 50 is below SMA 200")
    else:
        st.info("ℹ️ Not enough data to generate SMA signals")

    # ---------------- Volatility ----------------
    full_data["Daily Return"] = full_data["Close"].pct_change()
    volatility = full_data["Daily Return"].std() * (252 ** 0.5)

    st.subheader("📌 Annual Volatility")
    st.write(f"**{volatility:.2%}**")

    # ---------------- RSI ----------------
    st.subheader("🔁 Relative Strength Index (RSI)")
    rsi = RSIIndicator(full_data["Close"], window=14)
    full_data["RSI"] = rsi.rsi()
    st.line_chart(full_data["RSI"].dropna())

    # Safely access last RSI value
    if not full_data["RSI"].dropna().empty:
        last_rsi = full_data["RSI"].iloc[-1]
        if last_rsi > 70:
            st.warning("⚠️ RSI indicates overbought — potential caution for buying")
        elif last_rsi < 30:
            st.success("✅ RSI indicates oversold — potential buying opportunity")
        else:
            st.info("ℹ️ RSI in neutral range — no immediate signal")

    st.success("✅ Analysis complete!")
