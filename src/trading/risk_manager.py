"""
Risk Manager
Handles position sizing, stop-loss, and risk limits
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime


class RiskManager:
    """
    Risk management for trading operations
    """

    def __init__(
        self,
        max_position_size: float = 0.1,     # Max 10% of portfolio per position
        max_portfolio_risk: float = 0.02,    # Max 2% risk per trade
        stop_loss_pct: float = 0.05,         # 5% stop loss
        take_profit_pct: float = 0.10,       # 10% take profit
        max_daily_loss: float = 0.05,        # Max 5% daily loss
        max_drawdown: float = 0.20           # Max 20% drawdown
    ):
        """
        Initialize risk manager

        Args:
            max_position_size: Maximum position size as fraction of portfolio
            max_portfolio_risk: Maximum risk per trade as fraction of portfolio
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
            max_daily_loss: Maximum daily loss as fraction of portfolio
            max_drawdown: Maximum drawdown as fraction of portfolio
        """
        self.max_position_size = max_position_size
        self.max_portfolio_risk = max_portfolio_risk
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_daily_loss = max_daily_loss
        self.max_drawdown = max_drawdown

        self.daily_pnl = 0.0
        self.daily_pnl_date = datetime.now().date()
        self.peak_portfolio_value = 0.0

        self.logger = logging.getLogger(__name__)

    def calculate_position_size(
        self,
        portfolio_value: float,
        current_price: float,
        volatility: Optional[float] = None
    ) -> float:
        """
        Calculate appropriate position size

        Args:
            portfolio_value: Current portfolio value
            current_price: Current asset price
            volatility: Optional volatility measure (0-1)

        Returns:
            Number of shares to trade
        """
        # Base position size
        max_investment = portfolio_value * self.max_position_size

        # Adjust for volatility if provided
        if volatility is not None and volatility > 0:
            # Reduce position size for high volatility
            volatility_adj = min(1.0, 0.5 / volatility) if volatility > 0.5 else 1.0
            max_investment *= volatility_adj

        # Calculate shares
        shares = max_investment / current_price

        self.logger.debug(f"Calculated position size: {shares:.2f} shares (${max_investment:.2f})")

        return shares

    def calculate_stop_loss(self, entry_price: float, side: str = 'buy') -> float:
        """
        Calculate stop-loss price

        Args:
            entry_price: Entry price
            side: 'buy' or 'sell'

        Returns:
            Stop-loss price
        """
        if side.lower() == 'buy':
            stop_price = entry_price * (1 - self.stop_loss_pct)
        else:
            stop_price = entry_price * (1 + self.stop_loss_pct)

        return stop_price

    def calculate_take_profit(self, entry_price: float, side: str = 'buy') -> float:
        """
        Calculate take-profit price

        Args:
            entry_price: Entry price
            side: 'buy' or 'sell'

        Returns:
            Take-profit price
        """
        if side.lower() == 'buy':
            take_profit = entry_price * (1 + self.take_profit_pct)
        else:
            take_profit = entry_price * (1 - self.take_profit_pct)

        return take_profit

    def should_close_position(
        self,
        entry_price: float,
        current_price: float,
        side: str = 'buy'
    ) -> tuple[bool, str]:
        """
        Check if position should be closed based on stop-loss or take-profit

        Args:
            entry_price: Entry price
            current_price: Current price
            side: 'buy' or 'sell'

        Returns:
            (should_close, reason)
        """
        stop_loss = self.calculate_stop_loss(entry_price, side)
        take_profit = self.calculate_take_profit(entry_price, side)

        if side.lower() == 'buy':
            if current_price <= stop_loss:
                return True, 'STOP_LOSS'
            elif current_price >= take_profit:
                return True, 'TAKE_PROFIT'
        else:
            if current_price >= stop_loss:
                return True, 'STOP_LOSS'
            elif current_price <= take_profit:
                return True, 'TAKE_PROFIT'

        return False, 'NONE'

    def update_daily_pnl(self, pnl: float):
        """
        Update daily P&L tracking

        Args:
            pnl: Profit/Loss amount
        """
        current_date = datetime.now().date()

        # Reset daily P&L if new day
        if current_date != self.daily_pnl_date:
            self.daily_pnl = 0.0
            self.daily_pnl_date = current_date

        self.daily_pnl += pnl

    def check_risk_limits(self, portfolio_value: float, initial_value: float) -> tuple[bool, str]:
        """
        Check if risk limits are breached

        Args:
            portfolio_value: Current portfolio value
            initial_value: Initial portfolio value

        Returns:
            (within_limits, reason)
        """
        # Update peak value
        if portfolio_value > self.peak_portfolio_value:
            self.peak_portfolio_value = portfolio_value

        # Check daily loss limit
        daily_loss_pct = abs(self.daily_pnl) / initial_value if initial_value > 0 else 0
        if self.daily_pnl < 0 and daily_loss_pct > self.max_daily_loss:
            return False, f'DAILY_LOSS_LIMIT_EXCEEDED ({daily_loss_pct:.2%})'

        # Check max drawdown
        if self.peak_portfolio_value > 0:
            current_drawdown = (self.peak_portfolio_value - portfolio_value) / self.peak_portfolio_value
            if current_drawdown > self.max_drawdown:
                return False, f'MAX_DRAWDOWN_EXCEEDED ({current_drawdown:.2%})'

        return True, 'OK'

    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics"""
        return {
            'daily_pnl': self.daily_pnl,
            'daily_pnl_date': str(self.daily_pnl_date),
            'peak_portfolio_value': self.peak_portfolio_value,
            'max_position_size': self.max_position_size,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'max_daily_loss': self.max_daily_loss,
            'max_drawdown': self.max_drawdown
        }
