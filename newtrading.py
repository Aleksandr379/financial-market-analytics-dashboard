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
    "etfs": ["SPY", "QQQ", "VOO", "IWM", "DIA", "XLK", "XLE", "XLF", "XLY", "XLP",
             "XLV", "XLC", "XLI", "XLB", "XLRE", "ARKK", "ARKG", "ARKQ", "ARKW",
             "ARKF", "TLT", "HYG", "LQD", "EEM", "EFA", "VNQ", "GLD", "SLV", "USO", "UNG"],
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
    user_start_date = st.date_input("Start Date", earliest_date)
    start_date = max(user_start_date, earliest_date)  # Prevent selecting unavailable data
with col2:
    end_date = st.date_input("End Date", pd.to_datetime("today").date())

if start_date >= end_date:
    st.error("❌ Start date must be earlier than the end date.")
    st.stop()

# ------------------- Cached downloader -------------------
@st.cache_data
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

# ------------------------------------------------------
#                   MAIN ANALYSIS
# ------------------------------------------------------
if analyze:
    data = get_data(symbol, start_date, end_date)
    data = flatten_columns(data)

    # ---------------- Limit rows to avoid freezing ----------------
    max_rows = st.slider("Max rows to analyze", 1000, 10000, 2000, key="rows_slider")
    data = data.tail(max_rows)

    if data.empty:
        st.error("❌ No data found for this symbol in the selected date range.")
        st.stop()

    # ---------------- Closing Price ----------------
    st.subheader(f"📌 {symbol} Closing Price")
    st.line_chart(data["Close"])

    # ---------------- Moving Averages ----------------
    data["SMA_50"] = data["Close"].rolling(window=50, min_periods=1).mean()
    data["SMA_200"] = data["Close"].rolling(window=200, min_periods=1).mean()

    st.subheader("📊 Moving Averages (50 & 200 Days)")
    st.line_chart(data[["Close", "SMA_50", "SMA_200"]])

    # ---------------- SMA-based Buy/Sell Signal ----------------
    if data["SMA_50"].notna().iloc[-1] and data["SMA_200"].notna().iloc[-1]:
        if data["SMA_50"].iloc[-1] > data["SMA_200"].iloc[-1]:
            st.success("✅ Potential Buy Signal: SMA 50 is above SMA 200")
        elif data["SMA_50"].iloc[-1] < data["SMA_200"].iloc[-1]:
            st.warning("⚠️ Potential Sell Signal: SMA 50 is below SMA 200")
    else:
        st.info("ℹ️ Not enough data to generate SMA signals")

    # ---------------- Daily Returns ----------------
    data["Daily Return"] = data["Close"].pct_change()
    st.subheader("📈 Daily Returns")
    st.line_chart(data["Daily Return"].dropna())

    # ---------------- Return Distribution ----------------
    st.subheader("📉 Return Distribution Histogram")
    fig, ax = plt.subplots()
    sns.histplot(data["Daily Return"].dropna(), kde=True, ax=ax)
    st.pyplot(fig)
    plt.clf()
    plt.close('all')

    # ---------------- Volatility ----------------
    volatility = data["Daily Return"].std() * (252 ** 0.5)
    st.subheader("📌 Annual Volatility")
    st.write(f"**{volatility:.2%}**")

    # ---------------- RSI ----------------
    st.subheader("🔁 Relative Strength Index (RSI)")
    rsi = RSIIndicator(data["Close"], window=14)
    data["RSI"] = rsi.rsi()
    st.line_chart(data["RSI"].dropna())
    st.caption("Overbought > 70, Oversold < 30")

    if data["RSI"].notna().iloc[-1]:
        if data["RSI"].iloc[-1] > 70:
            st.warning("⚠️ RSI indicates overbought — potential caution for buying")
        elif data["RSI"].iloc[-1] < 30:
            st.success("✅ RSI indicates oversold — potential buying opportunity")
        else:
            st.info("ℹ️ RSI in neutral range — no immediate signal")
    else:
        st.info("ℹ️ Not enough data to compute RSI signal")

    # ---------------- Candlestick ----------------
    st.subheader("🕯️ Candlestick Chart")
    days = st.slider("Number of Days for Candlestick Chart", 30, 365, 100)
    mpf_data = data[-days:]

    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    if all(col in mpf_data.columns for col in required_cols):
        mpf_data = mpf_data[required_cols]
        try:
            fig_candle, _ = mpf.plot(
                mpf_data,
                type="candle",
                style="yahoo",
                volume=True,
                mav=(50, 200),
                show_nontrading=False,
                returnfig=True
            )
        except:
            fig_candle = mpf.plot(
                mpf_data,
                type="candle",
                style="yahoo",
                volume=True,
                mav=(50, 200),
                show_nontrading=False,
                returnfig=True
            )[0]
        st.pyplot(fig_candle)
    else:
        st.warning("⚠️ Some OHLCV columns are missing; candlestick chart cannot be displayed.")

    plt.clf()
    plt.close('all')

    st.success("✅ Analysis complete!")

