"""
Base Strategy Class
All trading strategies should inherit from this class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import logging


class BaseStrategy(ABC):
    """Abstract base class for trading strategies"""

    def __init__(self, name: str, parameters: Optional[Dict[str, Any]] = None):
        """
        Initialize strategy

        Args:
            name: Strategy name
            parameters: Strategy-specific parameters
        """
        self.name = name
        self.parameters = parameters or {}
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on data

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Series with signals: 1 for buy, -1 for sell, 0 for hold
        """
        pass

    def should_buy(self, data: pd.DataFrame) -> bool:
        """
        Check if strategy suggests buying

        Args:
            data: DataFrame with OHLCV data

        Returns:
            True if buy signal detected
        """
        signals = self.generate_signals(data)
        return signals.iloc[-1] == 1 if not signals.empty else False

    def should_sell(self, data: pd.DataFrame) -> bool:
        """
        Check if strategy suggests selling

        Args:
            data: DataFrame with OHLCV data

        Returns:
            True if sell signal detected
        """
        signals = self.generate_signals(data)
        return signals.iloc[-1] == -1 if not signals.empty else False

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze current market conditions

        Args:
            data: DataFrame with OHLCV data

        Returns:
            Dictionary with analysis results
        """
        signals = self.generate_signals(data)
        current_signal = signals.iloc[-1] if not signals.empty else 0

        signal_map = {1: 'BUY', -1: 'SELL', 0: 'HOLD'}

        return {
            'strategy': self.name,
            'signal': signal_map[current_signal],
            'signal_value': int(current_signal),
            'parameters': self.parameters,
            'timestamp': data.index[-1] if not data.empty else None
        }

    def __str__(self) -> str:
        return f"{self.name} Strategy"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', parameters={self.parameters})>"
