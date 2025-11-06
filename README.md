# Autotrader - Automated Trading System

Ein vollständiges automatisiertes Trading-System mit Web-Dashboard, das sowohl Paper-Trading als auch Live-Trading über die Alpaca API unterstützt.

## Features

- **Automatisiertes Trading**: Bot mit konfigurierbaren Strategien
- **Paper Trading**: Teste mit Fake-Geld ohne Risiko
- **Live Trading**: Handel mit echten Assets (Aktien & Krypto)
- **Backtesting**: Teste Strategien auf historischen Daten
- **Risk Management**: Stop-Loss, Take-Profit, Position Sizing
- **Web Dashboard**: Moderne React-Oberfläche mit Echtzeit-Updates
- **Mehrere Strategien**:
  - Moving Average Crossover (SMA/EMA)
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - Einfach erweiterbar für eigene Strategien
- **Parameter Optimization**: Grid Search & Genetic Algorithms
- **Notifications**: Telegram & Email Alerts
- **Advanced Analytics**: 30+ Performance Metrics, Monte Carlo Simulation

## Architektur

```
autotrader/
├── src/                      # Backend (Python)
│   ├── api/                  # Alpaca API Client & FastAPI
│   ├── strategies/           # Trading Strategien
│   ├── backtesting/          # Backtesting Engine
│   ├── trading/              # Trading Engine & Risk Management
│   └── utils/                # Config & Logger
├── frontend/                 # Frontend (React + Vite)
│   └── src/
│       ├── pages/            # Dashboard, Trading, Backtest, Positions
│       └── services/         # API Client
├── config/                   # Konfiguration
└── examples/                 # Beispielskripte

```

## Installation

### 1. Backend Setup (Python)

```bash
# Python dependencies installieren
pip install -r requirements.txt

# Environment Variablen einrichten
cp .env.example .env
# Editiere .env und füge deine Alpaca API Keys ein
```

### 2. Alpaca API Keys

1. Gehe zu [Alpaca](https://alpaca.markets/) und erstelle einen Account
2. Navigiere zu Paper Trading und hole dir die API Keys
3. Füge die Keys in `.env` ein:

```bash
ALPACA_API_KEY=your_paper_api_key_here
ALPACA_SECRET_KEY=your_paper_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
TRADING_MODE=paper
```

### 3. Frontend Setup (React)

```bash
cd frontend
npm install
```

## Verwendung

### Web Dashboard starten

**Terminal 1 - Backend starten:**
```bash
# Im Hauptverzeichnis
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend starten:**
```bash
cd frontend
npm run dev
```

Öffne Browser: `http://localhost:3000`

### Dashboard Features

1. **Dashboard**: Übersicht über Portfolio, Positionen, P&L
2. **Trading Bot**: Bot starten/stoppen, Strategie konfigurieren
3. **Backtest**: Strategien auf historischen Daten testen
4. **Positions**: Offene Positionen anzeigen, Orders platzieren

### Programmatische Verwendung

**Backtest durchführen:**
```bash
python examples/backtest_example.py
```

**Paper Trading starten:**
```bash
python examples/paper_trading_example.py
```

## 🆕 Neue Features (v0.2.0)

### Zusätzliche Strategien

#### MACD Strategy
```python
from src.strategies.macd_strategy import MACDStrategy

strategy = MACDStrategy(
    fast_period=12,
    slow_period=26,
    signal_period=9
)
```

#### Bollinger Bands
```python
from src.strategies.bollinger_bands import BollingerBandsStrategy

strategy = BollingerBandsStrategy(
    period=20,
    num_std=2.0
)
```

### Parameter Optimization

**Grid Search:**
```python
from src.optimization import ParameterOptimizer

optimizer = ParameterOptimizer(strategy_class, data, metric='sharpe_ratio')
param_grid = {
    'short_window': [10, 20, 30],
    'long_window': [40, 50, 60]
}
best_params, results = optimizer.grid_search(param_grid)
```

**Genetic Algorithm:**
```python
from src.optimization import GeneticOptimizer

optimizer = GeneticOptimizer(
    strategy_class, data,
    param_bounds={'fast_period': (5, 20), 'slow_period': (20, 50)},
    generations=20
)
best_params, results = optimizer.optimize()
```

### Telegram Notifications

```python
from src.notifications import NotificationManager, TelegramNotifier

manager = NotificationManager()
telegram = TelegramNotifier(bot_token='YOUR_TOKEN', chat_ids=['YOUR_CHAT_ID'])
manager.add_channel(telegram)

await manager.notify_trade(symbol='SPY', side='buy', quantity=10, price=450.0)
```

### Advanced Analytics

```python
from src.analytics import PerformanceAnalyzer, MonteCarloSimulation

analyzer = PerformanceAnalyzer(trades, equity_curve)
report = analyzer.generate_report()
print(report)

mc = MonteCarloSimulation(returns, n_simulations=1000)
mc_results = mc.run(n_periods=252)
```

### Trailing Stop-Loss

```python
from src.trading.risk_manager import RiskManager

risk_manager = RiskManager(
    trailing_stop_pct=0.03,
    use_trailing_stop=True
)
```

## Strategien

### Moving Average Crossover

Kaufsignal: Kurzfristiger MA kreuzt über langfristigen MA (Golden Cross)
Verkaufssignal: Kurzfristiger MA kreuzt unter langfristigen MA (Death Cross)

```python
from src.strategies.moving_average import MovingAverageCrossover

strategy = MovingAverageCrossover(
    short_window=20,  # 20 Tage
    long_window=50,   # 50 Tage
    ma_type='sma'     # oder 'ema'
)
```

### RSI Strategy

Kaufsignal: RSI kreuzt über Oversold-Level (Standard: 30)
Verkaufssignal: RSI kreuzt unter Overbought-Level (Standard: 70)

```python
from src.strategies.rsi_strategy import RSIStrategy

strategy = RSIStrategy(
    period=14,
    oversold=30,
    overbought=70
)
```

## Eigene Strategie erstellen

```python
from src.strategies.base_strategy import BaseStrategy
import pandas as pd

class MyStrategy(BaseStrategy):
    def __init__(self, param1, param2):
        super().__init__('MyStrategy', {
            'param1': param1,
            'param2': param2
        })
        self.param1 = param1
        self.param2 = param2

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Implementiere deine Logik
        signals = pd.Series(0, index=data.index)

        # Buy signal = 1
        # Sell signal = -1
        # Hold = 0

        return signals
```

## Risk Management

Das System enthält automatisches Risk Management:

- **Position Sizing**: Max % des Portfolios pro Position (Standard: 10%)
- **Stop Loss**: Automatischer Stop bei Verlust (Standard: 5%)
- **Take Profit**: Automatischer Gewinnmitnahme (Standard: 10%)
- **Daily Loss Limit**: Max täglicher Verlust (Standard: 5%)
- **Max Drawdown**: Max Portfolio-Drawdown (Standard: 20%)

Konfigurierbar in `config/config.yaml` oder per Code:

```python
from src.trading.risk_manager import RiskManager

risk_manager = RiskManager(
    max_position_size=0.1,
    stop_loss_pct=0.05,
    take_profit_pct=0.10,
    max_daily_loss=0.05,
    max_drawdown=0.20
)
```

## API Endpunkte

### Account
- `GET /api/account` - Account Info
- `GET /api/positions` - Alle Positionen

### Trading
- `POST /api/orders` - Order platzieren
- `DELETE /api/positions/{symbol}` - Position schließen

### Strategy
- `POST /api/strategies/analyze` - Strategie analysieren

### Backtest
- `POST /api/backtest` - Backtest durchführen

### Bot
- `POST /api/bot/start` - Bot starten
- `POST /api/bot/stop` - Bot stoppen
- `GET /api/bot/status` - Bot Status

### WebSocket
- `ws://localhost:8000/ws` - Echtzeit-Updates

## Konfiguration

Erstelle `config/config.yaml` (siehe `config/config.example.yaml`):

```yaml
alpaca:
  api_key: "your_key"
  secret_key: "your_secret"
  base_url: "https://paper-api.alpaca.markets"

trading:
  mode: "paper"
  symbols:
    - "SPY"
    - "AAPL"
  check_interval: 60

risk:
  max_position_size: 0.1
  stop_loss_pct: 0.05
  take_profit_pct: 0.10
```

## Wichtige Hinweise

⚠️ **PAPER TRADING ZUERST!**
- Teste alle Strategien zuerst im Paper Trading Modus
- Überprüfe Backtesting-Ergebnisse sorgfältig
- Verstehe die Risiken des automatisierten Tradings

⚠️ **Live Trading**
- Nutze nur Kapital, das du dir leisten kannst zu verlieren
- Starte mit kleinen Beträgen
- Überwache den Bot regelmäßig
- Setze angemessene Risk Management Parameter

## Technologie Stack

**Backend:**
- Python 3.9+
- FastAPI
- Alpaca API (alpaca-py)
- Pandas, NumPy
- SQLAlchemy
- WebSockets

**Frontend:**
- React 18
- Vite
- TailwindCSS
- Recharts
- Tanstack Query
- Axios

## Lizenz

Siehe LICENSE Datei

## Disclaimer

Diese Software dient nur zu Bildungszwecken. Trading ist riskant. Der Autor übernimmt keine Haftung für finanzielle Verluste. Nutze auf eigene Gefahr.