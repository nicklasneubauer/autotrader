"""
Turtle Trading System
The famous trend-following system that made millions

Richard Dennis trained a group of traders (the "Turtles") with this system in the 1980s.
They turned $1 million into $100 million in 4 years.

Rules:
1. Entry: Break out of 20-day high (buy) or 20-day low (sell)
2. Exit: Break out of 10-day low (for longs) or 10-day high (for shorts)
3. Use ATR for position sizing
4. Pyramid into winning positions

This is one of the most profitable trend-following systems ever created.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import BaseStrategy


class TurtleTradingStrategy(BaseStrategy):
    """
    Turtle Trading System - Richard Dennis' legendary strategy

    Entry System:
    - System 1: 20-day breakout (more trades, lower returns)
    - System 2: 55-day breakout (fewer trades, higher returns)

    Exit:
    - Exit on 10-day (System 1) or 20-day (System 2) opposite breakout

    Parameters:
        entry_period: Breakout period for entry (default: 20)
        exit_period: Breakout period for exit (default: 10)
        atr_period: Period for ATR calculation (default: 20)
        use_system_2: Use 55-day entry (default: False)
    """

    def __init__(
        self,
        entry_period: int = 20,
        exit_period: int = 10,
        atr_period: int = 20,
        use_system_2: bool = False
    ):
        if use_system_2:
            entry_period = 55
            exit_period = 20

        parameters = {
            'entry_period': entry_period,
            'exit_period': exit_period,
            'atr_period': atr_period,
            'system': 'System 2' if use_system_2 else 'System 1'
        }
        super().__init__('TurtleTrading', parameters)
        self.entry_period = entry_period
        self.exit_period = exit_period
        self.atr_period = atr_period

    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """Calculate Average True Range (ATR)"""
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR is the moving average of True Range
        atr = tr.rolling(window=self.atr_period).mean()
        return atr

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate Turtle Trading signals

        Buy: Price breaks above highest high of last entry_period days
        Sell: Price breaks below lowest low of last exit_period days (for longs)
        """
        required_cols = ['high', 'low', 'close']
        if data.empty or not all(col in data.columns for col in required_cols):
            self.logger.warning("Invalid data provided to strategy - need OHLC data")
            return pd.Series(dtype=int)

        df = data.copy()

        # Calculate breakout levels
        df['highest_high'] = df['high'].rolling(window=self.entry_period).max()
        df['lowest_low'] = df['low'].rolling(window=self.entry_period).min()

        # Exit levels (shorter period)
        df['exit_highest'] = df['high'].rolling(window=self.exit_period).max()
        df['exit_lowest'] = df['low'].rolling(window=self.exit_period).min()

        # Calculate ATR for reference
        df['atr'] = self.calculate_atr(df['high'], df['low'], df['close'])

        # Initialize signals
        signals = pd.Series(0, index=df.index)

        # Track position state
        in_position = False

        for i in range(self.entry_period, len(df)):
            current_price = df['close'].iloc[i]
            prev_high = df['highest_high'].iloc[i-1]
            prev_low = df['lowest_low'].iloc[i-1]
            exit_low = df['exit_lowest'].iloc[i-1]

            if not in_position:
                # Entry: Breakout above previous high
                if current_price > prev_high:
                    signals.iloc[i] = 1
                    in_position = True
                    self.logger.debug(f"Turtle BUY: Price {current_price:.2f} > High {prev_high:.2f}")

            else:
                # Exit: Break below exit low
                if current_price < exit_low:
                    signals.iloc[i] = -1
                    in_position = False
                    self.logger.debug(f"Turtle SELL: Price {current_price:.2f} < Exit Low {exit_low:.2f}")

        return signals

    def calculate_position_size(
        self,
        portfolio_value: float,
        current_price: float,
        atr: float
    ) -> float:
        """
        Calculate position size using Turtle's N-based sizing

        The Turtles risked 1% of their account per trade.
        Position Size = (1% of Capital) / (2 * ATR)
        """
        risk_per_trade = portfolio_value * 0.01  # 1% risk
        if atr > 0:
            position_size = risk_per_trade / (2 * atr)
            shares = position_size / current_price
            return shares
        return 0

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Extended analysis with Turtle metrics"""
        base_analysis = super().analyze(data)

        required_cols = ['high', 'low', 'close']
        if data.empty or not all(col in data.columns for col in required_cols):
            return base_analysis

        df = data.copy()

        # Calculate current levels
        highest_high = df['high'].rolling(window=self.entry_period).max().iloc[-1]
        lowest_low = df['low'].rolling(window=self.entry_period).min().iloc[-1]
        exit_lowest = df['low'].rolling(window=self.exit_period).min().iloc[-1]
        atr = self.calculate_atr(df['high'], df['low'], df['close']).iloc[-1]

        current_price = df['close'].iloc[-1]

        # Calculate distances
        distance_to_entry = ((highest_high - current_price) / current_price) * 100
        distance_to_exit = ((current_price - exit_lowest) / current_price) * 100

        # Determine market state
        if current_price > highest_high * 0.99:  # Within 1% of breakout
            market_state = 'NEAR_BREAKOUT'
        elif current_price < exit_lowest * 1.01:
            market_state = 'NEAR_EXIT'
        elif current_price > (highest_high + lowest_low) / 2:
            market_state = 'UPPER_RANGE'
        else:
            market_state = 'LOWER_RANGE'

        base_analysis.update({
            'current_price': float(current_price),
            'entry_breakout_level': float(highest_high) if not pd.isna(highest_high) else None,
            'exit_level': float(exit_lowest) if not pd.isna(exit_lowest) else None,
            'atr': float(atr) if not pd.isna(atr) else None,
            'distance_to_entry_pct': float(distance_to_entry) if not pd.isna(distance_to_entry) else None,
            'distance_to_exit_pct': float(distance_to_exit) if not pd.isna(distance_to_exit) else None,
            'market_state': market_state,
            'volatility_2atr': float(2 * atr) if not pd.isna(atr) else None
        })

        return base_analysis
