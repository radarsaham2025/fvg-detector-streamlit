import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

st.title("📊 FVG Detector")

# ========= FETCH DATA =========
def fetch_data(ticker_input, last_days):
    ticker = f"{ticker_input}.JK"
    end_date = datetime.today()
    start_date = end_date - timedelta(days=last_days * 3)

    try:
        df = yf.download(ticker, start=start_date.strftime("%Y-%m-%d"),
                         end=end_date.strftime("%Y-%m-%d"), auto_adjust=False)
        if df.empty:
            st.error(f"Data tidak tersedia untuk {ticker}.")
            return None

        df = df.tail(last_days)
        df[['Open','High','Low','Close']] = df[['Open','High','Low','Close']].astype(float)
        return df

    except Exception as e:
        st.error(f"Error mengambil data: {e}")
        return None

# ========= DETECT FVG =========
def detect_fvg(df):
    fvg_list = []
    n = len(df)

    for i in range(n - 2):
        c1, c2, c3 = df.iloc[i], df.iloc[i+1], df.iloc[i+2]

        c1_high = float(c1["High"])
        c1_low = float(c1["Low"])
        c2_high = float(c2["High"])
        c2_low = float(c2["Low"])

        post_candles = df.loc[df.index > c3.name]

        # Bullish FVG
        if c2_low > c1_high:
            closed = False
            if not post_candles.empty:
                closed = (post_candles['Low'].to_numpy() <= c2_low).any()

            fvg_list.append({
                "type": "bullish",
                "low": int(round(c1_high)),
                "high": int(round(c2_low)),
                "date_start": c2.name.date(),
                "date_end": c3.name.date(),
                "status": "Closed" if closed else "Open"
            })

        # Bearish FVG
        if c2_high < c1_low:
            closed = False
            if not post_candles.empty:
                closed = (post_candles['High'].to_numpy() >= c2_high).any()

            fvg_list.append({
                "type": "bearish",
                "low": int(round(c2_high)),
                "high": int(round(c1_low)),
                "date_start": c2.name.date(),
                "date_end": c3.name.date(),
                "status": "Closed" if closed else "Open"
            })

    return pd.DataFrame(fvg_list)

# ========= STREAMLIT UI =========
ticker_input = st.text_input("Kode saham (4 huruf, contoh BBCA, BULL)").upper()
last_days = st.number_input("Last berapa days", min_value=5, max_value=200, value=30)

if st.button("🔍 Proses FVG"):
    if len(ticker_input) != 4 or not ticker_input.isalpha():
        st.error("Kode saham harus 4 huruf!")
    else:
        df = fetch_data(ticker_input, last_days)
        if df is not None:
            fvg_df = detect_fvg(df)

            if fvg_df.empty:
                st.warning("Tidak ditemukan FVG.")
            else:
                st.success(f"Ditemukan {len(fvg_df)} FVG!")
                st.dataframe(fvg_df)

                # unduh CSV
                csv = fvg_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"FVG_{ticker_input}_{last_days}days.csv",
                    mime="text/csv"
                )
