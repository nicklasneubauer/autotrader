"""
Moving Average Crossover Strategy

Buy signal: Short MA crosses above Long MA (Golden Cross)
Sell signal: Short MA crosses below Long MA (Death Cross)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from .base_strategy import BaseStrategy


class MovingAverageCrossover(BaseStrategy):
    """
    Moving Average Crossover Strategy

    Parameters:
        short_window: Period for short moving average (default: 20)
        long_window: Period for long moving average (default: 50)
        ma_type: Type of moving average - 'sma' or 'ema' (default: 'sma')
    """

    def __init__(
        self,
        short_window: int = 20,
        long_window: int = 50,
        ma_type: str = 'sma'
    ):
        parameters = {
            'short_window': short_window,
            'long_window': long_window,
            'ma_type': ma_type
        }
        super().__init__('MovingAverageCrossover', parameters)
        self.short_window = short_window
        self.long_window = long_window
        self.ma_type = ma_type.lower()

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on MA crossover

        Args:
            data: DataFrame with at least 'close' column

        Returns:
            Series with signals: 1 (buy), -1 (sell), 0 (hold)
        """
        if data.empty or 'close' not in data.columns:
            self.logger.warning("Invalid data provided to strategy")
            return pd.Series(dtype=int)

        df = data.copy()

        # Calculate moving averages
        if self.ma_type == 'ema':
            df['short_ma'] = df['close'].ewm(span=self.short_window, adjust=False).mean()
            df['long_ma'] = df['close'].ewm(span=self.long_window, adjust=False).mean()
        else:  # sma
            df['short_ma'] = df['close'].rolling(window=self.short_window).mean()
            df['long_ma'] = df['close'].rolling(window=self.long_window).mean()

        # Initialize signal column
        df['signal'] = 0

        # Generate signals
        # Buy when short MA crosses above long MA
        df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1

        # Sell when short MA crosses below long MA
        df.loc[df['short_ma'] < df['long_ma'], 'signal'] = -1

        # Detect actual crossovers (change in signal)
        df['position'] = df['signal'].diff()

        # Only signal on crossover points
        signals = pd.Series(0, index=df.index)
        signals[df['position'] == 2] = 1  # Golden cross (buy)
        signals[df['position'] == -2] = -1  # Death cross (sell)

        return signals

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Extended analysis with MA values"""
        base_analysis = super().analyze(data)

        if data.empty or 'close' not in data.columns:
            return base_analysis

        df = data.copy()

        # Calculate MAs
        if self.ma_type == 'ema':
            short_ma = df['close'].ewm(span=self.short_window, adjust=False).mean().iloc[-1]
            long_ma = df['close'].ewm(span=self.long_window, adjust=False).mean().iloc[-1]
        else:
            short_ma = df['close'].rolling(window=self.short_window).mean().iloc[-1]
            long_ma = df['close'].rolling(window=self.long_window).mean().iloc[-1]

        current_price = df['close'].iloc[-1]

        base_analysis.update({
            'current_price': float(current_price),
            'short_ma': float(short_ma) if not pd.isna(short_ma) else None,
            'long_ma': float(long_ma) if not pd.isna(long_ma) else None,
            'ma_spread': float(short_ma - long_ma) if not pd.isna(short_ma) and not pd.isna(long_ma) else None,
            'ma_spread_pct': float((short_ma - long_ma) / long_ma * 100) if not pd.isna(short_ma) and not pd.isna(long_ma) else None
        })

        return base_analysis
