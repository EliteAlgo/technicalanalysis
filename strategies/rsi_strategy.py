import pandas as pd
import numpy as np

def calculate_rsi_strategy(df, period=14, overbought=70, oversold=30):
    """Calculates RSI Strategy."""
    df = df.copy()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Signal: Mean Reversion
    df['signal'] = 0
    df.loc[df['rsi'] < oversold, 'signal'] = 1
    df.loc[df['rsi'] > overbought, 'signal'] = -1
    
    # Forward fill signal
    df['signal'] = df['signal'].replace(0, np.nan).ffill().fillna(0)
    
    return df
