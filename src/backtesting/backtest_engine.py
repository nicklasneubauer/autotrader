"""
Backtesting Engine
Test trading strategies on historical data
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from ..strategies.base_strategy import BaseStrategy


class BacktestEngine:
    """
    Backtesting engine for trading strategies
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission: float = 0.001,  # 0.1% per trade
        slippage: float = 0.0005    # 0.05% slippage
    ):
        """
        Initialize backtest engine

        Args:
            initial_capital: Starting capital
            commission: Commission per trade (as decimal)
            slippage: Slippage per trade (as decimal)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.logger = logging.getLogger(__name__)

    def run(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
        position_size: float = 1.0
    ) -> Dict[str, Any]:
        """
        Run backtest

        Args:
            strategy: Trading strategy to test
            data: Historical price data with OHLCV
            position_size: Fraction of capital to use per trade (0-1)

        Returns:
            Dictionary with backtest results
        """
        if data.empty or 'close' not in data.columns:
            raise ValueError("Data must contain 'close' column")

        self.logger.info(f"Running backtest for {strategy.name}")

        # Generate signals
        signals = strategy.generate_signals(data)

        # Initialize tracking variables
        df = data.copy()
        df['signal'] = signals
        df['position'] = 0.0
        df['holdings'] = 0.0
        df['cash'] = self.initial_capital
        df['total'] = self.initial_capital
        df['returns'] = 0.0

        cash = self.initial_capital
        shares = 0.0
        trades = []

        # Simulate trading
        for i in range(len(df)):
            current_price = df['close'].iloc[i]
            signal = df['signal'].iloc[i]

            # Buy signal
            if signal == 1 and shares == 0:
                # Calculate number of shares to buy
                buy_amount = cash * position_size
                effective_price = current_price * (1 + self.slippage)
                shares_to_buy = buy_amount / effective_price
                commission_cost = buy_amount * self.commission

                if buy_amount > commission_cost:
                    shares = shares_to_buy
                    cash -= (buy_amount + commission_cost)

                    trades.append({
                        'date': df.index[i],
                        'type': 'BUY',
                        'price': effective_price,
                        'shares': shares,
                        'value': buy_amount,
                        'commission': commission_cost,
                        'cash': cash
                    })

                    self.logger.debug(f"BUY: {shares:.2f} shares @ ${effective_price:.2f}")

            # Sell signal
            elif signal == -1 and shares > 0:
                # Sell all shares
                effective_price = current_price * (1 - self.slippage)
                sell_amount = shares * effective_price
                commission_cost = sell_amount * self.commission

                cash += (sell_amount - commission_cost)

                trades.append({
                    'date': df.index[i],
                    'type': 'SELL',
                    'price': effective_price,
                    'shares': shares,
                    'value': sell_amount,
                    'commission': commission_cost,
                    'cash': cash
                })

                self.logger.debug(f"SELL: {shares:.2f} shares @ ${effective_price:.2f}")

                shares = 0.0

            # Update portfolio values
            df.loc[df.index[i], 'position'] = shares
            df.loc[df.index[i], 'holdings'] = shares * current_price
            df.loc[df.index[i], 'cash'] = cash
            df.loc[df.index[i], 'total'] = cash + (shares * current_price)

        # Calculate returns
        df['returns'] = df['total'].pct_change()

        # Calculate performance metrics
        results = self._calculate_metrics(df, trades)

        self.logger.info(f"Backtest complete. Total Return: {results['total_return']:.2f}%")

        return results

    def _calculate_metrics(self, df: pd.DataFrame, trades: List[Dict]) -> Dict[str, Any]:
        """Calculate performance metrics"""

        final_value = df['total'].iloc[-1]
        total_return = ((final_value - self.initial_capital) / self.initial_capital) * 100

        # Calculate returns statistics
        returns = df['returns'].dropna()
        sharpe_ratio = self._calculate_sharpe_ratio(returns)
        max_drawdown = self._calculate_max_drawdown(df['total'])

        # Trade statistics
        num_trades = len(trades)
        winning_trades = 0
        losing_trades = 0

        if num_trades >= 2:
            for i in range(0, len(trades) - 1, 2):
                if i + 1 < len(trades):
                    buy_trade = trades[i]
                    sell_trade = trades[i + 1]
                    if sell_trade['value'] > buy_trade['value']:
                        winning_trades += 1
                    else:
                        losing_trades += 1

        win_rate = (winning_trades / (winning_trades + losing_trades) * 100) if (winning_trades + losing_trades) > 0 else 0

        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'num_trades': num_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'trades': trades,
            'equity_curve': df[['total', 'holdings', 'cash']].to_dict('index')
        }

    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe Ratio

        Args:
            returns: Series of returns
            risk_free_rate: Annual risk-free rate

        Returns:
            Sharpe ratio
        """
        if returns.empty or returns.std() == 0:
            return 0.0

        # Assume daily returns, annualize
        excess_returns = returns - (risk_free_rate / 252)
        sharpe = np.sqrt(252) * (excess_returns.mean() / returns.std())

        return float(sharpe)

    def _calculate_max_drawdown(self, equity_curve: pd.Series) -> float:
        """
        Calculate maximum drawdown

        Args:
            equity_curve: Series of portfolio values

        Returns:
            Maximum drawdown as percentage
        """
        if equity_curve.empty:
            return 0.0

        cumulative_max = equity_curve.expanding().max()
        drawdown = (equity_curve - cumulative_max) / cumulative_max
        max_dd = drawdown.min() * 100

        return float(max_dd)
