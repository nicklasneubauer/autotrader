"""
Pydantic schemas for API
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# Account schemas
class AccountInfo(BaseModel):
    equity: float
    cash: float
    buying_power: float
    portfolio_value: float


# Position schemas
class Position(BaseModel):
    symbol: str
    qty: float
    side: str
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_plpc: float
    current_price: float
    avg_entry_price: float


# Order schemas
class OrderRequest(BaseModel):
    symbol: str
    qty: float
    side: str
    order_type: str = 'market'
    limit_price: Optional[float] = None
    time_in_force: str = 'day'


class OrderResponse(BaseModel):
    id: str
    symbol: str
    qty: float
    side: str
    type: str
    status: str


# Strategy schemas
class StrategyCreate(BaseModel):
    name: str
    strategy_type: str
    parameters: Dict[str, Any]


class StrategyResponse(BaseModel):
    id: int
    name: str
    strategy_type: str
    parameters: Dict[str, Any]
    is_active: bool


class StrategyAnalysis(BaseModel):
    strategy: str
    signal: str
    signal_value: int
    parameters: Dict[str, Any]
    timestamp: Optional[datetime] = None
    current_price: Optional[float] = None


# Backtest schemas
class BacktestRequest(BaseModel):
    strategy_type: str
    parameters: Dict[str, Any]
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float = 100000
    position_size: float = 1.0


class BacktestResponse(BaseModel):
    initial_capital: float
    final_value: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    num_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float


# Trading bot schemas
class BotStartRequest(BaseModel):
    strategy_type: str
    parameters: Dict[str, Any]
    symbols: List[str]
    check_interval: int = 60


class BotStatus(BaseModel):
    is_running: bool
    strategy: str
    symbols: List[str]
    current_portfolio_value: float
    initial_portfolio_value: float
    pnl: float
    pnl_pct: float


# Historical data schemas
class HistoricalDataRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: Optional[str] = None
    timeframe: str = '1Day'
    asset_type: str = 'stock'
