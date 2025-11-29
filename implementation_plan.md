# Goal
Create an end‑to‑end Streamlit web application that:
1. Provides a login screen.
2. Allows the user to fetch the latest instrument token list from Zerodha and store it as `instrument_tokens.json`.
3. Lets the user select a script (currently only the Nifty 3‑minute data script) and download the historical data into a dedicated `data/` folder.
4. Runs the existing back‑testing engine on the downloaded CSV and displays the calculated metrics.

## Proposed Changes
- **Folder structure**
  - `data/` – will hold `instrument_tokens.json` and any downloaded CSV files.
  - `pages/` – optional Streamlit multi‑page folder (not required for this simple flow).
- **New files**
  - `login.py` – simple hard‑coded credential check (username/password) used by the Streamlit app.
  - `implementation_plan.md` – this document (created now).
- **Modified files**
  - `app.py` – refactored to include a login screen, sidebar navigation, and integration with `instrument_tokens.py`, `nifty_3min_data.py`, and `backtest_engine.py`.
  - `nifty_3min_data.py` – minor adjustment to expose a callable `download_data()` that returns the generated CSV filename.
  - `instrument_tokens.py` – unchanged (already provides `fetch_instruments` and `save_instruments`).
  - `backtest_engine.py` – unchanged (already provides `load_data`, `run_backtest`, `calculate_metrics`).
- **Requirements**
  - Ensure `requirements.txt` contains `streamlit`, `pandas`, `numpy`, `pyotp`, `kiteconnect`, and `requests` (already present).

## Verification Plan
1. **Login** – Verify that entering the correct credentials shows the main UI; wrong credentials show an error.
2. **Fetch Instruments** – Click the "Fetch Instruments" button and confirm that `data/instrument_tokens.json` is created and a success message appears.
3. **Download Data** – After fetching instruments, click "Download Nifty Data" and confirm a CSV file appears in `data/`.
4. **Backtest** – Select the newly created CSV from a dropdown, run the backtest, and display a table of metrics. Verify that metrics are non‑empty.
5. **UI Flow** – Ensure the app runs without errors via `streamlit run app.py`.

Once you approve this plan, I will proceed with the implementation.
