"""
Trader
Main trading engine that executes strategies
"""

import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from ..api.alpaca_client import AlpacaClient
from ..strategies.base_strategy import BaseStrategy
from .risk_manager import RiskManager


class Trader:
    """
    Main trading engine
    """

    def __init__(
        self,
        api_client: AlpacaClient,
        strategy: BaseStrategy,
        risk_manager: Optional[RiskManager] = None,
        symbols: Optional[List[str]] = None,
        check_interval: int = 60  # seconds
    ):
        """
        Initialize trader

        Args:
            api_client: Alpaca API client
            strategy: Trading strategy
            risk_manager: Risk manager (optional)
            symbols: List of symbols to trade (default: ['SPY'])
            check_interval: How often to check for signals (seconds)
        """
        self.api_client = api_client
        self.strategy = strategy
        self.risk_manager = risk_manager or RiskManager()
        self.symbols = symbols or ['SPY']
        self.check_interval = check_interval

        self.is_running = False
        self.positions = {}
        self.initial_portfolio_value = 0.0

        self.logger = logging.getLogger(__name__)

    def start(self):
        """Start the trading bot"""
        self.logger.info("Starting trading bot...")
        self.is_running = True

        # Get initial portfolio value
        account = self.api_client.get_account()
        self.initial_portfolio_value = account['portfolio_value']
        self.risk_manager.peak_portfolio_value = self.initial_portfolio_value

        self.logger.info(f"Initial portfolio value: ${self.initial_portfolio_value:,.2f}")
        self.logger.info(f"Trading symbols: {', '.join(self.symbols)}")
        self.logger.info(f"Strategy: {self.strategy.name}")

        try:
            while self.is_running:
                self._trading_loop()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.logger.info("Stopping trading bot...")
            self.stop()
        except Exception as e:
            self.logger.error(f"Error in trading loop: {e}", exc_info=True)
            self.stop()

    def stop(self):
        """Stop the trading bot"""
        self.is_running = False
        self.logger.info("Trading bot stopped")

    def _trading_loop(self):
        """Main trading loop iteration"""
        try:
            # Check risk limits
            account = self.api_client.get_account()
            portfolio_value = account['portfolio_value']

            within_limits, reason = self.risk_manager.check_risk_limits(
                portfolio_value,
                self.initial_portfolio_value
            )

            if not within_limits:
                self.logger.warning(f"Risk limit breached: {reason}. Closing all positions.")
                self.api_client.close_all_positions()
                self.stop()
                return

            # Process each symbol
            for symbol in self.symbols:
                self._process_symbol(symbol, portfolio_value)

        except Exception as e:
            self.logger.error(f"Error in trading loop: {e}", exc_info=True)

    def _process_symbol(self, symbol: str, portfolio_value: float):
        """Process trading logic for a symbol"""
        try:
            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=100)  # Get enough data for indicators

            data = self.api_client.get_historical_data(
                symbol=symbol,
                start=start_date,
                end=end_date,
                timeframe='1Day'
            )

            if data.empty:
                self.logger.warning(f"No data available for {symbol}")
                return

            # Analyze with strategy
            analysis = self.strategy.analyze(data)
            signal = analysis['signal']
            current_price = analysis.get('current_price', data['close'].iloc[-1])

            self.logger.info(f"{symbol}: {signal} | Price: ${current_price:.2f}")

            # Get current position
            position = self.api_client.get_position(symbol)

            # Handle existing position
            if position:
                self._handle_existing_position(symbol, position, current_price, signal)
            # Handle new position
            elif signal == 'BUY':
                self._handle_buy_signal(symbol, portfolio_value, current_price)
            elif signal == 'SELL':
                self.logger.debug(f"SELL signal for {symbol} but no position held")

        except Exception as e:
            self.logger.error(f"Error processing {symbol}: {e}", exc_info=True)

    def _handle_existing_position(
        self,
        symbol: str,
        position: Dict[str, Any],
        current_price: float,
        signal: str
    ):
        """Handle existing position"""
        entry_price = position['avg_entry_price']
        qty = position['qty']

        # Check stop-loss and take-profit
        should_close, reason = self.risk_manager.should_close_position(
            entry_price,
            current_price,
            'buy'
        )

        if should_close:
            self.logger.info(f"Closing position for {symbol}: {reason}")
            self.api_client.close_position(symbol)

            # Update daily P&L
            pnl = (current_price - entry_price) * qty
            self.risk_manager.update_daily_pnl(pnl)

        elif signal == 'SELL':
            self.logger.info(f"SELL signal for {symbol}, closing position")
            self.api_client.close_position(symbol)

            # Update daily P&L
            pnl = (current_price - entry_price) * qty
            self.risk_manager.update_daily_pnl(pnl)

    def _handle_buy_signal(self, symbol: str, portfolio_value: float, current_price: float):
        """Handle buy signal"""
        # Calculate position size
        shares = self.risk_manager.calculate_position_size(
            portfolio_value,
            current_price
        )

        if shares < 1:
            self.logger.debug(f"Position size too small for {symbol}: {shares}")
            return

        # Place order
        self.logger.info(f"BUY signal for {symbol}: {shares:.2f} shares @ ${current_price:.2f}")

        order = self.api_client.place_market_order(
            symbol=symbol,
            qty=shares,
            side='buy'
        )

        if order:
            self.logger.info(f"Order placed successfully: {order['id']}")
        else:
            self.logger.error(f"Failed to place order for {symbol}")

    def get_status(self) -> Dict[str, Any]:
        """Get current trading status"""
        account = self.api_client.get_account()
        positions = self.api_client.get_positions()

        return {
            'is_running': self.is_running,
            'strategy': self.strategy.name,
            'symbols': self.symbols,
            'account': account,
            'positions': positions,
            'risk_metrics': self.risk_manager.get_risk_metrics(),
            'initial_portfolio_value': self.initial_portfolio_value,
            'current_portfolio_value': account['portfolio_value'],
            'pnl': account['portfolio_value'] - self.initial_portfolio_value,
            'pnl_pct': ((account['portfolio_value'] - self.initial_portfolio_value) / self.initial_portfolio_value * 100) if self.initial_portfolio_value > 0 else 0
        }
