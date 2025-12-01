import pandas as pd

def calculate_macd_strategy(df, fast=12, slow=26, signal_period=9):
    """Calculates MACD Strategy."""
    df = df.copy()
    exp1 = df['close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['close'].ewm(span=slow, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['signal_line'] = df['macd'].ewm(span=signal_period, adjust=False).mean()
    
    df['signal'] = 0
    df.loc[df['macd'] > df['signal_line'], 'signal'] = 1
    df.loc[df['macd'] < df['signal_line'], 'signal'] = -1
    return df
