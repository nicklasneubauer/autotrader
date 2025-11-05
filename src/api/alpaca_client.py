"""
Alpaca API Client
Handles connection to Alpaca for both paper and live trading
"""

import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, AssetClass
import logging


class AlpacaClient:
    """
    Wrapper for Alpaca API with support for both stocks and crypto
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        base_url: Optional[str] = None,
        paper: bool = True
    ):
        """
        Initialize Alpaca client

        Args:
            api_key: Alpaca API key (or set ALPACA_API_KEY env var)
            secret_key: Alpaca secret key (or set ALPACA_SECRET_KEY env var)
            base_url: API base URL (or set ALPACA_BASE_URL env var)
            paper: Use paper trading mode (default: True)
        """
        self.api_key = api_key or os.getenv('ALPACA_API_KEY')
        self.secret_key = secret_key or os.getenv('ALPACA_SECRET_KEY')
        self.base_url = base_url or os.getenv('ALPACA_BASE_URL',
                                               'https://paper-api.alpaca.markets' if paper else 'https://api.alpaca.markets')

        if not self.api_key or not self.secret_key:
            raise ValueError("API keys must be provided or set in environment variables")

        # Initialize clients
        self.trading_client = TradingClient(
            self.api_key,
            self.secret_key,
            paper=paper
        )

        self.stock_data_client = StockHistoricalDataClient(
            self.api_key,
            self.secret_key
        )

        self.crypto_data_client = CryptoHistoricalDataClient(
            self.api_key,
            self.secret_key
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Alpaca client initialized in {'paper' if paper else 'live'} trading mode")

    def get_account(self) -> Dict[str, Any]:
        """Get account information"""
        account = self.trading_client.get_account()
        return {
            'equity': float(account.equity),
            'cash': float(account.cash),
            'buying_power': float(account.buying_power),
            'portfolio_value': float(account.portfolio_value),
            'pattern_day_trader': account.pattern_day_trader,
            'trading_blocked': account.trading_blocked,
            'account_blocked': account.account_blocked
        }

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        positions = self.trading_client.get_all_positions()
        return [{
            'symbol': pos.symbol,
            'qty': float(pos.qty),
            'side': pos.side,
            'market_value': float(pos.market_value),
            'cost_basis': float(pos.cost_basis),
            'unrealized_pl': float(pos.unrealized_pl),
            'unrealized_plpc': float(pos.unrealized_plpc),
            'current_price': float(pos.current_price),
            'avg_entry_price': float(pos.avg_entry_price)
        } for pos in positions]

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position for a specific symbol"""
        try:
            pos = self.trading_client.get_open_position(symbol)
            return {
                'symbol': pos.symbol,
                'qty': float(pos.qty),
                'side': pos.side,
                'market_value': float(pos.market_value),
                'cost_basis': float(pos.cost_basis),
                'unrealized_pl': float(pos.unrealized_pl),
                'unrealized_plpc': float(pos.unrealized_plpc),
                'current_price': float(pos.current_price),
                'avg_entry_price': float(pos.avg_entry_price)
            }
        except Exception as e:
            self.logger.debug(f"No position found for {symbol}: {e}")
            return None

    def get_historical_data(
        self,
        symbol: str,
        start: datetime,
        end: Optional[datetime] = None,
        timeframe: str = '1Day',
        asset_type: str = 'stock'
    ) -> pd.DataFrame:
        """
        Get historical price data

        Args:
            symbol: Asset symbol (e.g., 'AAPL', 'BTC/USD')
            start: Start datetime
            end: End datetime (default: now)
            timeframe: Bar timeframe (1Min, 5Min, 15Min, 1Hour, 1Day, etc.)
            asset_type: 'stock' or 'crypto'

        Returns:
            DataFrame with OHLCV data
        """
        end = end or datetime.now()

        # Map timeframe string to TimeFrame enum
        timeframe_map = {
            '1Min': TimeFrame.Minute,
            '5Min': TimeFrame(5, TimeFrame.Unit.Minute),
            '15Min': TimeFrame(15, TimeFrame.Unit.Minute),
            '1Hour': TimeFrame.Hour,
            '1Day': TimeFrame.Day,
            '1Week': TimeFrame.Week,
            '1Month': TimeFrame.Month,
        }

        tf = timeframe_map.get(timeframe, TimeFrame.Day)

        try:
            if asset_type.lower() == 'crypto':
                request = CryptoBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=tf,
                    start=start,
                    end=end
                )
                bars = self.crypto_data_client.get_crypto_bars(request)
            else:
                request = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    timeframe=tf,
                    start=start,
                    end=end
                )
                bars = self.stock_data_client.get_stock_bars(request)

            # Convert to DataFrame
            df = bars.df
            if not df.empty and 'symbol' in df.index.names:
                df = df.reset_index(level='symbol', drop=True)

            return df

        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()

    def place_market_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        time_in_force: str = 'day'
    ) -> Optional[Dict[str, Any]]:
        """
        Place a market order

        Args:
            symbol: Asset symbol
            qty: Quantity to trade
            side: 'buy' or 'sell'
            time_in_force: 'day', 'gtc', 'ioc', 'fok'

        Returns:
            Order details or None if failed
        """
        try:
            order_side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
            tif_map = {
                'day': TimeInForce.DAY,
                'gtc': TimeInForce.GTC,
                'ioc': TimeInForce.IOC,
                'fok': TimeInForce.FOK
            }

            request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=tif_map.get(time_in_force.lower(), TimeInForce.DAY)
            )

            order = self.trading_client.submit_order(request)

            self.logger.info(f"Market order placed: {side.upper()} {qty} {symbol}")

            return {
                'id': str(order.id),
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side.value,
                'type': order.type.value,
                'status': order.status.value,
                'filled_qty': float(order.filled_qty) if order.filled_qty else 0,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None,
                'submitted_at': order.submitted_at
            }

        except Exception as e:
            self.logger.error(f"Error placing market order: {e}")
            return None

    def place_limit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        limit_price: float,
        time_in_force: str = 'day'
    ) -> Optional[Dict[str, Any]]:
        """
        Place a limit order

        Args:
            symbol: Asset symbol
            qty: Quantity to trade
            side: 'buy' or 'sell'
            limit_price: Limit price
            time_in_force: 'day', 'gtc', 'ioc', 'fok'

        Returns:
            Order details or None if failed
        """
        try:
            order_side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
            tif_map = {
                'day': TimeInForce.DAY,
                'gtc': TimeInForce.GTC,
                'ioc': TimeInForce.IOC,
                'fok': TimeInForce.FOK
            }

            request = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=order_side,
                time_in_force=tif_map.get(time_in_force.lower(), TimeInForce.DAY),
                limit_price=limit_price
            )

            order = self.trading_client.submit_order(request)

            self.logger.info(f"Limit order placed: {side.upper()} {qty} {symbol} @ ${limit_price}")

            return {
                'id': str(order.id),
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side.value,
                'type': order.type.value,
                'limit_price': float(order.limit_price),
                'status': order.status.value,
                'filled_qty': float(order.filled_qty) if order.filled_qty else 0,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None,
                'submitted_at': order.submitted_at
            }

        except Exception as e:
            self.logger.error(f"Error placing limit order: {e}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            self.trading_client.cancel_order_by_id(order_id)
            self.logger.info(f"Order {order_id} cancelled")
            return True
        except Exception as e:
            self.logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    def get_orders(self, status: str = 'open') -> List[Dict[str, Any]]:
        """Get orders by status (open, closed, all)"""
        try:
            from alpaca.trading.enums import QueryOrderStatus
            status_map = {
                'open': QueryOrderStatus.OPEN,
                'closed': QueryOrderStatus.CLOSED,
                'all': QueryOrderStatus.ALL
            }

            from alpaca.trading.requests import GetOrdersRequest
            request = GetOrdersRequest(status=status_map.get(status, QueryOrderStatus.OPEN))
            orders = self.trading_client.get_orders(request)

            return [{
                'id': str(order.id),
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side.value,
                'type': order.type.value,
                'status': order.status.value,
                'filled_qty': float(order.filled_qty) if order.filled_qty else 0,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None,
                'submitted_at': order.submitted_at
            } for order in orders]

        except Exception as e:
            self.logger.error(f"Error fetching orders: {e}")
            return []

    def close_position(self, symbol: str) -> bool:
        """Close a position entirely"""
        try:
            self.trading_client.close_position(symbol)
            self.logger.info(f"Position closed for {symbol}")
            return True
        except Exception as e:
            self.logger.error(f"Error closing position for {symbol}: {e}")
            return False

    def close_all_positions(self) -> bool:
        """Close all open positions"""
        try:
            self.trading_client.close_all_positions(cancel_orders=True)
            self.logger.info("All positions closed")
            return True
        except Exception as e:
            self.logger.error(f"Error closing all positions: {e}")
            return False
