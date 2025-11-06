"""
Professional Trading Strategies Example
Demonstrates industry-proven algorithms used by hedge funds and professional traders

Strategies included:
1. Mean Reversion - Used by Renaissance Technologies, DE Shaw
2. Turtle Trading - Richard Dennis' $100M system
3. Pairs Trading - Statistical arbitrage (Renaissance, Citadel)
4. Multi-Strategy - Diversification across strategies
5. VWAP - Institutional benchmark
6. Ichimoku Cloud - Japanese all-in-one system
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.api.alpaca_client import AlpacaClient
from src.strategies.mean_reversion import MeanReversionStrategy
from src.strategies.turtle_trading import TurtleTradingStrategy
from src.strategies.pairs_trading import PairsTradingStrategy
from src.strategies.multi_strategy import MultiStrategyPortfolio
from src.strategies.vwap_strategy import VWAPStrategy
from src.strategies.ichimoku_cloud import IchimokuCloudStrategy
from src.strategies.moving_average import MovingAverageCrossover
from src.strategies.rsi_strategy import RSIStrategy
from src.backtesting.backtest_engine import BacktestEngine
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger(level='INFO')


def test_mean_reversion():
    """Mean Reversion - Renaissance Technologies style"""
    logger.info("="*80)
    logger.info("1. MEAN REVERSION STRATEGY")
    logger.info("Used by: Renaissance Technologies, D.E. Shaw")
    logger.info("="*80)

    client = AlpacaClient(paper=True)

    symbol = 'SPY'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    logger.info(f"\nFetching data for {symbol}...")
    data = client.get_historical_data(symbol, start_date, end_date, timeframe='1Day')

    # Mean Reversion Strategy
    strategy = MeanReversionStrategy(
        lookback_period=20,
        entry_threshold=2.0,  # 2 std devs
        exit_threshold=0.5,
        use_zscore=True
    )

    # Analyze current state
    analysis = strategy.analyze(data)
    logger.info(f"\nCurrent Analysis:")
    logger.info(f"  Price: ${analysis['current_price']:.2f}")
    logger.info(f"  Mean: ${analysis['mean']:.2f}")
    logger.info(f"  Z-Score: {analysis['zscore']:.2f}")
    logger.info(f"  Condition: {analysis['condition']}")
    logger.info(f"  Signal: {analysis['signal']}")

    # Backtest
    engine = BacktestEngine(initial_capital=100000)
    results = engine.run(strategy, data, position_size=0.5)

    logger.info(f"\nBacktest Results:")
    logger.info(f"  Total Return: {results['total_return']:.2f}%")
    logger.info(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    logger.info(f"  Max Drawdown: {results['max_drawdown']:.2f}%")
    logger.info(f"  Win Rate: {results['win_rate']:.2f}%")
    logger.info(f"  Number of Trades: {results['num_trades']}")


def test_turtle_trading():
    """Turtle Trading - Richard Dennis' legendary system"""
    logger.info("\n" + "="*80)
    logger.info("2. TURTLE TRADING SYSTEM")
    logger.info("Richard Dennis trained the 'Turtles' - $1M → $100M in 4 years")
    logger.info("="*80)

    client = AlpacaClient(paper=True)

    symbol = 'AAPL'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years

    logger.info(f"\nFetching data for {symbol}...")
    data = client.get_historical_data(symbol, start_date, end_date, timeframe='1Day')

    # Turtle System 1 (20-day breakout)
    strategy = TurtleTradingStrategy(
        entry_period=20,
        exit_period=10,
        use_system_2=False
    )

    analysis = strategy.analyze(data)
    logger.info(f"\nCurrent Analysis:")
    logger.info(f"  Price: ${analysis['current_price']:.2f}")
    logger.info(f"  Entry Breakout Level: ${analysis['entry_breakout_level']:.2f}")
    logger.info(f"  Exit Level: ${analysis['exit_level']:.2f}")
    logger.info(f"  ATR: ${analysis['atr']:.2f}")
    logger.info(f"  Market State: {analysis['market_state']}")
    logger.info(f"  Signal: {analysis['signal']}")

    # Backtest
    engine = BacktestEngine(initial_capital=100000)
    results = engine.run(strategy, data, position_size=1.0)

    logger.info(f"\nBacktest Results:")
    logger.info(f"  Total Return: {results['total_return']:.2f}%")
    logger.info(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    logger.info(f"  Max Drawdown: {results['max_drawdown']:.2f}%")
    logger.info(f"  Win Rate: {results['win_rate']:.2f}%")
    logger.info(f"  Number of Trades: {results['num_trades']}")


def test_pairs_trading():
    """Pairs Trading - Statistical Arbitrage"""
    logger.info("\n" + "="*80)
    logger.info("3. PAIRS TRADING (Statistical Arbitrage)")
    logger.info("Used by: Renaissance Technologies, Citadel, Two Sigma")
    logger.info("="*80)

    client = AlpacaClient(paper=True)

    # Example: SPY vs QQQ (S&P 500 vs Nasdaq)
    symbol1 = 'SPY'
    symbol2 = 'QQQ'

    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    logger.info(f"\nFetching data for {symbol1} and {symbol2}...")
    data1 = client.get_historical_data(symbol1, start_date, end_date, timeframe='1Day')
    data2 = client.get_historical_data(symbol2, start_date, end_date, timeframe='1Day')

    # Pairs Trading Strategy
    strategy = PairsTradingStrategy(
        lookback_period=20,
        entry_threshold=2.0,
        exit_threshold=0.5
    )

    # Analyze pair
    analysis = strategy.analyze_pair(data1, data2, symbol1, symbol2)

    logger.info(f"\nPair Analysis:")
    logger.info(f"  {symbol1} Price: ${analysis['asset1_price']:.2f}")
    logger.info(f"  {symbol2} Price: ${analysis['asset2_price']:.2f}")
    logger.info(f"  Hedge Ratio: {analysis['hedge_ratio']:.4f}")
    logger.info(f"  Spread Z-Score: {analysis['spread_zscore']:.2f}")
    logger.info(f"  Correlation: {analysis['correlation']:.2f}")
    logger.info(f"  Condition: {analysis['condition']}")
    logger.info(f"  Signal: {analysis['signal']}")

    logger.info("\nNote: Pairs trading requires specialized execution")
    logger.info("      Long one asset, short the other simultaneously")


def test_multi_strategy():
    """Multi-Strategy Portfolio - Diversification"""
    logger.info("\n" + "="*80)
    logger.info("4. MULTI-STRATEGY PORTFOLIO")
    logger.info("Combine multiple strategies like Renaissance Technologies")
    logger.info("="*80)

    client = AlpacaClient(paper=True)

    symbol = 'SPY'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)

    logger.info(f"\nFetching data for {symbol}...")
    data = client.get_historical_data(symbol, start_date, end_date, timeframe='1Day')

    # Create individual strategies
    ma_strategy = MovingAverageCrossover(short_window=20, long_window=50)
    rsi_strategy = RSIStrategy(period=14, oversold=30, overbought=70)
    mean_rev_strategy = MeanReversionStrategy(lookback_period=20, entry_threshold=2.0)

    # Combine with Multi-Strategy Portfolio
    multi_strategy = MultiStrategyPortfolio(
        strategies=[
            (ma_strategy, 0.4),        # 40% weight
            (rsi_strategy, 0.3),       # 30% weight
            (mean_rev_strategy, 0.3)   # 30% weight
        ],
        voting_method='weighted'
    )

    # Analyze
    analysis = multi_strategy.analyze(data)

    logger.info(f"\nMulti-Strategy Analysis:")
    logger.info(f"  Combined Signal: {analysis['signal']}")
    logger.info(f"  Voting Method: {analysis['voting_method']}")
    logger.info(f"  Buy Votes: {analysis['buy_votes']}/{len(multi_strategy.strategies)}")
    logger.info(f"  Sell Votes: {analysis['sell_votes']}/{len(multi_strategy.strategies)}")
    logger.info(f"  Weighted Score: {analysis['weighted_signal_score']:.2f}")

    logger.info(f"\nIndividual Strategy Signals:")
    for strat_analysis in analysis['individual_strategies']:
        logger.info(f"  {strat_analysis['strategy']}: {strat_analysis['signal']} (weight: {strat_analysis['weight']})")

    # Backtest
    engine = BacktestEngine(initial_capital=100000)
    results = engine.run(multi_strategy, data, position_size=1.0)

    logger.info(f"\nBacktest Results:")
    logger.info(f"  Total Return: {results['total_return']:.2f}%")
    logger.info(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    logger.info(f"  Max Drawdown: {results['max_drawdown']:.2f}%")
    logger.info(f"  Win Rate: {results['win_rate']:.2f}%")

    # Compare to individual strategies
    logger.info(f"\n  Compare to individual strategies:")
    for strategy, weight in multi_strategy.strategies:
        engine_single = BacktestEngine(initial_capital=100000)
        results_single = engine_single.run(strategy, data, position_size=1.0)
        logger.info(f"  {strategy.name}: Return={results_single['total_return']:.2f}%, Sharpe={results_single['sharpe_ratio']:.2f}")


def test_vwap():
    """VWAP - Institutional Benchmark"""
    logger.info("\n" + "="*80)
    logger.info("5. VWAP STRATEGY")
    logger.info("Used by: All major banks, institutional traders")
    logger.info("="*80)

    client = AlpacaClient(paper=True)

    symbol = 'MSFT'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)

    logger.info(f"\nFetching data for {symbol}...")
    data = client.get_historical_data(symbol, start_date, end_date, timeframe='1Day')

    # VWAP Strategy
    strategy = VWAPStrategy(
        std_multiplier=2.0,
        use_bands=True
    )

    analysis = strategy.analyze(data)

    logger.info(f"\nVWAP Analysis:")
    logger.info(f"  Price: ${analysis['current_price']:.2f}")
    logger.info(f"  VWAP: ${analysis['vwap']:.2f}")
    logger.info(f"  Upper Band: ${analysis['upper_band']:.2f}")
    logger.info(f"  Lower Band: ${analysis['lower_band']:.2f}")
    logger.info(f"  Distance from VWAP: {analysis['distance_from_vwap_pct']:.2f}%")
    logger.info(f"  Position: {analysis['position']}")
    logger.info(f"  Bias: {analysis['bias']}")
    logger.info(f"  Signal: {analysis['signal']}")

    # Backtest
    engine = BacktestEngine(initial_capital=100000)
    results = engine.run(strategy, data, position_size=0.5)

    logger.info(f"\nBacktest Results:")
    logger.info(f"  Total Return: {results['total_return']:.2f}%")
    logger.info(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    logger.info(f"  Number of Trades: {results['num_trades']}")


def test_ichimoku():
    """Ichimoku Cloud - Japanese All-in-One System"""
    logger.info("\n" + "="*80)
    logger.info("6. ICHIMOKU CLOUD STRATEGY")
    logger.info("Comprehensive Japanese trading system - 'One Look Equilibrium Chart'")
    logger.info("="*80)

    client = AlpacaClient(paper=True)

    symbol = 'SPY'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    logger.info(f"\nFetching data for {symbol}...")
    data = client.get_historical_data(symbol, start_date, end_date, timeframe='1Day')

    # Ichimoku Cloud Strategy
    strategy = IchimokuCloudStrategy(
        tenkan_period=9,
        kijun_period=26,
        senkou_span_b_period=52
    )

    analysis = strategy.analyze(data)

    logger.info(f"\nIchimoku Analysis:")
    logger.info(f"  Price: ${analysis['current_price']:.2f}")
    logger.info(f"  Tenkan-sen (Conversion): ${analysis['tenkan_sen']:.2f}")
    logger.info(f"  Kijun-sen (Base): ${analysis['kijun_sen']:.2f}")
    logger.info(f"  Cloud Top: ${analysis['cloud_top']:.2f}")
    logger.info(f"  Cloud Bottom: ${analysis['cloud_bottom']:.2f}")
    logger.info(f"  Cloud Color: {analysis['cloud_color']}")
    logger.info(f"  Price Position: {analysis['price_position']}")
    logger.info(f"  TK Status: {analysis['tk_status']}")
    logger.info(f"  Overall Trend: {analysis['overall_trend']}")
    logger.info(f"  Signal: {analysis['signal']}")

    # Backtest
    engine = BacktestEngine(initial_capital=100000)
    results = engine.run(strategy, data, position_size=1.0)

    logger.info(f"\nBacktest Results:")
    logger.info(f"  Total Return: {results['total_return']:.2f}%")
    logger.info(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    logger.info(f"  Max Drawdown: {results['max_drawdown']:.2f}%")
    logger.info(f"  Number of Trades: {results['num_trades']}")


def main():
    """Run all professional strategy examples"""
    logger.info("PROFESSIONAL TRADING STRATEGIES - INDUSTRY-PROVEN ALGORITHMS")
    logger.info("These strategies are used by the world's top hedge funds and traders\n")

    # Run all tests
    test_mean_reversion()
    test_turtle_trading()
    test_pairs_trading()
    test_multi_strategy()
    test_vwap()
    test_ichimoku()

    logger.info("\n" + "="*80)
    logger.info("ALL PROFESSIONAL STRATEGIES DEMONSTRATED")
    logger.info("="*80)
    logger.info("\nKey Takeaways:")
    logger.info("1. Mean Reversion: Works best in ranging markets")
    logger.info("2. Turtle Trading: Excellent for trending markets")
    logger.info("3. Pairs Trading: Market-neutral, works in any market")
    logger.info("4. Multi-Strategy: Best risk-adjusted returns through diversification")
    logger.info("5. VWAP: Great for institutional-sized positions")
    logger.info("6. Ichimoku: Comprehensive all-in-one system")
    logger.info("\nRecommendation: Use Multi-Strategy to combine the best of all!")


if __name__ == "__main__":
    main()
