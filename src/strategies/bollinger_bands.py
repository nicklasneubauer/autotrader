"""
Bollinger Bands Strategy

Buy signal: Price touches or breaks below lower band (oversold)
Sell signal: Price touches or breaks above upper band (overbought)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy


class BollingerBandsStrategy(BaseStrategy):
    """
    Bollinger Bands Strategy for mean reversion

    Parameters:
        period: Moving average period (default: 20)
        num_std: Number of standard deviations (default: 2)
        ma_type: Type of moving average - 'sma' or 'ema' (default: 'sma')
    """

    def __init__(
        self,
        period: int = 20,
        num_std: float = 2.0,
        ma_type: str = 'sma'
    ):
        parameters = {
            'period': period,
            'num_std': num_std,
            'ma_type': ma_type
        }
        super().__init__('BollingerBands', parameters)
        self.period = period
        self.num_std = num_std
        self.ma_type = ma_type.lower()

    def calculate_bollinger_bands(self, data: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands

        Args:
            data: Price series

        Returns:
            (middle_band, upper_band, lower_band)
        """
        # Calculate middle band (moving average)
        if self.ma_type == 'ema':
            middle_band = data.ewm(span=self.period, adjust=False).mean()
        else:
            middle_band = data.rolling(window=self.period).mean()

        # Calculate standard deviation
        std = data.rolling(window=self.period).std()

        # Calculate upper and lower bands
        upper_band = middle_band + (std * self.num_std)
        lower_band = middle_band - (std * self.num_std)

        return middle_band, upper_band, lower_band

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on Bollinger Bands

        Args:
            data: DataFrame with at least 'close' column

        Returns:
            Series with signals: 1 (buy), -1 (sell), 0 (hold)
        """
        if data.empty or 'close' not in data.columns:
            self.logger.warning("Invalid data provided to strategy")
            return pd.Series(dtype=int)

        df = data.copy()

        # Calculate Bollinger Bands
        middle, upper, lower = self.calculate_bollinger_bands(df['close'])
        df['bb_middle'] = middle
        df['bb_upper'] = upper
        df['bb_lower'] = lower

        # Calculate %B (position within bands)
        df['percent_b'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # Initialize signals
        signals = pd.Series(0, index=df.index)

        # Buy signal: Price crosses below lower band (oversold)
        below_lower = df['close'] < df['bb_lower']
        below_lower_prev = below_lower.shift(1)
        buy_signal = (~below_lower_prev) & below_lower
        signals[buy_signal] = 1

        # Alternative buy: Price was below and crosses back above lower band
        crosses_above_lower = (df['close'].shift(1) < df['bb_lower'].shift(1)) & (df['close'] > df['bb_lower'])
        signals[crosses_above_lower] = 1

        # Sell signal: Price crosses above upper band (overbought)
        above_upper = df['close'] > df['bb_upper']
        above_upper_prev = above_upper.shift(1)
        sell_signal = (~above_upper_prev) & above_upper
        signals[sell_signal] = -1

        # Alternative sell: Price was above and crosses back below upper band
        crosses_below_upper = (df['close'].shift(1) > df['bb_upper'].shift(1)) & (df['close'] < df['bb_upper'])
        signals[crosses_below_upper] = -1

        return signals

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Extended analysis with Bollinger Bands values"""
        base_analysis = super().analyze(data)

        if data.empty or 'close' not in data.columns:
            return base_analysis

        df = data.copy()
        middle, upper, lower = self.calculate_bollinger_bands(df['close'])

        current_price = df['close'].iloc[-1]
        current_middle = middle.iloc[-1]
        current_upper = upper.iloc[-1]
        current_lower = lower.iloc[-1]

        # Calculate %B and bandwidth
        if not pd.isna(current_upper) and not pd.isna(current_lower):
            percent_b = (current_price - current_lower) / (current_upper - current_lower)
            bandwidth = (current_upper - current_lower) / current_middle * 100

            # Determine condition
            if percent_b < 0:
                condition = 'BELOW_LOWER_BAND'
            elif percent_b < 0.2:
                condition = 'NEAR_LOWER_BAND'
            elif percent_b > 1.0:
                condition = 'ABOVE_UPPER_BAND'
            elif percent_b > 0.8:
                condition = 'NEAR_UPPER_BAND'
            elif 0.4 <= percent_b <= 0.6:
                condition = 'NEUTRAL'
            elif percent_b < 0.5:
                condition = 'BELOW_MIDDLE'
            else:
                condition = 'ABOVE_MIDDLE'
        else:
            percent_b = None
            bandwidth = None
            condition = 'INSUFFICIENT_DATA'

        base_analysis.update({
            'current_price': float(current_price),
            'bb_upper': float(current_upper) if not pd.isna(current_upper) else None,
            'bb_middle': float(current_middle) if not pd.isna(current_middle) else None,
            'bb_lower': float(current_lower) if not pd.isna(current_lower) else None,
            'percent_b': float(percent_b) if percent_b is not None else None,
            'bandwidth': float(bandwidth) if bandwidth is not None else None,
            'condition': condition
        })

        return base_analysis
