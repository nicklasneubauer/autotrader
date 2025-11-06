"""
Pairs Trading Strategy
Statistical arbitrage between correlated assets

Used extensively by:
- Renaissance Technologies (Medallion Fund)
- Citadel
- Two Sigma
- DE Shaw

The strategy exploits temporary divergences between historically correlated assets.

Example pairs:
- Coca-Cola (KO) vs Pepsi (PEP)
- Gold (GLD) vs Silver (SLV)
- S&P 500 (SPY) vs Nasdaq (QQQ)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from .base_strategy import BaseStrategy


class PairsTradingStrategy(BaseStrategy):
    """
    Pairs Trading - Market Neutral Strategy

    Trade the spread between two correlated assets:
    1. Calculate spread = Asset1 - (hedge_ratio * Asset2)
    2. Calculate z-score of spread
    3. Buy spread when z-score < -entry_threshold (spread too low)
    4. Sell spread when z-score > entry_threshold (spread too high)
    5. Exit when z-score crosses exit_threshold

    Market neutral: Long one asset, short the other

    Parameters:
        lookback_period: Period for calculating mean/std (default: 20)
        entry_threshold: Z-score threshold for entry (default: 2.0)
        exit_threshold: Z-score threshold for exit (default: 0.5)
        hedge_ratio_period: Period for calculating hedge ratio (default: 60)
    """

    def __init__(
        self,
        lookback_period: int = 20,
        entry_threshold: float = 2.0,
        exit_threshold: float = 0.5,
        hedge_ratio_period: int = 60
    ):
        parameters = {
            'lookback_period': lookback_period,
            'entry_threshold': entry_threshold,
            'exit_threshold': exit_threshold,
            'hedge_ratio_period': hedge_ratio_period
        }
        super().__init__('PairsTrading', parameters)
        self.lookback_period = lookback_period
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.hedge_ratio_period = hedge_ratio_period

    def calculate_hedge_ratio(self, asset1: pd.Series, asset2: pd.Series) -> float:
        """
        Calculate hedge ratio using linear regression
        hedge_ratio = covariance(asset1, asset2) / variance(asset2)
        """
        if len(asset1) < self.hedge_ratio_period or len(asset2) < self.hedge_ratio_period:
            return 1.0

        # Use recent data
        a1 = asset1.iloc[-self.hedge_ratio_period:]
        a2 = asset2.iloc[-self.hedge_ratio_period:]

        # Calculate using numpy
        covariance = np.cov(a1, a2)[0][1]
        variance = np.var(a2)

        if variance > 0:
            hedge_ratio = covariance / variance
        else:
            hedge_ratio = 1.0

        return hedge_ratio

    def calculate_spread(
        self,
        asset1: pd.Series,
        asset2: pd.Series,
        hedge_ratio: float
    ) -> pd.Series:
        """
        Calculate spread between two assets
        spread = asset1 - (hedge_ratio * asset2)
        """
        spread = asset1 - (hedge_ratio * asset2)
        return spread

    def calculate_zscore(self, spread: pd.Series) -> pd.Series:
        """Calculate z-score of spread"""
        mean = spread.rolling(window=self.lookback_period).mean()
        std = spread.rolling(window=self.lookback_period).std()
        zscore = (spread - mean) / std
        return zscore

    def generate_signals_for_pair(
        self,
        asset1_data: pd.DataFrame,
        asset2_data: pd.DataFrame
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Generate signals for a pair of assets

        Returns:
            (signals_asset1, signals_asset2, spread)
        """
        if 'close' not in asset1_data.columns or 'close' not in asset2_data.columns:
            self.logger.warning("Both assets must have 'close' column")
            return pd.Series(dtype=int), pd.Series(dtype=int), pd.Series(dtype=float)

        # Align the data
        asset1 = asset1_data['close']
        asset2 = asset2_data['close']

        # Calculate hedge ratio
        hedge_ratio = self.calculate_hedge_ratio(asset1, asset2)
        self.logger.info(f"Calculated hedge ratio: {hedge_ratio:.4f}")

        # Calculate spread and z-score
        spread = self.calculate_spread(asset1, asset2, hedge_ratio)
        zscore = self.calculate_zscore(spread)

        # Generate signals
        signals_asset1 = pd.Series(0, index=asset1.index)
        signals_asset2 = pd.Series(0, index=asset2.index)

        # When spread is too low (z-score < -entry_threshold):
        # Buy asset1 (undervalued), Sell asset2 (overvalued)
        entry_long = zscore < -self.entry_threshold
        signals_asset1[entry_long] = 1   # Buy asset1
        signals_asset2[entry_long] = -1  # Sell/Short asset2

        # When spread is too high (z-score > entry_threshold):
        # Sell asset1 (overvalued), Buy asset2 (undervalued)
        entry_short = zscore > self.entry_threshold
        signals_asset1[entry_short] = -1  # Sell/Short asset1
        signals_asset2[entry_short] = 1   # Buy asset2

        # Exit when spread returns to mean
        exit_condition = abs(zscore) < self.exit_threshold
        # Only exit if we had a position
        prev_signal_1 = signals_asset1.shift(1).fillna(0)
        exit_condition = exit_condition & (prev_signal_1 != 0)

        # Exit signals (flatten position)
        signals_asset1[exit_condition] = 0
        signals_asset2[exit_condition] = 0

        return signals_asset1, signals_asset2, spread

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Single asset version - not ideal for pairs trading
        Use generate_signals_for_pair() instead
        """
        self.logger.warning("Pairs trading requires two assets. Use generate_signals_for_pair()")
        return pd.Series(0, index=data.index)

    def analyze_pair(
        self,
        asset1_data: pd.DataFrame,
        asset2_data: pd.DataFrame,
        asset1_symbol: str = "Asset1",
        asset2_symbol: str = "Asset2"
    ) -> Dict[str, Any]:
        """Analyze a pair of assets"""

        if 'close' not in asset1_data.columns or 'close' not in asset2_data.columns:
            return {
                'error': 'Both assets must have close prices',
                'strategy': self.name
            }

        asset1 = asset1_data['close']
        asset2 = asset2_data['close']

        # Calculate metrics
        hedge_ratio = self.calculate_hedge_ratio(asset1, asset2)
        spread = self.calculate_spread(asset1, asset2, hedge_ratio)
        zscore = self.calculate_zscore(spread)

        current_zscore = zscore.iloc[-1] if not zscore.empty else np.nan
        current_spread = spread.iloc[-1] if not spread.empty else np.nan

        # Calculate correlation
        correlation = asset1.corr(asset2)

        # Determine signal
        if not pd.isna(current_zscore):
            if current_zscore < -self.entry_threshold:
                signal = f'BUY_SPREAD (Long {asset1_symbol}, Short {asset2_symbol})'
                condition = 'SPREAD_TOO_LOW'
            elif current_zscore > self.entry_threshold:
                signal = f'SELL_SPREAD (Short {asset1_symbol}, Long {asset2_symbol})'
                condition = 'SPREAD_TOO_HIGH'
            elif abs(current_zscore) < self.exit_threshold:
                signal = 'NEUTRAL (Exit positions)'
                condition = 'SPREAD_AT_MEAN'
            else:
                signal = 'HOLD'
                condition = 'SPREAD_DIVERGING'
        else:
            signal = 'INSUFFICIENT_DATA'
            condition = 'INSUFFICIENT_DATA'

        return {
            'strategy': self.name,
            'asset1': asset1_symbol,
            'asset2': asset2_symbol,
            'signal': signal,
            'hedge_ratio': float(hedge_ratio),
            'current_spread': float(current_spread) if not pd.isna(current_spread) else None,
            'spread_zscore': float(current_zscore) if not pd.isna(current_zscore) else None,
            'correlation': float(correlation),
            'condition': condition,
            'entry_threshold': self.entry_threshold,
            'exit_threshold': self.exit_threshold,
            'asset1_price': float(asset1.iloc[-1]),
            'asset2_price': float(asset2.iloc[-1])
        }

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Override base analyze - pairs trading needs two assets"""
        return {
            'strategy': self.name,
            'message': 'Use analyze_pair() method for pairs trading',
            'parameters': self.parameters
        }
