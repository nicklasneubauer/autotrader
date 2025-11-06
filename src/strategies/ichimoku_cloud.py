"""
Ichimoku Cloud Strategy
Comprehensive Japanese trading system created by Goichi Hosoda

"Ichimoku Kinko Hyo" = "One Look Equilibrium Chart"

Used extensively by:
- Japanese traders
- Forex traders worldwide
- Crypto traders
- Professional technical analysts

The Ichimoku Cloud provides support/resistance, trend direction, and momentum
all in one indicator system.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy


class IchimokuCloudStrategy(BaseStrategy):
    """
    Ichimoku Cloud Strategy - Complete trading system

    Components:
    1. Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
    2. Kijun-sen (Base Line): (26-period high + 26-period low)/2
    3. Senkou Span A (Leading Span A): (Tenkan-sen + Kijun-sen)/2, shifted 26 periods
    4. Senkou Span B (Leading Span B): (52-period high + 52-period low)/2, shifted 26 periods
    5. Chikou Span (Lagging Span): Close price, shifted back 26 periods

    The "cloud" (Kumo) is the area between Senkou Span A and B.

    Trading Rules:
    - Buy when price is above cloud (bullish)
    - Sell when price is below cloud (bearish)
    - TK Cross: Buy when Tenkan crosses above Kijun
    - Cloud color: Green (A>B) = bullish, Red (B>A) = bearish

    Parameters:
        tenkan_period: Conversion line period (default: 9)
        kijun_period: Base line period (default: 26)
        senkou_span_b_period: Leading Span B period (default: 52)
    """

    def __init__(
        self,
        tenkan_period: int = 9,
        kijun_period: int = 26,
        senkou_span_b_period: int = 52
    ):
        parameters = {
            'tenkan_period': tenkan_period,
            'kijun_period': kijun_period,
            'senkou_span_b_period': senkou_span_b_period,
            'displacement': kijun_period
        }
        super().__init__('IchimokuCloud', parameters)
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period
        self.senkou_span_b_period = senkou_span_b_period

    def calculate_ichimoku(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series
    ) -> Dict[str, pd.Series]:
        """
        Calculate all Ichimoku components

        Returns:
            Dictionary with all Ichimoku lines
        """
        # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
        period9_high = high.rolling(window=self.tenkan_period).max()
        period9_low = low.rolling(window=self.tenkan_period).min()
        tenkan_sen = (period9_high + period9_low) / 2

        # Kijun-sen (Base Line): (26-period high + 26-period low)/2
        period26_high = high.rolling(window=self.kijun_period).max()
        period26_low = low.rolling(window=self.kijun_period).min()
        kijun_sen = (period26_high + period26_low) / 2

        # Senkou Span A (Leading Span A): (Tenkan-sen + Kijun-sen)/2, shifted forward 26 periods
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(self.kijun_period)

        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2, shifted forward 26 periods
        period52_high = high.rolling(window=self.senkou_span_b_period).max()
        period52_low = low.rolling(window=self.senkou_span_b_period).min()
        senkou_span_b = ((period52_high + period52_low) / 2).shift(self.kijun_period)

        # Chikou Span (Lagging Span): Close shifted back 26 periods
        chikou_span = close.shift(-self.kijun_period)

        return {
            'tenkan_sen': tenkan_sen,
            'kijun_sen': kijun_sen,
            'senkou_span_a': senkou_span_a,
            'senkou_span_b': senkou_span_b,
            'chikou_span': chikou_span
        }

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate Ichimoku-based signals

        Strong Buy: Price above cloud + TK cross + Green cloud
        Buy: Price crosses above cloud
        Sell: Price crosses below cloud
        Strong Sell: Price below cloud + TK cross down + Red cloud
        """
        required_cols = ['high', 'low', 'close']
        if data.empty or not all(col in data.columns for col in required_cols):
            self.logger.warning("Ichimoku strategy requires OHLC data")
            return pd.Series(dtype=int)

        df = data.copy()

        # Calculate Ichimoku components
        ichimoku = self.calculate_ichimoku(df['high'], df['low'], df['close'])
        for key, value in ichimoku.items():
            df[key] = value

        # Initialize signals
        signals = pd.Series(0, index=df.index)

        # Cloud top and bottom
        df['cloud_top'] = df[['senkou_span_a', 'senkou_span_b']].max(axis=1)
        df['cloud_bottom'] = df[['senkou_span_a', 'senkou_span_b']].min(axis=1)

        # Cloud color (green if A > B, red if B > A)
        df['cloud_green'] = df['senkou_span_a'] > df['senkou_span_b']

        # Price position relative to cloud
        df['price_above_cloud'] = df['close'] > df['cloud_top']
        df['price_below_cloud'] = df['close'] < df['cloud_bottom']

        # TK Cross
        df['tk_cross_up'] = (df['tenkan_sen'] > df['kijun_sen']) & (df['tenkan_sen'].shift(1) <= df['kijun_sen'].shift(1))
        df['tk_cross_down'] = (df['tenkan_sen'] < df['kijun_sen']) & (df['tenkan_sen'].shift(1) >= df['kijun_sen'].shift(1))

        # Generate signals
        for i in range(self.senkou_span_b_period, len(df)):
            # Strong Buy: Price above cloud + Bullish TK cross + Green cloud
            if (df['price_above_cloud'].iloc[i] and
                df['tk_cross_up'].iloc[i] and
                df['cloud_green'].iloc[i]):
                signals.iloc[i] = 1
                self.logger.debug(f"Strong BUY signal at {df.index[i]}")

            # Buy: Price crosses above cloud
            elif (df['price_above_cloud'].iloc[i] and
                  not df['price_above_cloud'].iloc[i-1] and
                  not df['price_below_cloud'].iloc[i-1]):
                signals.iloc[i] = 1
                self.logger.debug(f"BUY signal (cloud breakout) at {df.index[i]}")

            # Strong Sell: Price below cloud + Bearish TK cross + Red cloud
            elif (df['price_below_cloud'].iloc[i] and
                  df['tk_cross_down'].iloc[i] and
                  not df['cloud_green'].iloc[i]):
                signals.iloc[i] = -1
                self.logger.debug(f"Strong SELL signal at {df.index[i]}")

            # Sell: Price crosses below cloud
            elif (df['price_below_cloud'].iloc[i] and
                  not df['price_below_cloud'].iloc[i-1] and
                  not df['price_above_cloud'].iloc[i-1]):
                signals.iloc[i] = -1
                self.logger.debug(f"SELL signal (cloud breakdown) at {df.index[i]}")

        return signals

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Extended analysis with Ichimoku metrics"""
        base_analysis = super().analyze(data)

        required_cols = ['high', 'low', 'close']
        if data.empty or not all(col in data.columns for col in required_cols):
            return base_analysis

        df = data.copy()

        # Calculate Ichimoku
        ichimoku = self.calculate_ichimoku(df['high'], df['low'], df['close'])
        for key, value in ichimoku.items():
            df[key] = value

        current_price = df['close'].iloc[-1]

        # Get current values (use valid index, avoiding NaN from shift)
        idx = -self.kijun_period - 1 if len(df) > self.kijun_period else -1

        tenkan = df['tenkan_sen'].iloc[-1]
        kijun = df['kijun_sen'].iloc[-1]
        senkou_a = df['senkou_span_a'].iloc[idx] if len(df) > self.kijun_period else np.nan
        senkou_b = df['senkou_span_b'].iloc[idx] if len(df) > self.kijun_period else np.nan

        # Cloud metrics
        if not pd.isna(senkou_a) and not pd.isna(senkou_b):
            cloud_top = max(senkou_a, senkou_b)
            cloud_bottom = min(senkou_a, senkou_b)
            cloud_color = 'GREEN (Bullish)' if senkou_a > senkou_b else 'RED (Bearish)'

            # Price position
            if current_price > cloud_top:
                price_position = 'ABOVE_CLOUD (Bullish)'
            elif current_price < cloud_bottom:
                price_position = 'BELOW_CLOUD (Bearish)'
            else:
                price_position = 'INSIDE_CLOUD (Neutral)'

            cloud_thickness = ((cloud_top - cloud_bottom) / cloud_bottom) * 100
        else:
            cloud_top = None
            cloud_bottom = None
            cloud_color = 'INSUFFICIENT_DATA'
            price_position = 'INSUFFICIENT_DATA'
            cloud_thickness = None

        # TK Cross
        if not pd.isna(tenkan) and not pd.isna(kijun):
            if tenkan > kijun:
                tk_status = 'BULLISH (Tenkan > Kijun)'
            elif tenkan < kijun:
                tk_status = 'BEARISH (Tenkan < Kijun)'
            else:
                tk_status = 'NEUTRAL'
        else:
            tk_status = 'INSUFFICIENT_DATA'

        # Overall trend
        if price_position == 'ABOVE_CLOUD (Bullish)' and cloud_color == 'GREEN (Bullish)' and 'BULLISH' in tk_status:
            overall_trend = 'STRONG_BULLISH'
        elif price_position == 'ABOVE_CLOUD (Bullish)':
            overall_trend = 'BULLISH'
        elif price_position == 'BELOW_CLOUD (Bearish)' and cloud_color == 'RED (Bearish)' and 'BEARISH' in tk_status:
            overall_trend = 'STRONG_BEARISH'
        elif price_position == 'BELOW_CLOUD (Bearish)':
            overall_trend = 'BEARISH'
        else:
            overall_trend = 'NEUTRAL'

        base_analysis.update({
            'current_price': float(current_price),
            'tenkan_sen': float(tenkan) if not pd.isna(tenkan) else None,
            'kijun_sen': float(kijun) if not pd.isna(kijun) else None,
            'cloud_top': float(cloud_top) if cloud_top is not None else None,
            'cloud_bottom': float(cloud_bottom) if cloud_bottom is not None else None,
            'cloud_color': cloud_color,
            'cloud_thickness_pct': float(cloud_thickness) if cloud_thickness is not None else None,
            'price_position': price_position,
            'tk_status': tk_status,
            'overall_trend': overall_trend
        })

        return base_analysis
