"""
Advanced Features Example
Demonstrates new features: MACD, Bollinger Bands, Parameter Optimization, Notifications
"""

import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.api.alpaca_client import AlpacaClient
from src.strategies.macd_strategy import MACDStrategy
from src.strategies.bollinger_bands import BollingerBandsStrategy
from src.strategies.moving_average import MovingAverageCrossover
from src.backtesting.backtest_engine import BacktestEngine
from src.optimization import ParameterOptimizer, GeneticOptimizer
from src.analytics import PerformanceAnalyzer
from src.notifications import NotificationManager, TelegramNotifier
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger(level='INFO')


def example_macd_strategy():
    """Test MACD strategy"""
    logger.info("="*80)
    logger.info("MACD Strategy Example")
    logger.info("="*80)

    # Initialize client
    client = AlpacaClient(paper=True)

    # Get historical data
    symbol = 'AAPL'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    logger.info(f"Fetching data for {symbol}...")
    data = client.get_historical_data(
        symbol=symbol,
        start=start_date,
        end=end_date,
        timeframe='1Day'
    )

    # Create MACD strategy
    strategy = MACDStrategy(
        fast_period=12,
        slow_period=26,
        signal_period=9
    )

    # Run backtest
    engine = BacktestEngine(initial_capital=100000)
    results = engine.run(strategy, data)

    # Print results
    logger.info(f"\nMACDStrategy Results for {symbol}:")
    logger.info(f"  Total Return: {results['total_return']:.2f}%")
    logger.info(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    logger.info(f"  Max Drawdown: {results['max_drawdown']:.2f}%")
    logger.info(f"  Win Rate: {results['win_rate']:.2f}%")
    logger.info(f"  Number of Trades: {results['num_trades']}")


def example_bollinger_bands():
    """Test Bollinger Bands strategy"""
    logger.info("\n" + "="*80)
    logger.info("Bollinger Bands Strategy Example")
    logger.info("="*80)

    client = AlpacaClient(paper=True)

    symbol = 'SPY'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    logger.info(f"Fetching data for {symbol}...")
    data = client.get_historical_data(
        symbol=symbol,
        start=start_date,
        end=end_date,
        timeframe='1Day'
    )

    # Create Bollinger Bands strategy
    strategy = BollingerBandsStrategy(
        period=20,
        num_std=2.0
    )

    # Run backtest
    engine = BacktestEngine(initial_capital=100000)
    results = engine.run(strategy, data)

    # Print results
    logger.info(f"\nBollinger Bands Results for {symbol}:")
    logger.info(f"  Total Return: {results['total_return']:.2f}%")
    logger.info(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    logger.info(f"  Max Drawdown: {results['max_drawdown']:.2f}%")
    logger.info(f"  Win Rate: {results['win_rate']:.2f}%")
    logger.info(f"  Number of Trades: {results['num_trades']}")


def example_parameter_optimization():
    """Optimize strategy parameters"""
    logger.info("\n" + "="*80)
    logger.info("Parameter Optimization Example")
    logger.info("="*80)

    client = AlpacaClient(paper=True)

    symbol = 'SPY'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years for optimization

    logger.info(f"Fetching data for {symbol}...")
    data = client.get_historical_data(
        symbol=symbol,
        start=start_date,
        end=end_date,
        timeframe='1Day'
    )

    # Grid search optimization for Moving Average strategy
    logger.info("\nOptimizing Moving Average Crossover strategy...")

    optimizer = ParameterOptimizer(
        strategy_class=MovingAverageCrossover,
        data=data,
        initial_capital=100000,
        metric='sharpe_ratio'
    )

    param_grid = {
        'short_window': [10, 20, 30],
        'long_window': [40, 50, 60],
        'ma_type': ['sma', 'ema']
    }

    best_params, best_results = optimizer.grid_search(param_grid)

    logger.info("\nOptimization Results:")
    logger.info(f"  Best Parameters: {best_params}")
    logger.info(f"  Sharpe Ratio: {best_results['sharpe_ratio']:.2f}")
    logger.info(f"  Total Return: {best_results['total_return']:.2f}%")

    # Get results DataFrame
    results_df = optimizer.get_results_dataframe()
    logger.info(f"\nTop 5 Parameter Combinations:")
    logger.info(results_df.head())


def example_genetic_optimization():
    """Optimize using genetic algorithm"""
    logger.info("\n" + "="*80)
    logger.info("Genetic Algorithm Optimization Example")
    logger.info("="*80)

    client = AlpacaClient(paper=True)

    symbol = 'MSFT'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)

    logger.info(f"Fetching data for {symbol}...")
    data = client.get_historical_data(
        symbol=symbol,
        start=start_date,
        end=end_date,
        timeframe='1Day'
    )

    # Genetic optimization for MACD
    logger.info("\nOptimizing MACD strategy with Genetic Algorithm...")

    param_bounds = {
        'fast_period': (5, 20),
        'slow_period': (20, 50),
        'signal_period': (5, 15)
    }

    optimizer = GeneticOptimizer(
        strategy_class=MACDStrategy,
        data=data,
        param_bounds=param_bounds,
        metric='sharpe_ratio',
        population_size=30,
        generations=10
    )

    best_params, best_results = optimizer.optimize()

    logger.info("\nGenetic Optimization Results:")
    logger.info(f"  Best Parameters: {best_params}")
    logger.info(f"  Sharpe Ratio: {best_results['sharpe_ratio']:.2f}")
    logger.info(f"  Total Return: {best_results['total_return']:.2f}%")


def example_advanced_analytics():
    """Advanced performance analytics"""
    logger.info("\n" + "="*80)
    logger.info("Advanced Performance Analytics Example")
    logger.info("="*80)

    client = AlpacaClient(paper=True)

    symbol = 'SPY'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    data = client.get_historical_data(
        symbol=symbol,
        start=start_date,
        end=end_date,
        timeframe='1Day'
    )

    # Run backtest
    strategy = MovingAverageCrossover(short_window=20, long_window=50)
    engine = BacktestEngine(initial_capital=100000)
    results = engine.run(strategy, data)

    # Perform advanced analytics
    from src.analytics import PerformanceAnalyzer, MonteCarloSimulation
    import pandas as pd

    # Create equity curve series
    equity_curve = pd.Series(
        [v['total'] for v in results['equity_curve'].values()],
        index=list(results['equity_curve'].keys())
    )

    analyzer = PerformanceAnalyzer(
        trades=results['trades'],
        equity_curve=equity_curve
    )

    # Generate comprehensive report
    report = analyzer.generate_report()
    print(report)

    # Monte Carlo simulation
    returns = equity_curve.pct_change().dropna()
    mc = MonteCarloSimulation(returns, n_simulations=1000)
    mc_results = mc.run(n_periods=252)

    logger.info("\nMonte Carlo Simulation Results (1 year projection):")
    logger.info(f"  Mean Return: {mc_results['mean_return']:.2f}%")
    logger.info(f"  5th Percentile: {mc_results['percentile_5']:.2f}%")
    logger.info(f"  95th Percentile: {mc_results['percentile_95']:.2f}%")
    logger.info(f"  Probability of Positive Return: {mc_results['probability_positive']:.2f}%")


async def example_notifications():
    """Test notification system"""
    logger.info("\n" + "="*80)
    logger.info("Notification System Example")
    logger.info("="*80)

    # Initialize notification manager
    notification_manager = NotificationManager()

    # Add Telegram channel (if configured)
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if telegram_token and telegram_chat_id:
        telegram = TelegramNotifier(
            bot_token=telegram_token,
            chat_ids=[telegram_chat_id]
        )
        notification_manager.add_channel(telegram)
        logger.info("Telegram notifications enabled")
    else:
        logger.warning("Telegram credentials not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")

    # Send test notifications
    await notification_manager.notify_bot_status(is_running=True, strategy="Example Strategy")
    await asyncio.sleep(1)

    await notification_manager.notify_trade(
        symbol="SPY",
        side="buy",
        quantity=10,
        price=450.25
    )
    await asyncio.sleep(1)

    await notification_manager.notify_signal(
        symbol="AAPL",
        signal="BUY",
        strategy="MACD",
        details={
            'macd': 2.5,
            'signal_line': 1.8,
            'histogram': 0.7
        }
    )
    await asyncio.sleep(1)

    await notification_manager.notify_performance(
        portfolio_value=105250.50,
        pnl=5250.50,
        pnl_pct=5.25
    )

    logger.info("Notifications sent successfully!")


def main():
    """Run all examples"""
    logger.info("Starting Advanced Features Examples\n")

    # Run examples
    example_macd_strategy()
    example_bollinger_bands()
    example_parameter_optimization()
    example_genetic_optimization()
    example_advanced_analytics()

    # Notifications (async)
    logger.info("\nTesting notifications...")
    asyncio.run(example_notifications())

    logger.info("\n" + "="*80)
    logger.info("All examples completed!")
    logger.info("="*80)


if __name__ == "__main__":
    main()
