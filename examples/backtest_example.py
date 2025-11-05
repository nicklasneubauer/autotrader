"""
Backtest Example
Run a backtest on historical data
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.api.alpaca_client import AlpacaClient
from src.strategies.moving_average import MovingAverageCrossover
from src.strategies.rsi_strategy import RSIStrategy
from src.backtesting.backtest_engine import BacktestEngine
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger(level='INFO')


def run_moving_average_backtest():
    """Run backtest with Moving Average strategy"""
    logger.info("Starting Moving Average backtest...")

    # Initialize Alpaca client
    client = AlpacaClient(paper=True)

    # Get historical data
    symbol = 'SPY'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1 year

    logger.info(f"Fetching historical data for {symbol}...")
    data = client.get_historical_data(
        symbol=symbol,
        start=start_date,
        end=end_date,
        timeframe='1Day'
    )

    if data.empty:
        logger.error("No data available")
        return

    logger.info(f"Got {len(data)} days of data")

    # Create strategy
    strategy = MovingAverageCrossover(
        short_window=20,
        long_window=50,
        ma_type='sma'
    )

    # Run backtest
    engine = BacktestEngine(
        initial_capital=100000,
        commission=0.001,
        slippage=0.0005
    )

    results = engine.run(strategy, data, position_size=1.0)

    # Print results
    logger.info("\n" + "="*50)
    logger.info("BACKTEST RESULTS")
    logger.info("="*50)
    logger.info(f"Strategy: {strategy.name}")
    logger.info(f"Symbol: {symbol}")
    logger.info(f"Period: {start_date.date()} to {end_date.date()}")
    logger.info(f"Initial Capital: ${results['initial_capital']:,.2f}")
    logger.info(f"Final Value: ${results['final_value']:,.2f}")
    logger.info(f"Total Return: {results['total_return']:.2f}%")
    logger.info(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    logger.info(f"Max Drawdown: {results['max_drawdown']:.2f}%")
    logger.info(f"Number of Trades: {results['num_trades']}")
    logger.info(f"Winning Trades: {results['winning_trades']}")
    logger.info(f"Losing Trades: {results['losing_trades']}")
    logger.info(f"Win Rate: {results['win_rate']:.2f}%")
    logger.info("="*50)


def run_rsi_backtest():
    """Run backtest with RSI strategy"""
    logger.info("Starting RSI backtest...")

    # Initialize Alpaca client
    client = AlpacaClient(paper=True)

    # Get historical data
    symbol = 'AAPL'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    logger.info(f"Fetching historical data for {symbol}...")
    data = client.get_historical_data(
        symbol=symbol,
        start=start_date,
        end=end_date,
        timeframe='1Day'
    )

    if data.empty:
        logger.error("No data available")
        return

    logger.info(f"Got {len(data)} days of data")

    # Create strategy
    strategy = RSIStrategy(
        period=14,
        oversold=30,
        overbought=70
    )

    # Run backtest
    engine = BacktestEngine(
        initial_capital=100000,
        commission=0.001,
        slippage=0.0005
    )

    results = engine.run(strategy, data, position_size=0.5)  # Use 50% of capital

    # Print results
    logger.info("\n" + "="*50)
    logger.info("BACKTEST RESULTS")
    logger.info("="*50)
    logger.info(f"Strategy: {strategy.name}")
    logger.info(f"Symbol: {symbol}")
    logger.info(f"Period: {start_date.date()} to {end_date.date()}")
    logger.info(f"Initial Capital: ${results['initial_capital']:,.2f}")
    logger.info(f"Final Value: ${results['final_value']:,.2f}")
    logger.info(f"Total Return: {results['total_return']:.2f}%")
    logger.info(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    logger.info(f"Max Drawdown: {results['max_drawdown']:.2f}%")
    logger.info(f"Number of Trades: {results['num_trades']}")
    logger.info(f"Winning Trades: {results['winning_trades']}")
    logger.info(f"Losing Trades: {results['losing_trades']}")
    logger.info(f"Win Rate: {results['win_rate']:.2f}%")
    logger.info("="*50)


if __name__ == "__main__":
    # Run both backtests
    run_moving_average_backtest()
    print("\n" + "="*80 + "\n")
    run_rsi_backtest()
