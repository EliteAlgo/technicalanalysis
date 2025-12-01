import pandas as pd
import numpy as np

def calculate_supertrend(df, period=10, multiplier=3):
    """Calculates Supertrend indicator."""
    df = df.copy()
    
    # ATR Calculation
    df['tr0'] = abs(df['high'] - df['low'])
    df['tr1'] = abs(df['high'] - df['close'].shift(1))
    df['tr2'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
    df['atr'] = df['tr'].rolling(period).mean()
    
    # Basic Bands
    hl2 = (df['high'] + df['low']) / 2
    df['basic_upper'] = hl2 + (multiplier * df['atr'])
    df['basic_lower'] = hl2 - (multiplier * df['atr'])
    
    # Final Bands
    df['final_upper'] = df['basic_upper']
    df['final_lower'] = df['basic_lower']
    df['supertrend'] = 0.0
    
    # Iterative calculation
    for i in range(1, len(df)):
        # Final Upper Band
        if df['basic_upper'].iloc[i] < df['final_upper'].iloc[i-1] or \
           df['close'].iloc[i-1] > df['final_upper'].iloc[i-1]:
            df.loc[df.index[i], 'final_upper'] = df['basic_upper'].iloc[i]
        else:
            df.loc[df.index[i], 'final_upper'] = df['final_upper'].iloc[i-1]
            
        # Final Lower Band
        if df['basic_lower'].iloc[i] > df['final_lower'].iloc[i-1] or \
           df['close'].iloc[i-1] < df['final_lower'].iloc[i-1]:
            df.loc[df.index[i], 'final_lower'] = df['basic_lower'].iloc[i]
        else:
            df.loc[df.index[i], 'final_lower'] = df['final_lower'].iloc[i-1]
            
        # Supertrend
        if df['supertrend'].iloc[i-1] == df['final_upper'].iloc[i-1]:
            if df['close'].iloc[i] <= df['final_upper'].iloc[i]:
                df.loc[df.index[i], 'supertrend'] = df['final_upper'].iloc[i]
            else:
                df.loc[df.index[i], 'supertrend'] = df['final_lower'].iloc[i]
        elif df['supertrend'].iloc[i-1] == df['final_lower'].iloc[i-1]:
            if df['close'].iloc[i] >= df['final_lower'].iloc[i]:
                df.loc[df.index[i], 'supertrend'] = df['final_lower'].iloc[i]
            else:
                df.loc[df.index[i], 'supertrend'] = df['final_upper'].iloc[i]
        else:
            if df['close'].iloc[i] <= df['final_upper'].iloc[i]:
                df.loc[df.index[i], 'supertrend'] = df['final_upper'].iloc[i]
            else:
                df.loc[df.index[i], 'supertrend'] = df['final_lower'].iloc[i]
                
    # Signal
    df['signal'] = np.where(df['close'] > df['supertrend'], 1, -1)
    return df
