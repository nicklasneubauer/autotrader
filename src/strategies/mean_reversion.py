"""
Mean Reversion Strategy
Based on the principle that prices tend to return to their average

This is one of the most popular strategies used by quantitative hedge funds.
The strategy assumes that extreme price movements are temporary and will revert.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy


class MeanReversionStrategy(BaseStrategy):
    """
    Mean Reversion Strategy

    Buy when price is significantly below moving average (oversold)
    Sell when price is significantly above moving average (overbought)

    Used by:
    - Renaissance Technologies
    - D.E. Shaw
    - Many quant hedge funds

    Parameters:
        lookback_period: Period for calculating mean (default: 20)
        entry_threshold: Number of std devs for entry (default: 2.0)
        exit_threshold: Number of std devs for exit (default: 0.5)
        use_zscore: Use z-score instead of percentage deviation (default: True)
    """

    def __init__(
        self,
        lookback_period: int = 20,
        entry_threshold: float = 2.0,
        exit_threshold: float = 0.5,
        use_zscore: bool = True
    ):
        parameters = {
            'lookback_period': lookback_period,
            'entry_threshold': entry_threshold,
            'exit_threshold': exit_threshold,
            'use_zscore': use_zscore
        }
        super().__init__('MeanReversion', parameters)
        self.lookback_period = lookback_period
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.use_zscore = use_zscore

    def calculate_zscore(self, data: pd.Series) -> pd.Series:
        """
        Calculate rolling z-score
        Z-score = (current - mean) / std
        """
        mean = data.rolling(window=self.lookback_period).mean()
        std = data.rolling(window=self.lookback_period).std()
        zscore = (data - mean) / std
        return zscore

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate mean reversion signals

        Buy: When price is entry_threshold std devs below mean
        Sell: When price returns to within exit_threshold of mean
        """
        if data.empty or 'close' not in data.columns:
            self.logger.warning("Invalid data provided to strategy")
            return pd.Series(dtype=int)

        df = data.copy()

        if self.use_zscore:
            # Z-score method (more robust)
            df['zscore'] = self.calculate_zscore(df['close'])

            # Initialize signals
            signals = pd.Series(0, index=df.index)

            # Buy when extremely oversold (negative z-score)
            buy_condition = df['zscore'] < -self.entry_threshold
            signals[buy_condition] = 1

            # Sell when returns to mean or becomes overbought
            sell_condition = (df['zscore'] > -self.exit_threshold) | (df['zscore'] > self.entry_threshold)
            # Only sell if we were previously long (had a buy signal)
            prev_signals = signals.shift(1).fillna(0)
            sell_condition = sell_condition & (prev_signals == 1)
            signals[sell_condition] = -1

        else:
            # Percentage deviation method
            df['sma'] = df['close'].rolling(window=self.lookback_period).mean()
            df['std'] = df['close'].rolling(window=self.lookback_period).std()
            df['upper_band'] = df['sma'] + (self.entry_threshold * df['std'])
            df['lower_band'] = df['sma'] - (self.entry_threshold * df['std'])
            df['exit_upper'] = df['sma'] + (self.exit_threshold * df['std'])
            df['exit_lower'] = df['sma'] - (self.exit_threshold * df['std'])

            signals = pd.Series(0, index=df.index)

            # Buy when price crosses below lower band
            buy_condition = df['close'] < df['lower_band']
            signals[buy_condition] = 1

            # Sell when price returns to mean
            sell_condition = df['close'] > df['exit_lower']
            prev_signals = signals.shift(1).fillna(0)
            sell_condition = sell_condition & (prev_signals == 1)
            signals[sell_condition] = -1

        return signals

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Extended analysis with mean reversion metrics"""
        base_analysis = super().analyze(data)

        if data.empty or 'close' not in data.columns:
            return base_analysis

        df = data.copy()
        current_price = df['close'].iloc[-1]

        # Calculate metrics
        sma = df['close'].rolling(window=self.lookback_period).mean().iloc[-1]
        std = df['close'].rolling(window=self.lookback_period).std().iloc[-1]
        zscore = self.calculate_zscore(df['close']).iloc[-1]

        # Distance from mean
        if not pd.isna(sma) and not pd.isna(std):
            distance_pct = ((current_price - sma) / sma) * 100
            distance_std = (current_price - sma) / std if std > 0 else 0

            # Determine condition
            if zscore < -self.entry_threshold:
                condition = 'EXTREMELY_OVERSOLD'
            elif zscore < -1:
                condition = 'OVERSOLD'
            elif zscore > self.entry_threshold:
                condition = 'EXTREMELY_OVERBOUGHT'
            elif zscore > 1:
                condition = 'OVERBOUGHT'
            elif abs(zscore) < 0.5:
                condition = 'NEAR_MEAN'
            else:
                condition = 'NEUTRAL'
        else:
            distance_pct = None
            distance_std = None
            condition = 'INSUFFICIENT_DATA'

        base_analysis.update({
            'current_price': float(current_price),
            'mean': float(sma) if not pd.isna(sma) else None,
            'std': float(std) if not pd.isna(std) else None,
            'zscore': float(zscore) if not pd.isna(zscore) else None,
            'distance_from_mean_pct': float(distance_pct) if distance_pct is not None else None,
            'distance_in_std_devs': float(distance_std) if distance_std is not None else None,
            'condition': condition
        })

        return base_analysis
