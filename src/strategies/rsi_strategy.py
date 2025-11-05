"""
RSI (Relative Strength Index) Strategy

Buy signal: RSI crosses above oversold level (default: 30)
Sell signal: RSI crosses below overbought level (default: 70)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy


class RSIStrategy(BaseStrategy):
    """
    RSI Strategy for identifying overbought/oversold conditions

    Parameters:
        period: RSI period (default: 14)
        oversold: Oversold threshold (default: 30)
        overbought: Overbought threshold (default: 70)
    """

    def __init__(
        self,
        period: int = 14,
        oversold: float = 30,
        overbought: float = 70
    ):
        parameters = {
            'period': period,
            'oversold': oversold,
            'overbought': overbought
        }
        super().__init__('RSI', parameters)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def calculate_rsi(self, data: pd.Series, period: int) -> pd.Series:
        """
        Calculate RSI indicator

        Args:
            data: Price series
            period: RSI period

        Returns:
            RSI values
        """
        delta = data.diff()

        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on RSI

        Args:
            data: DataFrame with at least 'close' column

        Returns:
            Series with signals: 1 (buy), -1 (sell), 0 (hold)
        """
        if data.empty or 'close' not in data.columns:
            self.logger.warning("Invalid data provided to strategy")
            return pd.Series(dtype=int)

        df = data.copy()

        # Calculate RSI
        df['rsi'] = self.calculate_rsi(df['close'], self.period)

        # Initialize signals
        signals = pd.Series(0, index=df.index)

        # Buy signal: RSI crosses above oversold level
        oversold_condition = (df['rsi'] < self.oversold)
        oversold_prev = oversold_condition.shift(1)
        buy_signal = oversold_prev & (df['rsi'] >= self.oversold)
        signals[buy_signal] = 1

        # Sell signal: RSI crosses below overbought level
        overbought_condition = (df['rsi'] > self.overbought)
        overbought_prev = overbought_condition.shift(1)
        sell_signal = overbought_prev & (df['rsi'] <= self.overbought)
        signals[sell_signal] = -1

        return signals

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Extended analysis with RSI values"""
        base_analysis = super().analyze(data)

        if data.empty or 'close' not in data.columns:
            return base_analysis

        df = data.copy()
        rsi = self.calculate_rsi(df['close'], self.period)
        current_rsi = rsi.iloc[-1]
        current_price = df['close'].iloc[-1]

        # Determine market condition
        if pd.isna(current_rsi):
            condition = 'INSUFFICIENT_DATA'
        elif current_rsi < self.oversold:
            condition = 'OVERSOLD'
        elif current_rsi > self.overbought:
            condition = 'OVERBOUGHT'
        else:
            condition = 'NEUTRAL'

        base_analysis.update({
            'current_price': float(current_price),
            'rsi': float(current_rsi) if not pd.isna(current_rsi) else None,
            'condition': condition,
            'oversold_threshold': self.oversold,
            'overbought_threshold': self.overbought
        })

        return base_analysis
