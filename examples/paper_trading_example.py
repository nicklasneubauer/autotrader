"""
Paper Trading Example
Run the trading bot in paper trading mode
"""

import os
from dotenv import load_dotenv

from src.api.alpaca_client import AlpacaClient
from src.strategies.moving_average import MovingAverageCrossover
from src.trading.trader import Trader
from src.trading.risk_manager import RiskManager
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger(level='INFO')


def run_paper_trading():
    """Run paper trading bot"""
    logger.info("Starting paper trading bot...")

    # Initialize Alpaca client (paper trading)
    client = AlpacaClient(paper=True)

    # Check account
    account = client.get_account()
    logger.info(f"Account Status:")
    logger.info(f"  Portfolio Value: ${account['portfolio_value']:,.2f}")
    logger.info(f"  Buying Power: ${account['buying_power']:,.2f}")
    logger.info(f"  Cash: ${account['cash']:,.2f}")

    # Create strategy
    strategy = MovingAverageCrossover(
        short_window=20,
        long_window=50,
        ma_type='sma'
    )
    logger.info(f"Strategy: {strategy}")

    # Create risk manager
    risk_manager = RiskManager(
        max_position_size=0.1,      # 10% per position
        max_portfolio_risk=0.02,    # 2% risk per trade
        stop_loss_pct=0.05,         # 5% stop loss
        take_profit_pct=0.10,       # 10% take profit
        max_daily_loss=0.05,        # 5% max daily loss
        max_drawdown=0.20           # 20% max drawdown
    )
    logger.info("Risk Manager configured")

    # Create trader
    trader = Trader(
        api_client=client,
        strategy=strategy,
        risk_manager=risk_manager,
        symbols=['SPY', 'AAPL', 'MSFT'],  # Trade multiple symbols
        check_interval=60  # Check every 60 seconds
    )

    logger.info("="*50)
    logger.info("Paper Trading Bot Started")
    logger.info("Press Ctrl+C to stop")
    logger.info("="*50)

    # Start trading
    try:
        trader.start()
    except KeyboardInterrupt:
        logger.info("\nStopping trading bot...")
        trader.stop()
        logger.info("Trading bot stopped")

        # Print final status
        status = trader.get_status()
        logger.info("\n" + "="*50)
        logger.info("FINAL STATUS")
        logger.info("="*50)
        logger.info(f"Initial Portfolio Value: ${status['initial_portfolio_value']:,.2f}")
        logger.info(f"Current Portfolio Value: ${status['current_portfolio_value']:,.2f}")
        logger.info(f"P&L: ${status['pnl']:,.2f} ({status['pnl_pct']:.2f}%)")
        logger.info(f"Open Positions: {len(status['positions'])}")
        logger.info("="*50)


if __name__ == "__main__":
    run_paper_trading()
