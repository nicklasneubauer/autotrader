"""
Configuration Management
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration manager"""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration

        Args:
            config_file: Path to YAML config file
        """
        # Load environment variables
        load_dotenv()

        self.config_data = {}

        # Load from file if provided
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                self.config_data = yaml.safe_load(f) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value

        Args:
            key: Configuration key (supports dot notation, e.g., 'alpaca.api_key')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        # Try environment variable first (uppercase with underscores)
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value

        # Try config file
        keys = key.split('.')
        value = self.config_data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    def get_alpaca_config(self) -> Dict[str, str]:
        """Get Alpaca API configuration"""
        return {
            'api_key': self.get('alpaca.api_key') or self.get('ALPACA_API_KEY'),
            'secret_key': self.get('alpaca.secret_key') or self.get('ALPACA_SECRET_KEY'),
            'base_url': self.get('alpaca.base_url') or self.get('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'),
            'paper': self.get('trading.mode', 'paper') == 'paper'
        }

    def get_strategy_config(self, strategy_name: str) -> Dict[str, Any]:
        """Get strategy configuration"""
        return self.config_data.get('strategies', {}).get(strategy_name, {})

    def get_risk_config(self) -> Dict[str, float]:
        """Get risk management configuration"""
        risk_defaults = {
            'max_position_size': 0.1,
            'max_portfolio_risk': 0.02,
            'stop_loss_pct': 0.05,
            'take_profit_pct': 0.10,
            'max_daily_loss': 0.05,
            'max_drawdown': 0.20
        }

        risk_config = self.config_data.get('risk', {})
        return {**risk_defaults, **risk_config}

    def get_trading_config(self) -> Dict[str, Any]:
        """Get trading configuration"""
        return self.config_data.get('trading', {
            'symbols': ['SPY'],
            'check_interval': 60,
            'mode': 'paper'
        })

    @classmethod
    def from_file(cls, config_file: str) -> 'Config':
        """Create config from file"""
        return cls(config_file)

    @classmethod
    def from_env(cls) -> 'Config':
        """Create config from environment variables only"""
        return cls()
