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
        if request.strategy_type == 'moving_average':
            strategy = MovingAverageCrossover(**request.parameters)
        elif request.strategy_type == 'rsi':
            strategy = RSIStrategy(**request.parameters)
        else:
            raise HTTPException(status_code=400, detail="Invalid strategy type")

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
        if request.strategy_type == 'moving_average':
            strategy = MovingAverageCrossover(**request.parameters)
        elif request.strategy_type == 'rsi':
            strategy = RSIStrategy(**request.parameters)
        else:
            raise HTTPException(status_code=400, detail="Invalid strategy type")

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


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
