import pandas as pd

def calculate_golden_crossover(df, short_window=50, long_window=200):
    """Calculates Golden Crossover (SMA Crossover)."""
    df = df.copy()
    df['short_mavg'] = df['close'].rolling(window=short_window).mean()
    df['long_mavg'] = df['close'].rolling(window=long_window).mean()
    
    df['signal'] = 0
    df.loc[df['short_mavg'] > df['long_mavg'], 'signal'] = 1
    df.loc[df['short_mavg'] < df['long_mavg'], 'signal'] = -1
    return df
