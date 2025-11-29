# Walkthrough: Technical Analysis Backtesting Web App

This application provides an end-to-end solution for fetching market data, managing instrument tokens, and backtesting technical strategies.

## Features

1.  **Authentication**: Secure login screen (Default: `admin` / `password123`).
2.  **Instrument Management**: Fetch and save the latest instrument tokens from Zerodha Kite Connect.
3.  **Data Download**: 
    -   Select an exchange (NSE, BSE, etc.).
    -   Search and select a specific instrument.
    -   Download historical data for a custom date range and interval.
    -   Data is saved to the `data/` directory.
4.  **Backtesting**:
    -   Load downloaded CSV files.
    -   Apply strategies (Supertrend, Golden Crossover, RSI, MACD, Bollinger Bands).
    -   View comprehensive performance metrics.

## Setup & Usage

### 1. Prerequisites
Ensure you have the required Python packages installed:
```bash
pip install -r requirements.txt
```

### 2. Configuration
Update your Kite Connect credentials in `kite_auth.py`:
- `API_KEY`
- `API_SECRET`
- `USER_ID`
- `PASSWORD`
- `TOTP_KEY`

### 3. Running the App
Start the Streamlit application:
```bash
streamlit run app.py
```

### 4. Workflow
1.  **Login**: Enter username and password.
2.  **Fetch Instruments**: Go to "Fetch Instruments" page and click the button to initialize the token list.
3.  **Download Data**: Go to "Download Data", select your instrument, set dates, and download.
4.  **Backtest**: Go to "Backtest", select your file, configure the strategy, and run.

## File Structure
- `app.py`: Main Streamlit application.
- `kite_auth.py`: Authentication handler.
- `data_downloader.py`: Generic historical data fetcher.
- `instrument_tokens.py`: Instrument list fetcher.
- `backtest_engine.py`: Core backtesting logic.
- `login.py`: User authentication logic.
- `data/`: Directory for storing JSON tokens and CSV data.
