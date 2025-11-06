# 🖥️ Web-Dashboard Anleitung

## 📦 Installation & Start

### Schritt 1: Backend starten

Terminal 1:
```bash
# Im Hauptverzeichnis des Projekts
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Du siehst dann:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Schritt 2: Frontend starten

Terminal 2:
```bash
cd frontend
npm install  # Nur beim ersten Mal
npm run dev
```

Du siehst dann:
```
VITE v5.0.8  ready in 500 ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

### Schritt 3: Browser öffnen

Gehe zu: **http://localhost:3000**

---

## 📱 Dashboard-Seiten Übersicht

### 1. 📊 **Dashboard** (Startseite)

**URL**: `http://localhost:3000/`

#### Was du siehst:
- **Portfolio Stats (4 Karten oben)**:
  - 💰 **Portfolio Value**: Gesamtwert deines Portfolios
  - 📈 **Buying Power**: Verfügbare Kaufkraft
  - 💵 **Cash**: Verfügbares Bargeld
  - 📊 **Total P&L**: Gewinn/Verlust (grün=Gewinn, rot=Verlust)

- **Bot Status Alert** (wenn Bot läuft):
  - 🟢 Grüne Box: Bot ist aktiv
  - Zeigt Strategie und Symbole an

- **Open Positions Tabelle**:
  - Alle deine offenen Positionen
  - Spalten:
    - Symbol
    - Menge (Quantity)
    - Durchschnittlicher Kaufpreis
    - Aktueller Preis
    - Marktwert
    - Unrealisierter Gewinn/Verlust ($)
    - Unrealisierter Gewinn/Verlust (%)

#### Features:
- ✅ Echtzeit-Updates alle 30 Sekunden
- ✅ WebSocket-Verbindung für Live-Daten
- ✅ Farbcodierung (Grün=Gewinn, Rot=Verlust)

---

### 2. 🤖 **Trading Bot** (Automatisches Trading)

**URL**: `http://localhost:3000/trading`

#### Bot Status Sektion:

**Wenn Bot gestoppt ist**:
- 🟢 **Grüner "Start Bot" Button** zum Starten
- Konfigurationsformular ist sichtbar

**Wenn Bot läuft**:
- 🔴 **Roter "Stop Bot" Button** zum Stoppen
- Live-Status anzeigen:
  - Current Value (Aktueller Portfoliowert)
  - P&L (Gewinn/Verlust in $)
  - P&L % (Gewinn/Verlust in %)

#### Konfiguration:

1. **Strategy auswählen**:
   - Moving Average Crossover
   - RSI Strategy
   - **MACD Strategy** (neu!)
   - **Bollinger Bands** (neu!)

2. **Symbols eingeben**:
   - Komma-getrennte Liste: `SPY,AAPL,MSFT`
   - Für Crypto: `BTC/USD,ETH/USD`

3. **Check Interval**:
   - Wie oft der Bot checkt (in Sekunden)
   - Standard: 60 Sekunden

4. **Notifications** (Checkbox):
   - ✅ Aktivieren für Telegram/Email Benachrichtigungen

5. **Strategy Parameters** (je nach Strategie):

   **Moving Average**:
   - Short Window: 20
   - Long Window: 50
   - MA Type: SMA oder EMA

   **RSI**:
   - Period: 14
   - Oversold: 30
   - Overbought: 70

   **MACD** (neu!):
   - Fast Period: 12
   - Slow Period: 26
   - Signal Period: 9
   - Threshold: 0

   **Bollinger Bands** (neu!):
   - Period: 20
   - Standard Deviations: 2.0
   - MA Type: SMA oder EMA

#### Workflow:
1. Strategie auswählen
2. Parameter einstellen
3. Symbole eingeben
4. "Start Bot" klicken
5. Bot tradet automatisch!
6. "Stop Bot" zum Beenden

---

### 3. 📈 **Backtest** (Strategien testen)

**URL**: `http://localhost:3000/backtest`

#### So funktioniert's:

1. **Configuration Bereich**:
   - **Symbol**: z.B. SPY, AAPL, BTC/USD
   - **Strategy**: Wähle eine der 4 Strategien
   - **Start Date**: Startdatum (YYYY-MM-DD)
   - **End Date**: Enddatum
   - **Initial Capital**: Startkapital (z.B. 100000)

2. **Strategy Parameters**:
   - Gleiche Parameter wie beim Trading Bot
   - Teste verschiedene Werte!

3. **"Run Backtest" Button klicken**

4. **Results Anzeige**:
   - **Performance Karten** (4 Boxen):
     - Total Return (%)
     - Sharpe Ratio
     - Max Drawdown (%)
     - Win Rate (%)

   - **Details** (3 Boxen):
     - Final Value ($)
     - Number of Trades
     - Win/Loss Ratio

#### Tipps:
- 💡 Teste mindestens 1 Jahr Daten
- 💡 Vergleiche verschiedene Strategien
- 💡 Achte auf Max Drawdown (sollte < 20% sein)
- 💡 Sharpe Ratio > 1.0 ist gut

---

### 4. 💼 **Positions** (Manuelle Orders)

**URL**: `http://localhost:3000/positions`

#### New Order Formular:

Klicke auf **"Place Order"** Button oben rechts

**Formular Felder**:
1. **Symbol**: z.B. AAPL
2. **Quantity**: Anzahl Aktien (z.B. 10)
3. **Side**: Buy oder Sell
4. **Order Type**:
   - Market (sofort zum Marktpreis)
   - Limit (nur zu deinem Preis)
5. **Limit Price** (nur bei Limit Orders):
   - Dein Wunschpreis

**Buttons**:
- 🟢 "Place Order": Order aufgeben
- ⚪ "Cancel": Abbrechen

#### Open Positions Tabelle:

Zeigt alle offenen Positionen mit:
- Symbol
- Quantity
- Avg Entry (Kaufpreis)
- Current Price
- Market Value
- P&L ($)
- P&L (%)
- ❌ **Actions**: Klick zum Schließen

---

## 🎯 Praktische Workflows

### Workflow 1: Ersten Trade machen

1. Gehe zu **Positions**
2. Klicke "Place Order"
3. Eingabe:
   - Symbol: SPY
   - Quantity: 10
   - Side: Buy
   - Order Type: Market
4. Klicke "Place Order"
5. Gehe zu **Dashboard** → Siehst du Position!

### Workflow 2: Trading Bot starten

1. Gehe zu **Trading Bot**
2. Wähle Strategie: z.B. "MACD Strategy"
3. Symbole: `SPY,AAPL`
4. Parameter lassen (Standard ist gut)
5. Notifications aktivieren ✅
6. Klicke "Start Bot"
7. Bot tradet jetzt automatisch!

### Workflow 3: Backtest durchführen

1. Gehe zu **Backtest**
2. Eingabe:
   - Symbol: AAPL
   - Strategy: Bollinger Bands
   - Start: 2023-01-01
   - End: 2024-01-01
   - Capital: 100000
3. Parameter: Standard lassen
4. Klicke "Run Backtest"
5. Warte 5-10 Sekunden
6. Siehe Ergebnisse!

### Workflow 4: Beste Strategie finden

1. **Backtest** mit Moving Average → Notiere Return
2. **Backtest** mit RSI → Notiere Return
3. **Backtest** mit MACD → Notiere Return
4. **Backtest** mit Bollinger → Notiere Return
5. Nimm Strategie mit höchstem Sharpe Ratio
6. Starte **Trading Bot** mit dieser Strategie!

---

## ⚙️ Advanced Features

### Echtzeit-Updates

Das Dashboard nutzt **WebSocket** für Live-Updates:
- ✅ Portfolio-Werte aktualisieren automatisch
- ✅ Positionen werden live geupdatet
- ✅ Bot-Status zeigt Echtzeit-Performance

### Notifications Setup

Für Telegram-Benachrichtigungen:

1. **Bot erstellen**:
   - Gehe zu Telegram
   - Suche @BotFather
   - `/newbot` eingeben
   - Namen wählen
   - Token kopieren

2. **Chat ID holen**:
   - Suche @userinfobot
   - `/start` eingeben
   - Kopiere deine Chat ID

3. **.env konfigurieren**:
```bash
TELEGRAM_BOT_TOKEN=dein_token_hier
TELEGRAM_CHAT_ID=deine_chat_id_hier
```

4. **Backend neu starten**

5. Jetzt bekommst du Telegram-Nachrichten bei:
   - Trade Execution
   - Buy/Sell Signals
   - Bot Start/Stop
   - Risk Alerts
   - Performance Updates

---

## 🐛 Troubleshooting

### Problem: Dashboard lädt nicht

**Lösung**:
1. Check Backend läuft: `http://localhost:8000/health`
2. Check Frontend läuft: Siehe Terminal für Fehler
3. Browser-Cache leeren (Strg+Shift+R)

### Problem: "No data available"

**Lösung**:
1. Check Alpaca API Keys in `.env`
2. Check Internetverbindung
3. Check Symbol existiert (z.B. nicht "XYZ")

### Problem: Bot startet nicht

**Lösung**:
1. Check Backend Logs in Terminal 1
2. Check alle Parameter ausgefüllt
3. Check mindestens 1 Symbol eingegeben

### Problem: Orders werden nicht ausgeführt

**Lösung**:
1. Check Paper Trading Mode aktiv
2. Check genug Buying Power
3. Check Markt ist offen (US Markt: Mo-Fr 9:30-16:00 ET)

---

## 🎨 UI-Elemente erklärt

### Farben:
- 🟢 **Grün**: Positiv, Gewinn, Bullish
- 🔴 **Rot**: Negativ, Verlust, Bearish
- 🔵 **Blau**: Neutral, Info, Actions
- 🟡 **Gelb**: Warning, Achtung

### Icons:
- 📊 TrendingUp: Dashboard, Positives
- 📉 TrendingDown: Negatives
- 💰 DollarSign: Geld, Value
- 🎯 Activity: Trading, Bot
- 📈 BarChart: Backtest, Analytics
- 🛒 ShoppingCart: Orders
- ✓ Check: Erfolg
- ✗ X: Schließen, Fehler

### Status-Punkte:
- 🟢 Grüner Punkt = Aktiv/Running
- 🔴 Roter Punkt = Inaktiv/Stopped
- 🟡 Gelber Punkt = Warning

---

## 💡 Best Practices

1. **Immer erst Backtesten!**
   - Teste Strategie auf historischen Daten
   - Mindestens 6-12 Monate
   - Achte auf Max Drawdown

2. **Klein anfangen**
   - Starte mit 1-2 Symbolen
   - Nutze Paper Trading
   - Überwache regelmäßig

3. **Diversifikation**
   - Nicht alles in ein Symbol
   - Verschiedene Sektoren
   - Mix aus Strategien

4. **Risk Management beachten**
   - Stop-Loss nutzen
   - Max Position Size einhalten
   - Daily Loss Limits setzen

5. **Notifications aktivieren**
   - Wirst sofort informiert
   - Kannst schnell reagieren
   - Keine Überraschungen

---

## 📚 Weitere Ressourcen

- `README.md` - Allgemeine Übersicht
- `FEATURES.md` - Alle Features im Detail
- `CHANGELOG.md` - Was ist neu?
- `examples/` - Code-Beispiele
- API Docs: `http://localhost:8000/docs` (wenn Backend läuft)

---

Viel Erfolg beim Trading! 🚀📈
