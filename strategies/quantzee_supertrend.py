import pandas as pd
import numpy as np
from .supertrend import calculate_supertrend

def resample_for_htf(df, timeframe):
    """
    Resamples OHLCV data to the specified timeframe for HTF calculation.
    """
    conversion = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }
    # Filter for columns that actually exist
    available_conversion = {k: v for k, v in conversion.items() if k in df.columns}
    resampled_df = df.resample(timeframe).agg(available_conversion)
    resampled_df.dropna(inplace=True)
    return resampled_df

def calculate_quantzee_supertrend(df, ltf_timeframe, ltf_period=10, ltf_multiplier=3, htf_period=10, htf_multiplier=3):
    """
    Calculates QuantZee Supertrend Strategy (Multi-Timeframe).
    
    Logic:
    - LTF: Provided df (e.g., 3min)
    - HTF: Determined based on LTF (3min -> 15min, 15min -> 60min)
    - Buy: HTF Supertrend is Buy AND LTF Supertrend crosses to Buy
    - Sell: HTF Supertrend is Sell AND LTF Supertrend crosses to Sell
    - Buy Exit: LTF Supertrend crosses to Sell
    - Sell Exit: LTF Supertrend crosses to Buy
    """
    df = df.copy()
    
    # Determine HTF
    if ltf_timeframe == "3min":
        htf_timeframe = "15min"
    elif ltf_timeframe == "15min":
        htf_timeframe = "60min"
    else:
        # Default fallback if not specified, maybe 5x LTF? 
        # For now, let's default to 15min if unknown, or raise error?
        # Let's assume 15min as a safe default or just return simple supertrend
        htf_timeframe = "15min" 

    # 1. Calculate LTF Supertrend
    df_ltf = calculate_supertrend(df, ltf_period, ltf_multiplier)
    
    # 2. Resample to HTF
    df_htf_raw = resample_for_htf(df, htf_timeframe)
    
    # 3. Calculate HTF Supertrend
    df_htf = calculate_supertrend(df_htf_raw, htf_period, htf_multiplier)
    
    # 4. Merge HTF signal back to LTF
    # Rename HTF signal to avoid collision
    df_htf = df_htf[['signal']].rename(columns={'signal': 'htf_signal'})
    
    # Merge: reindex HTF to match LTF index (ffill)
    # This aligns the HTF signal to the LTF bars
    df_ltf['htf_signal'] = df_htf['htf_signal'].reindex(df_ltf.index, method='ffill')
    
    # 5. Generate QuantZee Signals
    # df_ltf['signal'] currently holds the LTF Supertrend signal (1 or -1)
    # We need to create a new 'final_signal' based on the logic
    
    df_ltf['ltf_signal'] = df_ltf['signal'] # Rename for clarity
    df_ltf['signal'] = 0 # Reset final signal
    
    # Logic:
    # Buy Entry: HTF == 1 AND LTF becomes 1
    # Sell Entry: HTF == -1 AND LTF becomes -1
    # Buy Exit: LTF becomes -1
    # Sell Exit: LTF becomes 1
    
    # We need to track the state
    position = 0 # 0: None, 1: Long, -1: Short
    signals = []
    
    for i in range(len(df_ltf)):
        ltf_sig = df_ltf['ltf_signal'].iloc[i]
        htf_sig = df_ltf['htf_signal'].iloc[i]
        
        # Check for change in LTF signal from previous bar
        # But here we just have the state of the signal (1 or -1).
        # Supertrend 'signal' column is 1 (Buy zone) or -1 (Sell zone).
        # A "cross" happens when it changes from -1 to 1 or 1 to -1.
        
        # Actually, simpler logic:
        # If we are flat:
        #   Check for Entry:
        #   If HTF is 1 and LTF is 1 -> Buy (if we weren't already Long)
        #   If HTF is -1 and LTF is -1 -> Sell (if we weren't already Short)
        
        # Wait, the user said: "if HTF is buy and then we get LTF as buy, then its buy"
        # This implies we wait for the crossover on LTF *while* HTF is already Buy.
        # OR if HTF is Buy and LTF is *already* Buy? Usually it means alignment.
        # Let's assume strict alignment: We take a trade when BOTH are aligned.
        # But exits are based on LTF only.
        
        current_signal = 0
        
        if position == 0:
            if htf_sig == 1 and ltf_sig == 1:
                position = 1
                current_signal = 1
            elif htf_sig == -1 and ltf_sig == -1:
                position = -1
                current_signal = -1
        elif position == 1:
            # Long position
            if ltf_sig == -1:
                # Exit Long
                position = 0
                current_signal = 0 # Or should we flip to short immediately if HTF is -1?
                # If LTF flips to -1, we exit.
                # If HTF is also -1, we might enter Short immediately.
                if htf_sig == -1:
                    position = -1
                    current_signal = -1
        elif position == -1:
            # Short position
            if ltf_sig == 1:
                # Exit Short
                position = 0
                current_signal = 0
                # Check for Long entry
                if htf_sig == 1:
                    position = 1
                    current_signal = 1
                    
        signals.append(current_signal)
        
    df_ltf['signal'] = signals
    
    # Clean up
    return df_ltf
