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
from strategies.supertrend import calculate_supertrend
from strategies.golden_crossover import calculate_golden_crossover
from strategies.rsi_strategy import calculate_rsi_strategy
from strategies.macd_strategy import calculate_macd_strategy
from strategies.bollinger_bands import calculate_bollinger_bands_strategy
from strategies.quantzee_supertrend import calculate_quantzee_supertrend

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
        "Gross Loss": round(gross_loss, 4),
        "Risk Reward Ratio": round(avg_win / avg_loss, 2) if avg_loss != 0 else 0
    }
    
    return metrics
