"""
MACD (Moving Average Convergence Divergence) Strategy

Buy signal: MACD crosses above signal line (bullish crossover)
Sell signal: MACD crosses below signal line (bearish crossover)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy


class MACDStrategy(BaseStrategy):
    """
    MACD Strategy for trend following

    Parameters:
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line period (default: 9)
        threshold: Minimum MACD value for signal (default: 0)
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        threshold: float = 0
    ):
        parameters = {
            'fast_period': fast_period,
            'slow_period': slow_period,
            'signal_period': signal_period,
            'threshold': threshold
        }
        super().__init__('MACD', parameters)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.threshold = threshold

    def calculate_macd(self, data: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD, Signal line, and Histogram

        Args:
            data: Price series

        Returns:
            (macd, signal, histogram)
        """
        # Calculate EMAs
        ema_fast = data.ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = data.ewm(span=self.slow_period, adjust=False).mean()

        # MACD line
        macd = ema_fast - ema_slow

        # Signal line
        signal = macd.ewm(span=self.signal_period, adjust=False).mean()

        # Histogram
        histogram = macd - signal

        return macd, signal, histogram

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on MACD

        Args:
            data: DataFrame with at least 'close' column

        Returns:
            Series with signals: 1 (buy), -1 (sell), 0 (hold)
        """
        if data.empty or 'close' not in data.columns:
            self.logger.warning("Invalid data provided to strategy")
            return pd.Series(dtype=int)

        df = data.copy()

        # Calculate MACD
        macd, signal, histogram = self.calculate_macd(df['close'])
        df['macd'] = macd
        df['signal'] = signal
        df['histogram'] = histogram

        # Initialize signals
        signals = pd.Series(0, index=df.index)

        # Buy signal: MACD crosses above signal line
        macd_above = df['macd'] > df['signal']
        macd_above_prev = macd_above.shift(1)
        buy_crossover = (~macd_above_prev) & macd_above

        # Additional filter: MACD should be above threshold
        buy_signal = buy_crossover & (df['macd'] > self.threshold)
        signals[buy_signal] = 1

        # Sell signal: MACD crosses below signal line
        macd_below = df['macd'] < df['signal']
        macd_below_prev = macd_below.shift(1)
        sell_crossover = (~macd_below_prev) & macd_below

        # Additional filter: MACD should be below -threshold
        sell_signal = sell_crossover & (df['macd'] < -self.threshold)
        signals[sell_signal] = -1

        return signals

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Extended analysis with MACD values"""
        base_analysis = super().analyze(data)

        if data.empty or 'close' not in data.columns:
            return base_analysis

        df = data.copy()
        macd, signal, histogram = self.calculate_macd(df['close'])

        current_price = df['close'].iloc[-1]
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        current_histogram = histogram.iloc[-1]

        # Determine trend
        if not pd.isna(current_macd) and not pd.isna(current_signal):
            if current_macd > current_signal and current_macd > 0:
                trend = 'STRONG_BULLISH'
            elif current_macd > current_signal:
                trend = 'BULLISH'
            elif current_macd < current_signal and current_macd < 0:
                trend = 'STRONG_BEARISH'
            elif current_macd < current_signal:
                trend = 'BEARISH'
            else:
                trend = 'NEUTRAL'
        else:
            trend = 'INSUFFICIENT_DATA'

        base_analysis.update({
            'current_price': float(current_price),
            'macd': float(current_macd) if not pd.isna(current_macd) else None,
            'signal_line': float(current_signal) if not pd.isna(current_signal) else None,
            'histogram': float(current_histogram) if not pd.isna(current_histogram) else None,
            'trend': trend
        })

        return base_analysis
