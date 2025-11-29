import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

# Local imports
import backtest_engine as engine
from kite_auth import get_kite
from instrument_tokens import fetch_instruments, save_instruments
from data_downloader import fetch_historical_data
from login import authenticate

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DATA_DIR = "data"
INSTRUMENT_FILE = os.path.join(DATA_DIR, "instrument_tokens.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def list_csv_files():
    """Return a list of CSV files in the data directory (excluding instrument list)."""
    return [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]

def load_csv(file_name):
    """Load a CSV file from the data directory using the backtest engine loader."""
    file_path = os.path.join(DATA_DIR, file_name)
    return engine.load_data(file_path)

# ----------------------------------------------------------------------
# Session state – authentication
# ----------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# ----------------------------------------------------------------------
# Login page
# ----------------------------------------------------------------------
if not st.session_state["authenticated"]:
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state["authenticated"] = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# ----------------------------------------------------------------------
# Main application – after successful login
# ----------------------------------------------------------------------
st.set_page_config(page_title="Backtesting Engine", layout="wide")
st.title("📈 Technical Analysis Backtesting Engine")

# Sidebar navigation
st.sidebar.header("Navigation")
page = st.sidebar.radio("Select page", ["Home", "Fetch Instruments", "Download Data", "Backtest"])

# ----------------------------------------------------------------------
# Home page – brief description
# ----------------------------------------------------------------------
if page == "Home":
    st.write(
        "Welcome! Use the sidebar to fetch the latest instrument list, download historical data, "
        "and run backtests on the downloaded CSV files."
    )

# ----------------------------------------------------------------------
# Fetch Instruments page
# ----------------------------------------------------------------------
elif page == "Fetch Instruments":
    st.subheader("Fetch Instrument Tokens")
    if st.button("Fetch and Save Instruments"):
        try:
            instruments = fetch_instruments()
            save_instruments(instruments, INSTRUMENT_FILE)
            st.success(f"Fetched and saved {len(instruments)} instruments to `{INSTRUMENT_FILE}`")
        except Exception as e:
            st.error(f"Failed to fetch instruments: {e}")

# ----------------------------------------------------------------------
# Download Data page
# ----------------------------------------------------------------------
elif page == "Download Data":
    st.subheader("Download Historical Data")
    
    # Check if instrument file exists
    if not os.path.exists(INSTRUMENT_FILE):
        st.warning(f"Instrument file not found at `{INSTRUMENT_FILE}`. Please fetch instruments first.")
    else:
        try:
            with open(INSTRUMENT_FILE, "r", encoding="utf-8") as f:
                instruments = json.load(f)
            
            # Convert to DataFrame for easier filtering
            df_instr = pd.DataFrame(instruments)
            
            # Filter by exchange
            exchanges = df_instr['exchange'].unique().tolist()
            selected_exchange = st.selectbox("Select Exchange", exchanges)
            
            # Filter instruments based on exchange
            df_filtered = df_instr[df_instr['exchange'] == selected_exchange]
            
            # Search/Select Instrument
            # Create a display label: "Tradingsymbol (Token)"
            df_filtered['display'] = df_filtered['tradingsymbol'] + " (" + df_filtered['instrument_token'].astype(str) + ")"
            selected_display = st.selectbox("Select Instrument", df_filtered['display'].tolist())
            
            # Get selected instrument details
            selected_row = df_filtered[df_filtered['display'] == selected_display].iloc[0]
            instrument_token = int(selected_row['instrument_token'])
            tradingsymbol = selected_row['tradingsymbol']
            
            # Date Range and Interval
            col1, col2, col3 = st.columns(3)
            start_date = col1.date_input("Start Date", pd.to_datetime("2023-01-01"), key="dl_start")
            end_date = col2.date_input("End Date", pd.to_datetime("today"), key="dl_end")
            interval = col3.selectbox("Interval", ["minute", "3minute", "5minute", "15minute", "30minute", "60minute", "day"], index=1)
            
            if st.button("Download Data"):
                with st.spinner(f"Downloading data for {tradingsymbol}..."):
                    try:
                        # Construct filename
                        filename = f"{tradingsymbol}_{interval}.csv"
                        output_path = os.path.join(DATA_DIR, filename)
                        
                        # Convert dates to datetime objects
                        start_dt = datetime.combine(start_date, datetime.min.time())
                        end_dt = datetime.combine(end_date, datetime.max.time())
                        
                        # Call downloader
                        result = fetch_historical_data(instrument_token, start_dt, end_dt, interval, output_path)
                        
                        if result:
                            st.success(f"Data downloaded successfully to `{result}`")
                        else:
                            st.error("No data found for the selected range.")
                            
                    except Exception as e:
                        st.error(f"Error downloading data: {e}")
                        
        except Exception as e:
            st.error(f"Error loading instrument tokens: {e}")

# ----------------------------------------------------------------------
# Backtest page
# ----------------------------------------------------------------------
elif page == "Backtest":
    st.subheader("Run Backtest on a CSV file")
    csv_files = list_csv_files()
    if not csv_files:
        st.warning("No CSV files found in the data folder. Download data first.")
    else:
        selected_file = st.selectbox("Select CSV file", csv_files)
        # Date range selectors – will be applied after loading
        st.sidebar.subheader("Date Range")
        start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2015-01-01"))
        end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))
        # Timeframe selector
        st.sidebar.subheader("Timeframe")
        timeframe = st.sidebar.selectbox(
            "Select Timeframe",
            ["Original", "3min", "5min", "15min", "30min", "1H", "4H", "1D"],
        )
        # Strategy selector
        st.sidebar.subheader("Strategy")
        strategy = st.sidebar.selectbox(
            "Select Strategy",
            ["None", "Supertrend", "Golden Crossover", "RSI Strategy", "MACD Strategy", "Bollinger Bands"],
        )
        # Strategy parameters
        params = {}
        if strategy == "Supertrend":
            params["period"] = st.sidebar.number_input("ATR Period", min_value=1, value=10)
            params["multiplier"] = st.sidebar.number_input("Multiplier", min_value=0.1, value=3.0, step=0.1)
        elif strategy == "Golden Crossover":
            params["short_window"] = st.sidebar.number_input("Short Window", min_value=1, value=50)
            params["long_window"] = st.sidebar.number_input("Long Window", min_value=1, value=200)
        elif strategy == "RSI Strategy":
            params["period"] = st.sidebar.number_input("RSI Period", min_value=1, value=14)
            params["overbought"] = st.sidebar.number_input("Overbought", min_value=50, value=70)
            params["oversold"] = st.sidebar.number_input("Oversold", min_value=1, value=30)
        elif strategy == "MACD Strategy":
            params["fast"] = st.sidebar.number_input("Fast Period", min_value=1, value=12)
            params["slow"] = st.sidebar.number_input("Slow Period", min_value=1, value=26)
            params["signal"] = st.sidebar.number_input("Signal Period", min_value=1, value=9)
        elif strategy == "Bollinger Bands":
            params["period"] = st.sidebar.number_input("Period", min_value=1, value=20)
            params["std_dev"] = st.sidebar.number_input("Std Dev", min_value=0.1, value=2.0, step=0.1)

        if st.button("Run Backtest"):
            with st.spinner("Running backtest…"):
                df = load_csv(selected_file)
                if df is None:
                    st.error("Failed to load CSV data.")
                else:
                    # Apply date filter
                    mask = (df.index.date >= start_date) & (df.index.date <= end_date)
                    df_filtered = df.loc[mask]
                    if df_filtered.empty:
                        st.warning("No data in selected date range.")
                    else:
                        # Resample & strategy
                        df_resampled = engine.resample_data(df_filtered, timeframe)
                        if strategy != "None":
                            if strategy == "Supertrend":
                                df_resampled = engine.calculate_supertrend(
                                    df_resampled, params["period"], params["multiplier"]
                                )
                            elif strategy == "Golden Crossover":
                                df_resampled = engine.calculate_golden_crossover(
                                    df_resampled, params["short_window"], params["long_window"]
                                )
                            elif strategy == "RSI Strategy":
                                df_resampled = engine.calculate_rsi_strategy(
                                    df_resampled,
                                    params["period"],
                                    params["overbought"],
                                    params["oversold"],
                                )
                            elif strategy == "MACD Strategy":
                                df_resampled = engine.calculate_macd_strategy(
                                    df_resampled, params["fast"], params["slow"], params["signal"]
                                )
                            elif strategy == "Bollinger Bands":
                                df_resampled = engine.calculate_bollinger_bands_strategy(
                                    df_resampled, params["period"], params["std_dev"]
                                )
                        # Run backtest & metrics
                        df_bt = engine.run_backtest(df_resampled)
                        metrics = engine.calculate_metrics(df_bt)
                        if metrics:
                            st.subheader("Backtest Performance Metrics")
                            cols = st.columns(4)
                            keys = list(metrics.keys())
                            for i, key in enumerate(keys):
                                cols[i % 4].metric(key, metrics[key])
                        else:
                            st.info("No metrics available.")
