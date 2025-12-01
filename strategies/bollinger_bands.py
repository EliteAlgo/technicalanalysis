import pandas as pd
import numpy as np

def calculate_bollinger_bands_strategy(df, period=20, std_dev=2):
    """Calculates Bollinger Bands Strategy."""
    df = df.copy()
    df['sma'] = df['close'].rolling(window=period).mean()
    df['std'] = df['close'].rolling(window=period).std()
    df['upper_band'] = df['sma'] + (df['std'] * std_dev)
    df['lower_band'] = df['sma'] - (df['std'] * std_dev)
    
    # Mean Reversion Strategy
    df['signal'] = 0
    df.loc[df['close'] < df['lower_band'], 'signal'] = 1
    df.loc[df['close'] > df['upper_band'], 'signal'] = -1
    
    # Forward fill
    df['signal'] = df['signal'].replace(0, np.nan).ffill().fillna(0)
    return df
