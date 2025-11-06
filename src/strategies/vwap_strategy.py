"""
VWAP Strategy (Volume-Weighted Average Price)
Institutional traders use VWAP as a benchmark

Used by:
- All major investment banks
- Institutional traders
- Algorithmic trading desks
- Day traders

VWAP shows the average price weighted by volume.
Trading above VWAP = bullish, below VWAP = bearish
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy


class VWAPStrategy(BaseStrategy):
    """
    VWAP (Volume-Weighted Average Price) Strategy

    VWAP = Sum(Price * Volume) / Sum(Volume)

    Trading rules:
    - Buy when price crosses above VWAP (bullish)
    - Sell when price crosses below VWAP (bearish)
    - Use standard deviation bands for better entries

    Parameters:
        std_multiplier: Multiplier for standard deviation bands (default: 2.0)
        lookback_period: Period for VWAP calculation (default: 0 = since start of day)
        use_bands: Use VWAP bands for entry (default: True)
    """

    def __init__(
        self,
        std_multiplier: float = 2.0,
        lookback_period: int = 0,
        use_bands: bool = True
    ):
        parameters = {
            'std_multiplier': std_multiplier,
            'lookback_period': lookback_period,
            'use_bands': use_bands
        }
        super().__init__('VWAP', parameters)
        self.std_multiplier = std_multiplier
        self.lookback_period = lookback_period
        self.use_bands = use_bands

    def calculate_vwap(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate VWAP and bands

        Returns:
            (vwap, upper_band, lower_band)
        """
        # Typical price
        typical_price = (high + low + close) / 3

        # VWAP calculation
        if self.lookback_period > 0:
            # Rolling VWAP
            pv = typical_price * volume
            cumulative_pv = pv.rolling(window=self.lookback_period).sum()
            cumulative_volume = volume.rolling(window=self.lookback_period).sum()
        else:
            # Cumulative VWAP (from start)
            cumulative_pv = (typical_price * volume).cumsum()
            cumulative_volume = volume.cumsum()

        vwap = cumulative_pv / cumulative_volume

        # Calculate VWAP bands using standard deviation
        if self.use_bands:
            # Calculate squared difference
            squared_diff = ((typical_price - vwap) ** 2) * volume

            if self.lookback_period > 0:
                sum_squared_diff = squared_diff.rolling(window=self.lookback_period).sum()
            else:
                sum_squared_diff = squared_diff.cumsum()

            variance = sum_squared_diff / cumulative_volume
            std = np.sqrt(variance)

            upper_band = vwap + (self.std_multiplier * std)
            lower_band = vwap - (self.std_multiplier * std)
        else:
            upper_band = vwap
            lower_band = vwap

        return vwap, upper_band, lower_band

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate VWAP-based signals

        Buy: Price crosses above VWAP (or lower band)
        Sell: Price crosses below VWAP (or upper band)
        """
        required_cols = ['high', 'low', 'close', 'volume']
        if data.empty or not all(col in data.columns for col in required_cols):
            self.logger.warning("VWAP strategy requires OHLCV data")
            return pd.Series(dtype=int)

        df = data.copy()

        # Calculate VWAP and bands
        vwap, upper_band, lower_band = self.calculate_vwap(
            df['high'], df['low'], df['close'], df['volume']
        )

        df['vwap'] = vwap
        df['upper_band'] = upper_band
        df['lower_band'] = lower_band

        # Initialize signals
        signals = pd.Series(0, index=df.index)

        if self.use_bands:
            # Use bands for entries
            # Buy when price touches/crosses below lower band
            buy_condition = df['close'] <= df['lower_band']
            # Confirm with price moving back towards VWAP
            buy_condition = buy_condition & (df['close'] > df['close'].shift(1))

            # Sell when price touches/crosses above upper band
            sell_condition = df['close'] >= df['upper_band']
            # Confirm with price moving back towards VWAP
            sell_condition = sell_condition & (df['close'] < df['close'].shift(1))

        else:
            # Simple VWAP crossover
            price_above_vwap = df['close'] > df['vwap']
            price_above_vwap_prev = price_above_vwap.shift(1)

            # Buy when price crosses above VWAP
            buy_condition = (~price_above_vwap_prev) & price_above_vwap

            # Sell when price crosses below VWAP
            sell_condition = price_above_vwap_prev & (~price_above_vwap)

        signals[buy_condition] = 1
        signals[sell_condition] = -1

        return signals

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Extended analysis with VWAP metrics"""
        base_analysis = super().analyze(data)

        required_cols = ['high', 'low', 'close', 'volume']
        if data.empty or not all(col in data.columns for col in required_cols):
            return base_analysis

        df = data.copy()

        # Calculate VWAP
        vwap, upper_band, lower_band = self.calculate_vwap(
            df['high'], df['low'], df['close'], df['volume']
        )

        current_price = df['close'].iloc[-1]
        current_vwap = vwap.iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]

        # Calculate position relative to VWAP
        if not pd.isna(current_vwap):
            distance_pct = ((current_price - current_vwap) / current_vwap) * 100

            # Determine position
            if current_price > current_upper:
                position = 'ABOVE_UPPER_BAND'
            elif current_price > current_vwap:
                position = 'ABOVE_VWAP'
            elif current_price < current_lower:
                position = 'BELOW_LOWER_BAND'
            elif current_price < current_vwap:
                position = 'BELOW_VWAP'
            else:
                position = 'AT_VWAP'

            # Trading bias
            if distance_pct > 1:
                bias = 'BEARISH (Price too high)'
            elif distance_pct < -1:
                bias = 'BULLISH (Price too low)'
            else:
                bias = 'NEUTRAL'
        else:
            distance_pct = None
            position = 'INSUFFICIENT_DATA'
            bias = 'UNKNOWN'

        base_analysis.update({
            'current_price': float(current_price),
            'vwap': float(current_vwap) if not pd.isna(current_vwap) else None,
            'upper_band': float(current_upper) if not pd.isna(current_upper) else None,
            'lower_band': float(current_lower) if not pd.isna(current_lower) else None,
            'distance_from_vwap_pct': float(distance_pct) if distance_pct is not None else None,
            'position': position,
            'bias': bias
        })

        return base_analysis
