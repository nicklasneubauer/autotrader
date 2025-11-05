"""
Database setup and models
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database URL
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./autotrader.db')

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class Trade(Base):
    """Trade records"""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    strategy = Column(String)
    side = Column(String)  # buy or sell
    quantity = Column(Float)
    price = Column(Float)
    order_id = Column(String, unique=True)
    status = Column(String)  # open, filled, cancelled
    timestamp = Column(DateTime, default=datetime.utcnow)
    pnl = Column(Float, nullable=True)


class BacktestResult(Base):
    """Backtest results"""
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, index=True)
    strategy = Column(String)
    symbol = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    initial_capital = Column(Float)
    final_value = Column(Float)
    total_return = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    num_trades = Column(Integer)
    win_rate = Column(Float)
    parameters = Column(Text)  # JSON string
    timestamp = Column(DateTime, default=datetime.utcnow)


class StrategyConfig(Base):
    """Strategy configurations"""
    __tablename__ = "strategy_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    strategy_type = Column(String)
    parameters = Column(Text)  # JSON string
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    """Initialize database"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
