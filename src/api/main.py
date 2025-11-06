"""
FastAPI Main Application
"""

from fastapi import FastAPI, WebSocket, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime, timedelta

from .database import init_db, get_db, Trade, BacktestResult
from .schemas import (
    AccountInfo, Position, OrderRequest, OrderResponse,
    StrategyCreate, StrategyAnalysis, BacktestRequest, BacktestResponse,
    BotStartRequest, BotStatus, HistoricalDataRequest
)
from ..api.alpaca_client import AlpacaClient
from ..strategies.moving_average import MovingAverageCrossover
from ..strategies.rsi_strategy import RSIStrategy
from ..strategies.macd_strategy import MACDStrategy
from ..strategies.bollinger_bands import BollingerBandsStrategy
from ..strategies.mean_reversion import MeanReversionStrategy
from ..strategies.turtle_trading import TurtleTradingStrategy
from ..strategies.pairs_trading import PairsTradingStrategy
from ..strategies.vwap_strategy import VWAPStrategy
from ..strategies.ichimoku_cloud import IchimokuCloudStrategy
from ..strategies.multi_strategy import MultiStrategyPortfolio
from ..backtesting.backtest_engine import BacktestEngine
from ..trading.trader import Trader
from ..trading.risk_manager import RiskManager
from ..utils.config import Config
from ..utils.logger import setup_logger

# Initialize app
app = FastAPI(
    title="Autotrader API",
    description="Automated Trading System API",
    version="0.1.0"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Global variables
config = Config.from_env()
logger = setup_logger(level=config.get('LOG_LEVEL', 'INFO'))
active_trader: Trader = None
alpaca_client: AlpacaClient = None

# WebSocket connections
active_connections: List[WebSocket] = []


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global alpaca_client
    try:
        alpaca_config = config.get_alpaca_config()
        alpaca_client = AlpacaClient(
            api_key=alpaca_config['api_key'],
            secret_key=alpaca_config['secret_key'],
            base_url=alpaca_config['base_url'],
            paper=alpaca_config['paper']
        )
        logger.info("Autotrader API started")
    except Exception as e:
        logger.error(f"Failed to initialize Alpaca client: {e}")


# ==================== Account Endpoints ====================

@app.get("/api/account", response_model=AccountInfo)
async def get_account():
    """Get account information"""
    try:
        account = alpaca_client.get_account()
        return account
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/positions", response_model=List[Position])
async def get_positions():
    """Get all positions"""
    try:
        positions = alpaca_client.get_positions()
        return positions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/positions/{symbol}", response_model=Position)
async def get_position(symbol: str):
    """Get position for symbol"""
    try:
        position = alpaca_client.get_position(symbol)
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")
        return position
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Trading Endpoints ====================

@app.post("/api/orders", response_model=OrderResponse)
async def place_order(order: OrderRequest, db: Session = Depends(get_db)):
    """Place an order"""
    try:
        if order.order_type == 'market':
            result = alpaca_client.place_market_order(
                symbol=order.symbol,
                qty=order.qty,
                side=order.side,
                time_in_force=order.time_in_force
            )
        elif order.order_type == 'limit':
            if not order.limit_price:
                raise HTTPException(status_code=400, detail="Limit price required for limit orders")
            result = alpaca_client.place_limit_order(
                symbol=order.symbol,
                qty=order.qty,
                side=order.side,
                limit_price=order.limit_price,
                time_in_force=order.time_in_force
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid order type")

        if not result:
            raise HTTPException(status_code=500, detail="Failed to place order")

        # Save to database
        trade = Trade(
            symbol=order.symbol,
            side=order.side,
            quantity=order.qty,
            price=result.get('filled_avg_price', 0),
            order_id=result['id'],
            status=result['status']
        )
        db.add(trade)
        db.commit()

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/positions/{symbol}")
async def close_position(symbol: str):
    """Close a position"""
    try:
        success = alpaca_client.close_position(symbol)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to close position")
        return {"message": f"Position closed for {symbol}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Strategy Endpoints ====================

@app.post("/api/strategies/analyze")
async def analyze_strategy(
    symbol: str,
    strategy_type: str,
    parameters: Dict[str, Any]
) -> StrategyAnalysis:
    """Analyze strategy for a symbol"""
    try:
        # Get historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=100)

        data = alpaca_client.get_historical_data(
            symbol=symbol,
            start=start_date,
            end=end_date,
            timeframe='1Day'
        )

        if data.empty:
            raise HTTPException(status_code=404, detail="No data available")

        # Create strategy
        if strategy_type == 'moving_average':
            strategy = MovingAverageCrossover(**parameters)
        elif strategy_type == 'rsi':
            strategy = RSIStrategy(**parameters)
        else:
            raise HTTPException(status_code=400, detail="Invalid strategy type")

        # Analyze
        analysis = strategy.analyze(data)
        return analysis

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Backtesting Endpoints ====================

@app.post("/api/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest, db: Session = Depends(get_db)):
    """Run backtest"""
    try:
        # Get historical data
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date)

        data = alpaca_client.get_historical_data(
            symbol=request.symbol,
            start=start_date,
            end=end_date,
            timeframe='1Day'
        )

        if data.empty:
            raise HTTPException(status_code=404, detail="No data available")

        # Create strategy
        strategy_map = {
            'moving_average': MovingAverageCrossover,
            'rsi': RSIStrategy,
            'macd': MACDStrategy,
            'bollinger_bands': BollingerBandsStrategy,
            'mean_reversion': MeanReversionStrategy,
            'turtle_trading': TurtleTradingStrategy,
            'pairs_trading': PairsTradingStrategy,
            'vwap': VWAPStrategy,
            'ichimoku': IchimokuCloudStrategy,
            'multi_strategy': MultiStrategyPortfolio,
        }

        strategy_class = strategy_map.get(request.strategy_type)
        if not strategy_class:
            raise HTTPException(status_code=400, detail=f"Invalid strategy type: {request.strategy_type}")

        strategy = strategy_class(**request.parameters)

        # Run backtest
        engine = BacktestEngine(initial_capital=request.initial_capital)
        results = engine.run(strategy, data, position_size=request.position_size)

        # Save results
        backtest_result = BacktestResult(
            strategy=request.strategy_type,
            symbol=request.symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=results['initial_capital'],
            final_value=results['final_value'],
            total_return=results['total_return'],
            sharpe_ratio=results['sharpe_ratio'],
            max_drawdown=results['max_drawdown'],
            num_trades=results['num_trades'],
            win_rate=results['win_rate'],
            parameters=json.dumps(request.parameters)
        )
        db.add(backtest_result)
        db.commit()

        return results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Trading Bot Endpoints ====================

@app.post("/api/bot/start")
async def start_bot(request: BotStartRequest, background_tasks: BackgroundTasks):
    """Start trading bot"""
    global active_trader

    try:
        if active_trader and active_trader.is_running:
            raise HTTPException(status_code=400, detail="Bot is already running")

        # Create strategy
        strategy_map = {
            'moving_average': MovingAverageCrossover,
            'rsi': RSIStrategy,
            'macd': MACDStrategy,
            'bollinger_bands': BollingerBandsStrategy,
            'mean_reversion': MeanReversionStrategy,
            'turtle_trading': TurtleTradingStrategy,
            'pairs_trading': PairsTradingStrategy,
            'vwap': VWAPStrategy,
            'ichimoku': IchimokuCloudStrategy,
            'multi_strategy': MultiStrategyPortfolio,
        }

        strategy_class = strategy_map.get(request.strategy_type)
        if not strategy_class:
            raise HTTPException(status_code=400, detail=f"Invalid strategy type: {request.strategy_type}")

        strategy = strategy_class(**request.parameters)

        # Create risk manager
        risk_config = config.get_risk_config()
        risk_manager = RiskManager(**risk_config)

        # Create trader
        active_trader = Trader(
            api_client=alpaca_client,
            strategy=strategy,
            risk_manager=risk_manager,
            symbols=request.symbols,
            check_interval=request.check_interval
        )

        # Start in background
        background_tasks.add_task(active_trader.start)

        return {"message": "Trading bot started", "strategy": request.strategy_type}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bot/stop")
async def stop_bot():
    """Stop trading bot"""
    global active_trader

    if not active_trader:
        raise HTTPException(status_code=400, detail="No bot is running")

    active_trader.stop()
    return {"message": "Trading bot stopped"}


@app.get("/api/bot/status", response_model=BotStatus)
async def get_bot_status():
    """Get bot status"""
    if not active_trader:
        return {
            "is_running": False,
            "strategy": None,
            "symbols": [],
            "current_portfolio_value": 0,
            "initial_portfolio_value": 0,
            "pnl": 0,
            "pnl_pct": 0
        }

    status = active_trader.get_status()
    return status


# ==================== Data Endpoints ====================

@app.post("/api/data/historical")
async def get_historical_data(request: HistoricalDataRequest):
    """Get historical data"""
    try:
        start_date = datetime.fromisoformat(request.start_date)
        end_date = datetime.fromisoformat(request.end_date) if request.end_date else datetime.now()

        data = alpaca_client.get_historical_data(
            symbol=request.symbol,
            start=start_date,
            end=end_date,
            timeframe=request.timeframe,
            asset_type=request.asset_type
        )

        if data.empty:
            raise HTTPException(status_code=404, detail="No data available")

        # Convert to JSON-serializable format
        data_dict = data.reset_index().to_dict('records')
        return {"symbol": request.symbol, "data": data_dict}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WebSocket Endpoint ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            # Send updates every 5 seconds
            await asyncio.sleep(5)

            if active_trader and active_trader.is_running:
                status = active_trader.get_status()
                await websocket.send_json({
                    "type": "status_update",
                    "data": status
                })

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket)


# ==================== Analytics Endpoints ====================

@app.get("/api/analytics")
async def get_analytics(timeframe: str = 'all', db: Session = Depends(get_db)):
    """Get performance analytics"""
    try:
        # Get trades from database
        trades = db.query(Trade).all()

        # Calculate mock analytics (in production, use PerformanceAnalyzer)
        return {
            "returns": {
                "total_return": 15.5,
                "cagr": 12.3,
                "avg_monthly": 1.2,
                "best_month": 5.8
            },
            "risk": {
                "sharpe_ratio": 1.45,
                "sortino_ratio": 1.82,
                "calmar_ratio": 0.95,
                "max_drawdown": -12.5,
                "volatility": 18.2,
                "var_95": -2.5,
                "cvar_95": -3.2,
                "beta": 0.92
            },
            "trades": {
                "total_trades": len(trades),
                "win_rate": 58.5,
                "profit_factor": 1.65,
                "avg_win_loss_ratio": 1.35,
                "avg_trade_pnl": 125.50,
                "best_trade": 850.00,
                "worst_trade": -320.00
            },
            "time": {
                "monthly_returns": []
            },
            "equity_curve": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trades")
async def get_trades(strategy: str = 'all', db: Session = Depends(get_db)):
    """Get trade history"""
    try:
        query = db.query(Trade)
        if strategy != 'all':
            query = query.filter(Trade.strategy == strategy)

        trades = query.order_by(Trade.timestamp.desc()).limit(100).all()
        return [
            {
                "timestamp": trade.timestamp.isoformat(),
                "symbol": trade.symbol,
                "side": trade.side,
                "quantity": trade.quantity,
                "price": trade.price,
                "pnl": trade.pnl,
                "strategy": trade.strategy
            }
            for trade in trades
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio/history")
async def get_portfolio_history(period: str = '7d'):
    """Get portfolio history"""
    try:
        # Mock data - in production, retrieve from database
        now = datetime.now()
        history = []
        for i in range(7):
            date = now - timedelta(days=6-i)
            history.append({
                "timestamp": date.isoformat(),
                "portfolio_value": 100000 + (i * 500),
                "pnl": i * 500
            })
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/activity/recent")
async def get_recent_activity(max: int = 10):
    """Get recent activity feed"""
    try:
        # Mock data - in production, retrieve from activity log
        activities = [
            {
                "type": "trade_buy",
                "title": "Bought 10 shares of AAPL",
                "message": "Executed at $175.50",
                "timestamp": datetime.now().isoformat(),
                "details": {"symbol": "AAPL", "qty": 10, "price": 175.50}
            }
        ]
        return activities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Strategy Comparison ====================

@app.post("/api/strategies/compare")
async def compare_strategies(request: Dict[str, Any]):
    """Compare multiple strategies"""
    try:
        symbol = request['symbol']
        strategies = request['strategies']
        start_date = datetime.fromisoformat(request['start_date'])
        end_date = datetime.fromisoformat(request['end_date'])

        # Get historical data
        data = alpaca_client.get_historical_data(
            symbol=symbol,
            start=start_date,
            end=end_date,
            timeframe='1Day'
        )

        if data.empty:
            raise HTTPException(status_code=404, detail="No data available")

        results = []
        best_index = 0
        best_sharpe = -999

        for idx, strategy_config in enumerate(strategies):
            strategy_type = strategy_config['type']
            params = strategy_config['params']

            # Create strategy
            strategy_map = {
                'moving_average': MovingAverageCrossover,
                'rsi': RSIStrategy,
                'macd': MACDStrategy,
                'bollinger_bands': BollingerBandsStrategy,
                'mean_reversion': MeanReversionStrategy,
                'turtle_trading': TurtleTradingStrategy,
                'vwap': VWAPStrategy,
                'ichimoku': IchimokuCloudStrategy,
            }

            strategy_class = strategy_map.get(strategy_type)
            if not strategy_class:
                continue

            strategy = strategy_class(**params)

            # Run backtest
            engine = BacktestEngine(initial_capital=request.get('initial_capital', 100000))
            result = engine.run(strategy, data)

            result['strategy_name'] = f"{strategy_type.title().replace('_', ' ')}"
            result['equity_curve'] = []
            results.append(result)

            if result['sharpe_ratio'] > best_sharpe:
                best_sharpe = result['sharpe_ratio']
                best_index = idx

        return {
            "results": results,
            "best_strategy_index": best_index
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Optimization ====================

@app.post("/api/strategies/optimize")
async def optimize_strategy(request: Dict[str, Any]):
    """Optimize strategy parameters"""
    try:
        # Mock optimization results
        return {
            "best_parameters": {
                "short_window": 18,
                "long_window": 45
            },
            "best_score": 1.65,
            "performance": {
                "total_return": 18.5,
                "sharpe_ratio": 1.65,
                "max_drawdown": -10.2,
                "win_rate": 62.0
            },
            "all_results": [],
            "top_combinations": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Watchlist Endpoints ====================

# Global watchlist storage (in production, use database)
watchlist_data = []

@app.get("/api/watchlist")
async def get_watchlist():
    """Get watchlist"""
    try:
        # Return watchlist with live quotes
        result = []
        for symbol in watchlist_data:
            try:
                quote = alpaca_client.get_latest_quote(symbol)
                result.append({
                    "symbol": symbol,
                    "price": quote.get('price', 0),
                    "change": quote.get('change', 0),
                    "change_percent": quote.get('change_percent', 0),
                    "volume": quote.get('volume', 0),
                    "high": quote.get('high', 0),
                    "low": quote.get('low', 0)
                })
            except:
                # Fallback to mock data
                result.append({
                    "symbol": symbol,
                    "price": 100.0,
                    "change": 0.5,
                    "change_percent": 0.5,
                    "volume": 1000000,
                    "high": 101.0,
                    "low": 99.0
                })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/watchlist")
async def add_to_watchlist(data: Dict[str, str]):
    """Add symbol to watchlist"""
    try:
        symbol = data['symbol'].upper()
        if symbol not in watchlist_data:
            watchlist_data.append(symbol)
        return {"message": f"Added {symbol} to watchlist"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str):
    """Remove symbol from watchlist"""
    try:
        symbol = symbol.upper()
        if symbol in watchlist_data:
            watchlist_data.remove(symbol)
        return {"message": f"Removed {symbol} from watchlist"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quotes/{symbol}")
async def get_quote(symbol: str):
    """Get quote for symbol"""
    try:
        quote = alpaca_client.get_latest_quote(symbol)
        return quote
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
