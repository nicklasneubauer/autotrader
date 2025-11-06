"""Trading strategies"""

from .base_strategy import BaseStrategy
from .moving_average import MovingAverageCrossover
from .rsi_strategy import RSIStrategy
from .macd_strategy import MACDStrategy
from .bollinger_bands import BollingerBandsStrategy
from .mean_reversion import MeanReversionStrategy
from .turtle_trading import TurtleTradingStrategy
from .pairs_trading import PairsTradingStrategy
from .multi_strategy import MultiStrategyPortfolio
from .vwap_strategy import VWAPStrategy
from .ichimoku_cloud import IchimokuCloudStrategy

__all__ = [
    'BaseStrategy',
    'MovingAverageCrossover',
    'RSIStrategy',
    'MACDStrategy',
    'BollingerBandsStrategy',
    'MeanReversionStrategy',
    'TurtleTradingStrategy',
    'PairsTradingStrategy',
    'MultiStrategyPortfolio',
    'VWAPStrategy',
    'IchimokuCloudStrategy'
]
