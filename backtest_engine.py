import pandas as pd
import numpy as np
import os

def get_available_scripts(directory='.'):
    """Scans the directory for .csv files and returns a list of script names."""
    scripts = [f.replace('.csv', '') for f in os.listdir(directory) if f.endswith('.csv')]
    return scripts

def load_data(file_path):
    """
    Loads data from CSV using PyArrow engine for speed.
    Expects columns: date, open, high, low, close, volume (or similar).
    """
    try:
        # Read CSV with PyArrow engine for performance
        try:
            df = pd.read_csv(file_path, engine='pyarrow')
        except ImportError:
            # Fallback if pyarrow is not installed/working
            df = pd.read_csv(file_path)
        except Exception:
             # Fallback for other read errors
            df = pd.read_csv(file_path)
        
        # Normalize column names to lowercase
        df.columns = df.columns.str.lower().str.strip()
        
        # Ensure 'date' column exists
        if 'date' not in df.columns:
            # Try to find a column that looks like a date
            for col in df.columns:
                if 'date' in col or 'time' in col:
                    df.rename(columns={col: 'date'}, inplace=True)
                    break
        
        if 'date' not in df.columns:
            raise ValueError("Could not find 'date' column in CSV.")

        # Parse dates
        df['date'] = pd.to_datetime(df['date'])
        
        # Set date as index for resampling
        df.set_index('date', inplace=True)
        
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def resample_data(df, timeframe):
    """
    Resamples OHLCV data to the specified timeframe.
    timeframe: str, e.g., '5min', '15min', '1H', '1D'
    """
    if timeframe == 'Original':
        return df.copy()
        
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
    
    # Drop rows with NaN
    resampled_df.dropna(inplace=True)
    
    return resampled_df

# --- Indicators & Strategies ---

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

def calculate_golden_crossover(df, short_window=50, long_window=200):
    """Calculates Golden Crossover (SMA Crossover)."""
    df = df.copy()
    df['short_mavg'] = df['close'].rolling(window=short_window).mean()
    df['long_mavg'] = df['close'].rolling(window=long_window).mean()
    
    df['signal'] = 0
    df.loc[df['short_mavg'] > df['long_mavg'], 'signal'] = 1
    df.loc[df['short_mavg'] < df['long_mavg'], 'signal'] = -1
    return df

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

def run_backtest(df):
    """
    Backtest engine calculating PnL and Metrics.
    """
    if 'signal' not in df.columns:
        return None
        
    df['returns'] = df['close'].pct_change()
    df['strategy_returns'] = df['returns'] * df['signal'].shift(1)
    
    df['cumulative_returns'] = (1 + df['strategy_returns']).cumprod()
    
    return df

def calculate_metrics(df):
    """
    Calculates comprehensive performance metrics.
    """
    if 'strategy_returns' not in df.columns:
        return {}
        
    strat_rets = df['strategy_returns'].dropna()
    
    if strat_rets.empty:
        return {}

    # 1. Total Return
    total_return = (df['cumulative_returns'].iloc[-1] - 1) * 100
    
    # 2. CAGR
    days = (df.index[-1] - df.index[0]).days
    if days > 0:
        cagr = ((df['cumulative_returns'].iloc[-1]) ** (365.0/days) - 1) * 100
    else:
        cagr = 0
        
    # 3. Volatility
    daily_rets = df['cumulative_returns'].resample('D').last().pct_change().dropna()
    volatility = daily_rets.std() * np.sqrt(252) * 100
    
    # 4. Sharpe Ratio
    sharpe = (daily_rets.mean() / daily_rets.std()) * np.sqrt(252) if daily_rets.std() != 0 else 0
    
    # 5. Sortino Ratio
    negative_rets = daily_rets[daily_rets < 0]
    sortino = (daily_rets.mean() / negative_rets.std()) * np.sqrt(252) if negative_rets.std() != 0 else 0
    
    # 6. Max Drawdown
    cum_rets = df['cumulative_returns']
    running_max = cum_rets.cummax()
    drawdown = (cum_rets - running_max) / running_max
    max_drawdown = drawdown.min() * 100
    
    # 7. Win Rate (Days)
    win_days = len(daily_rets[daily_rets > 0])
    total_days = len(daily_rets)
    win_rate_days = (win_days / total_days * 100) if total_days > 0 else 0
    
    # 8. Profit Factor
    gross_profit = strat_rets[strat_rets > 0].sum()
    gross_loss = abs(strat_rets[strat_rets < 0].sum())
    profit_factor = gross_profit / gross_loss if gross_loss != 0 else 0
    
    # 9. Avg Win / Avg Loss
    avg_win = strat_rets[strat_rets > 0].mean()
    avg_loss = abs(strat_rets[strat_rets < 0].mean())
    
    # 10. Expectancy
    win_rate_raw = len(strat_rets[strat_rets > 0]) / len(strat_rets)
    loss_rate_raw = 1 - win_rate_raw
    expectancy = (win_rate_raw * avg_win) - (loss_rate_raw * avg_loss)
    
    # 11. Calmar Ratio
    calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0
    
    # 12. Exposure Time
    exposure = (df['signal'] != 0).mean() * 100
    
    # 13. SQN
    n_trades = len(daily_rets)
    sqn = np.sqrt(n_trades) * (daily_rets.mean() / daily_rets.std()) if daily_rets.std() != 0 else 0

    # 14. No. of Trades
    if 'signal' in df.columns:
        # Count entries: signal != prev_signal AND signal != 0
        prev_signal = df['signal'].shift(1).fillna(0)
        entries = ((df['signal'] != prev_signal) & (df['signal'] != 0)).sum()
        num_trades = int(entries)
    else:
        num_trades = 0

    metrics = {
        "Total Return (%)": round(total_return, 2),
        "CAGR (%)": round(cagr, 2),
        "Volatility (Ann.) (%)": round(volatility, 2),
        "Sharpe Ratio": round(sharpe, 2),
        "Sortino Ratio": round(sortino, 2),
        "Max Drawdown (%)": round(max_drawdown, 2),
        "Calmar Ratio": round(calmar, 2),
        "Win Rate (Days) (%)": round(win_rate_days, 2),
        "Profit Factor": round(profit_factor, 2),
        "Avg Win (%)": round(avg_win * 100, 4),
        "Avg Loss (%)": round(avg_loss * 100, 4),
        "Expectancy (%)": round(expectancy * 100, 4),
        "Exposure Time (%)": round(exposure, 2),
        "SQN": round(sqn, 2),
        "No. of Trades": num_trades,
        "Data Points": len(df),
        "Start Date": str(df.index[0].date()),
        "End Date": str(df.index[-1].date()),
        "Gross Profit": round(gross_profit, 4),
        "Gross Loss": round(gross_loss, 4)
    }
    
    return metrics
