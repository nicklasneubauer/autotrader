"""
Advanced Risk Management Extensions
"""

from typing import Dict, Any, Optional
import logging


class TrailingStopManager:
    """Manages trailing stops for positions"""

    def __init__(self, trailing_pct: float = 0.03):
        """
        Initialize trailing stop manager

        Args:
            trailing_pct: Trailing stop percentage (default: 3%)
        """
        self.trailing_pct = trailing_pct
        self.positions: Dict[str, Dict[str, float]] = {}
        self.logger = logging.getLogger(__name__)

    def initialize_position(self, symbol: str, entry_price: float, side: str = 'buy'):
        """
        Initialize trailing stop for a position

        Args:
            symbol: Symbol
            entry_price: Entry price
            side: Position side ('buy' or 'sell')
        """
        if side.lower() == 'buy':
            trailing_stop = entry_price * (1 - self.trailing_pct)
            highest_price = entry_price
        else:
            trailing_stop = entry_price * (1 + self.trailing_pct)
            highest_price = entry_price

        self.positions[symbol] = {
            'entry_price': entry_price,
            'highest_price': highest_price,
            'lowest_price': entry_price,
            'trailing_stop': trailing_stop,
            'side': side.lower()
        }
        self.logger.info(f"Initialized trailing stop for {symbol}: {trailing_stop:.2f}")

    def update(self, symbol: str, current_price: float) -> Optional[float]:
        """
        Update trailing stop

        Args:
            symbol: Symbol
            current_price: Current price

        Returns:
            New trailing stop price if updated, None otherwise
        """
        if symbol not in self.positions:
            return None

        pos = self.positions[symbol]
        side = pos['side']

        if side == 'buy':
            # For long positions, update if price makes new high
            if current_price > pos['highest_price']:
                pos['highest_price'] = current_price
                new_stop = current_price * (1 - self.trailing_pct)

                # Only move stop up, never down
                if new_stop > pos['trailing_stop']:
                    old_stop = pos['trailing_stop']
                    pos['trailing_stop'] = new_stop
                    self.logger.info(f"Updated trailing stop for {symbol}: {old_stop:.2f} -> {new_stop:.2f}")
                    return new_stop

        else:  # sell/short
            # For short positions, update if price makes new low
            if current_price < pos['lowest_price']:
                pos['lowest_price'] = current_price
                new_stop = current_price * (1 + self.trailing_pct)

                # Only move stop down, never up
                if new_stop < pos['trailing_stop']:
                    old_stop = pos['trailing_stop']
                    pos['trailing_stop'] = new_stop
                    self.logger.info(f"Updated trailing stop for {symbol}: {old_stop:.2f} -> {new_stop:.2f}")
                    return new_stop

        return None

    def should_exit(self, symbol: str, current_price: float) -> bool:
        """
        Check if trailing stop is hit

        Args:
            symbol: Symbol
            current_price: Current price

        Returns:
            True if should exit position
        """
        if symbol not in self.positions:
            return False

        pos = self.positions[symbol]
        side = pos['side']

        if side == 'buy':
            # Exit if price drops below trailing stop
            if current_price <= pos['trailing_stop']:
                self.logger.info(f"Trailing stop hit for {symbol}: {current_price:.2f} <= {pos['trailing_stop']:.2f}")
                return True
        else:
            # Exit if price rises above trailing stop
            if current_price >= pos['trailing_stop']:
                self.logger.info(f"Trailing stop hit for {symbol}: {current_price:.2f} >= {pos['trailing_stop']:.2f}")
                return True

        return False

    def get_stop_price(self, symbol: str) -> Optional[float]:
        """Get current trailing stop price for symbol"""
        if symbol in self.positions:
            return self.positions[symbol]['trailing_stop']
        return None

    def remove_position(self, symbol: str):
        """Remove position from tracking"""
        if symbol in self.positions:
            del self.positions[symbol]
            self.logger.info(f"Removed trailing stop tracking for {symbol}")

    def get_position_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get full position info"""
        return self.positions.get(symbol)


class ATRStopLoss:
    """ATR-based dynamic stop-loss calculator"""

    def __init__(self, atr_multiplier: float = 2.0):
        """
        Initialize ATR stop-loss

        Args:
            atr_multiplier: Multiplier for ATR (default: 2.0)
        """
        self.atr_multiplier = atr_multiplier
        self.logger = logging.getLogger(__name__)

    def calculate_atr(self, high: list, low: list, close: list, period: int = 14) -> float:
        """
        Calculate Average True Range

        Args:
            high: List of high prices
            low: List of low prices
            close: List of close prices
            period: ATR period

        Returns:
            ATR value
        """
        if len(high) < period + 1:
            return 0.0

        true_ranges = []
        for i in range(1, len(high)):
            tr = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )
            true_ranges.append(tr)

        # Calculate ATR as average of true ranges
        atr = sum(true_ranges[-period:]) / period
        return atr

    def calculate_stop(self, current_price: float, atr: float, side: str = 'buy') -> float:
        """
        Calculate stop-loss based on ATR

        Args:
            current_price: Current price
            atr: ATR value
            side: Position side

        Returns:
            Stop-loss price
        """
        if side.lower() == 'buy':
            stop = current_price - (atr * self.atr_multiplier)
        else:
            stop = current_price + (atr * self.atr_multiplier)

        return stop
