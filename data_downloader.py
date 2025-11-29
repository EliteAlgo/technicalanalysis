import logging
import pandas as pd
import time
import os
from datetime import datetime, timedelta
from kite_auth import get_kite

# Configure logging
logging.basicConfig(level=logging.INFO)

def fetch_historical_data(instrument_token, start_date, end_date, interval, output_filename):
    """
    Fetch historical data for a given instrument token and save to CSV.
    
    Args:
        instrument_token (int): The instrument token.
        start_date (datetime): Start date.
        end_date (datetime): End date.
        interval (str): Candle interval (e.g., "3minute", "day").
        output_filename (str): Path to save the CSV.
    """
    try:
        # Obtain authenticated KiteConnect instance
        kite = get_kite()

        logging.info(
            f"Fetching data from {start_date} to {end_date} for token {instrument_token}"
        )

        all_data = []
        current_date = start_date

        while current_date < end_date:
            next_date = current_date + timedelta(days=60)
            if next_date > end_date:
                next_date = end_date

            logging.info(
                f"Fetching chunk: {current_date.date()} to {next_date.date()}"
            )

            try:
                data = kite.historical_data(
                    instrument_token=instrument_token,
                    from_date=current_date,
                    to_date=next_date,
                    interval=interval,
                )
                if data:
                    all_data.extend(data)
                    logging.info(f"Fetched {len(data)} records in this chunk.")
                else:
                    logging.warning("No data in this chunk.")
            except Exception as e:
                logging.error(
                    f"Error fetching chunk {current_date} to {next_date}: {e}"
                )
                # Continue with next chunk

            current_date = next_date
            time.sleep(0.5)  # gentle pause to respect rate limits

        if not all_data:
            logging.warning("No data fetched at all.")
            return None

        logging.info(f"Total records fetched: {len(all_data)}")

        # Create DataFrame and save to CSV
        df = pd.DataFrame(all_data)
        df.to_csv(output_filename, index=False)
        logging.info(f"Data saved to {output_filename}")
        return output_filename

    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        raise e

if __name__ == "__main__":
    # Default behavior: Nifty 3min data
    INSTRUMENT_TOKEN = 256265
    end = datetime.now()
    start = end - timedelta(days=365 * 2)
    fetch_historical_data(INSTRUMENT_TOKEN, start, end, "3minute", "nifty_3min_data.csv")
