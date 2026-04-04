require('dotenv').config();
const express = require('express');
const WebSocket = require('ws');
const crypto = require('crypto');
const http = require('http');
const Anthropic = require('@anthropic-ai/sdk');
const path = require('path');

// ============================================================
// CONFIG
// ============================================================
const CONFIG = {
  tradingMode: process.env.TRADING_MODE || 'testnet',
  symbol: process.env.SYMBOL || 'BTCUSDT',
  maxBalance: parseFloat(process.env.MAX_ACCOUNT_BALANCE) || 100,
  maxRiskPerTrade: 0.10,    // 10% of account per trade
  stopLossPercent: 0.05,     // 5% stop-loss
  maxOpenTrades: 3,
  decisionIntervalMs: 10000, // 10 seconds
  claudeModel: process.env.CLAUDE_MODEL || 'claude-sonnet-4-20250514',
};

const BYBIT_URLS = {
  testnet: {
    rest: 'https://api-testnet.bybit.com',
    ws: 'wss://stream-testnet.bybit.com/v5/public/spot',
  },
  live: {
    rest: 'https://api.bybit.com',
    ws: 'wss://stream.bybit.com/v5/public/spot',
  },
};

const BINANCE_WS = 'wss://stream.binance.com:9443/ws';

// ============================================================
// STATE
// ============================================================
const state = {
  candles: [],           // last 100 1m candles
  orderbook: { bids: [], asks: [] },
  currentPrice: 0,
  indicators: { rsi: null, macd: null, volume: 0 },
  openTrades: [],
  closedTrades: [],
  equity: CONFIG.maxBalance,
  lastDecision: null,
  lastDecisionTime: null,
  isRunning: false,
  logs: [],
  pnl: 0,
};

const sseClients = new Set();

function log(msg) {
  const entry = `[${new Date().toISOString()}] ${msg}`;
  state.logs.push(entry);
  if (state.logs.length > 200) state.logs.shift();
  console.log(entry);
  broadcastSSE({ type: 'log', data: entry });
}

function broadcastSSE(data) {
  const msg = `data: ${JSON.stringify(data)}\n\n`;
  for (const client of sseClients) {
    client.write(msg);
  }
}

// ============================================================
// TECHNICAL INDICATORS
// ============================================================
function calcRSI(closes, period = 14) {
  if (closes.length < period + 1) return null;
  let gains = 0, losses = 0;
  for (let i = closes.length - period; i < closes.length; i++) {
    const diff = closes[i] - closes[i - 1];
    if (diff > 0) gains += diff;
    else losses -= diff;
  }
  const avgGain = gains / period;
  const avgLoss = losses / period;
  if (avgLoss === 0) return 100;
  const rs = avgGain / avgLoss;
  return 100 - (100 / (1 + rs));
}

function calcEMA(data, period) {
  const k = 2 / (period + 1);
  const ema = [data[0]];
  for (let i = 1; i < data.length; i++) {
    ema.push(data[i] * k + ema[i - 1] * (1 - k));
  }
  return ema;
}

function calcMACD(closes) {
  if (closes.length < 35) return null;
  const ema12 = calcEMA(closes, 12);
  const ema26 = calcEMA(closes, 26);
  const macdLine = ema12.map((v, i) => v - ema26[i]);
  const signalLine = calcEMA(macdLine.slice(26), 9);
  const macd = macdLine[macdLine.length - 1];
  const signal = signalLine[signalLine.length - 1];
  return { macd: round(macd, 2), signal: round(signal, 2), histogram: round(macd - signal, 2) };
}

function updateIndicators() {
  const closes = state.candles.map(c => c.close);
  state.indicators.rsi = round(calcRSI(closes), 2);
  state.indicators.macd = calcMACD(closes);
  state.indicators.volume = state.candles.length > 0
    ? round(state.candles[state.candles.length - 1].volume, 2) : 0;
}

function round(v, d = 2) {
  if (v === null || v === undefined) return null;
  return Math.round(v * Math.pow(10, d)) / Math.pow(10, d);
}

// ============================================================
// BINANCE WEBSOCKET (Market Data)
// ============================================================
function connectBinanceWS() {
  const symbol = CONFIG.symbol.toLowerCase();
  const streams = `${symbol}@kline_1m/${symbol}@depth10@100ms/${symbol}@trade`;
  const ws = new WebSocket(`${BINANCE_WS}/${streams}`);

  ws.on('open', () => log('Binance WebSocket connected'));

  ws.on('message', (raw) => {
    try {
      const msg = JSON.parse(raw);

      // Kline (candlestick)
      if (msg.e === 'kline') {
        const k = msg.k;
        const candle = {
          time: k.t,
          open: parseFloat(k.o),
          high: parseFloat(k.h),
          low: parseFloat(k.l),
          close: parseFloat(k.c),
          volume: parseFloat(k.v),
          closed: k.x,
        };
        state.currentPrice = candle.close;

        if (candle.closed) {
          state.candles.push(candle);
          if (state.candles.length > 100) state.candles.shift();
          updateIndicators();
        } else if (state.candles.length > 0) {
          state.candles[state.candles.length - 1] = candle;
          updateIndicators();
        } else {
          state.candles.push(candle);
        }
      }

      // Orderbook
      if (msg.e === 'depthUpdate' || msg.bids) {
        const bids = (msg.b || msg.bids || []).slice(0, 5).map(([p, q]) => ({
          price: parseFloat(p), qty: parseFloat(q),
        }));
        const asks = (msg.a || msg.asks || []).slice(0, 5).map(([p, q]) => ({
          price: parseFloat(p), qty: parseFloat(q),
        }));
        if (bids.length) state.orderbook.bids = bids;
        if (asks.length) state.orderbook.asks = asks;
      }

      // Trade
      if (msg.e === 'trade') {
        state.currentPrice = parseFloat(msg.p);
      }

      checkStopLossTakeProfit();
      broadcastSSE({ type: 'state', data: getPublicState() });
    } catch (e) {
      // ignore parse errors on binary frames
    }
  });

  ws.on('close', () => {
    log('Binance WS disconnected, reconnecting in 5s...');
    setTimeout(connectBinanceWS, 5000);
  });

  ws.on('error', (err) => log(`Binance WS error: ${err.message}`));
}

// ============================================================
// BYBIT ORDER EXECUTION
// ============================================================
function bybitSign(params, secret) {
  const ordered = Object.keys(params).sort().map(k => `${k}=${params[k]}`).join('&');
  return crypto.createHmac('sha256', secret).update(ordered).digest('hex');
}

async function bybitRequest(method, endpoint, params = {}) {
  const base = BYBIT_URLS[CONFIG.tradingMode].rest;
  const timestamp = Date.now().toString();
  const apiKey = process.env.EXCHANGE_API_KEY;
  const secret = process.env.EXCHANGE_SECRET;

  const allParams = { ...params, api_key: apiKey, timestamp };
  allParams.sign = bybitSign(allParams, secret);

  const url = new URL(endpoint, base);

  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };

  if (method === 'GET') {
    Object.entries(allParams).forEach(([k, v]) => url.searchParams.append(k, v));
  } else {
    options.body = JSON.stringify(allParams);
  }

  const resp = await fetch(url.toString(), options);
  const data = await resp.json();

  if (data.retCode !== undefined && data.retCode !== 0) {
    throw new Error(`Bybit API error: ${data.retMsg} (code: ${data.retCode})`);
  }
  return data;
}

async function getAccountBalance() {
  try {
    const data = await bybitRequest('GET', '/v5/account/wallet-balance', {
      accountType: 'UNIFIED',
      coin: 'USDT',
    });
    const coin = data?.result?.list?.[0]?.coin?.[0];
    return coin ? parseFloat(coin.walletBalance) : CONFIG.maxBalance;
  } catch (e) {
    log(`Balance fetch error: ${e.message}`);
    return state.equity;
  }
}

async function placeOrder(side, qty, symbol = CONFIG.symbol) {
  log(`Placing ${side} order: ${qty} ${symbol}`);
  try {
    const result = await bybitRequest('POST', '/v5/order/create', {
      category: 'spot',
      symbol,
      side: side.charAt(0).toUpperCase() + side.slice(1),
      orderType: 'Market',
      qty: qty.toString(),
    });
    log(`Order placed: ${JSON.stringify(result?.result)}`);
    return result;
  } catch (e) {
    log(`Order error: ${e.message}`);
    throw e;
  }
}

// ============================================================
// TRADE MANAGEMENT
// ============================================================
function checkStopLossTakeProfit() {
  if (!state.currentPrice || state.openTrades.length === 0) return;

  for (let i = state.openTrades.length - 1; i >= 0; i--) {
    const trade = state.openTrades[i];

    if (state.currentPrice <= trade.stopLoss) {
      closeTrade(i, 'stop_loss');
    } else if (trade.takeProfit && state.currentPrice >= trade.takeProfit) {
      closeTrade(i, 'take_profit');
    }
  }
}

async function closeTrade(index, reason) {
  const trade = state.openTrades[index];
  if (!trade) return;

  const pnl = (state.currentPrice - trade.entryPrice) * trade.amount / trade.entryPrice;
  trade.exitPrice = state.currentPrice;
  trade.pnl = round(pnl, 4);
  trade.closedAt = new Date().toISOString();
  trade.closeReason = reason;

  state.openTrades.splice(index, 1);
  state.closedTrades.push(trade);
  state.equity += pnl;
  state.pnl += pnl;

  log(`Trade closed (${reason}): PnL ${pnl > 0 ? '+' : ''}${round(pnl, 2)} USDT`);

  // Execute sell on exchange
  try {
    const qtyInBase = trade.amount / state.currentPrice;
    if (qtyInBase > 0.00001) {
      await placeOrder('Sell', round(qtyInBase, 6));
    }
  } catch (e) {
    log(`Close order failed: ${e.message} (manual close may be needed)`);
  }

  broadcastSSE({ type: 'trade_closed', data: trade });
}

async function openTrade(decision) {
  if (state.openTrades.length >= CONFIG.maxOpenTrades) {
    log('Max open trades reached, skipping buy');
    return;
  }

  const maxPerTrade = state.equity * CONFIG.maxRiskPerTrade;
  const amount = Math.min(decision.amount || maxPerTrade, maxPerTrade);

  if (amount < 1) {
    log('Trade amount too small, skipping');
    return;
  }

  const stopLoss = decision.stop_loss || state.currentPrice * (1 - CONFIG.stopLossPercent);
  const takeProfit = decision.take_profit || null;

  const trade = {
    id: Date.now().toString(36),
    symbol: CONFIG.symbol,
    entryPrice: state.currentPrice,
    amount: round(amount, 2),
    stopLoss: round(stopLoss, 2),
    takeProfit: takeProfit ? round(takeProfit, 2) : null,
    openedAt: new Date().toISOString(),
  };

  // Execute buy on exchange
  try {
    const qtyInBase = amount / state.currentPrice;
    await placeOrder('Buy', round(qtyInBase, 6));
    state.openTrades.push(trade);
    state.equity -= amount;
    log(`Trade opened: BUY ${round(amount, 2)} USDT @ ${state.currentPrice} | SL: ${trade.stopLoss} | TP: ${trade.takeProfit || 'none'}`);
    broadcastSSE({ type: 'trade_opened', data: trade });
  } catch (e) {
    log(`Failed to open trade: ${e.message}`);
  }
}

// ============================================================
// CLAUDE AI DECISION ENGINE
// ============================================================
const anthropic = new Anthropic({ apiKey: process.env.CLAUDE_API_KEY });

async function getClaudeDecision() {
  const last20Candles = state.candles.slice(-20).map(c => ({
    time: new Date(c.time).toISOString(),
    o: c.open, h: c.high, l: c.low, c: c.close, v: round(c.volume, 2),
  }));

  const marketData = {
    symbol: CONFIG.symbol,
    currentPrice: state.currentPrice,
    candles_1m_last20: last20Candles,
    orderbook: {
      bestBid: state.orderbook.bids[0] || null,
      bestAsk: state.orderbook.asks[0] || null,
      bidDepth: state.orderbook.bids.slice(0, 5),
      askDepth: state.orderbook.asks.slice(0, 5),
    },
    indicators: state.indicators,
    account: {
      equity: round(state.equity, 2),
      openTrades: state.openTrades.length,
      maxOpenTrades: CONFIG.maxOpenTrades,
      openPositions: state.openTrades.map(t => ({
        entryPrice: t.entryPrice,
        amount: t.amount,
        stopLoss: t.stopLoss,
        takeProfit: t.takeProfit,
        unrealizedPnl: round((state.currentPrice - t.entryPrice) * t.amount / t.entryPrice, 2),
      })),
      totalPnl: round(state.pnl, 2),
    },
    riskRules: {
      maxRiskPerTrade: `${CONFIG.maxRiskPerTrade * 100}% of equity = ${round(state.equity * CONFIG.maxRiskPerTrade, 2)} USDT`,
      stopLoss: `${CONFIG.stopLossPercent * 100}% below entry`,
      maxOpenTrades: CONFIG.maxOpenTrades,
    },
  };

  const systemPrompt = `You are an expert crypto daytrader AI. You analyze real-time market data and make trading decisions.

RULES:
- You manage a small account (max ~100 USDT). Preserve capital above all.
- Max 10% of equity per trade. Max 3 open trades.
- Every BUY must have a stop_loss (max -5% from entry) and ideally a take_profit.
- Only trade when you see a clear edge. HOLD is always a valid and often best choice.
- Consider RSI, MACD, volume, orderbook imbalance, and price action.
- Be conservative. This is real money.

Respond with ONLY valid JSON, no markdown, no explanation:
{ "action": "buy" | "sell" | "hold", "amount": <USDT amount for buy>, "stop_loss": <price>, "take_profit": <price>, "reasoning": "<1 sentence>" }

For "sell": close the most profitable open position.
For "hold": just set amount to 0.`;

  try {
    const response = await anthropic.messages.create({
      model: CONFIG.claudeModel,
      max_tokens: 256,
      system: systemPrompt,
      messages: [{
        role: 'user',
        content: `Current market data:\n${JSON.stringify(marketData, null, 2)}\n\nWhat is your trading decision?`,
      }],
    });

    const text = response.content[0].text.trim();
    // Parse JSON, handling possible markdown wrapping
    const jsonStr = text.replace(/```json?\n?/g, '').replace(/```/g, '').trim();
    const decision = JSON.parse(jsonStr);
    log(`Claude decision: ${decision.action.toUpperCase()} | ${decision.reasoning}`);
    return decision;
  } catch (e) {
    log(`Claude API error: ${e.message}`);
    return { action: 'hold', amount: 0, reasoning: 'API error, defaulting to hold' };
  }
}

// ============================================================
// MAIN TRADING LOOP
// ============================================================
let decisionInterval = null;

async function tradingLoop() {
  if (!state.isRunning) return;
  if (state.candles.length < 20) {
    log('Waiting for enough candle data...');
    return;
  }

  try {
    const decision = await getClaudeDecision();
    state.lastDecision = decision;
    state.lastDecisionTime = new Date().toISOString();

    if (decision.action === 'buy') {
      await openTrade(decision);
    } else if (decision.action === 'sell' && state.openTrades.length > 0) {
      // Close most profitable trade
      let bestIdx = 0;
      let bestPnl = -Infinity;
      state.openTrades.forEach((t, i) => {
        const pnl = (state.currentPrice - t.entryPrice) * t.amount / t.entryPrice;
        if (pnl > bestPnl) { bestPnl = pnl; bestIdx = i; }
      });
      await closeTrade(bestIdx, 'ai_sell');
    }

    broadcastSSE({ type: 'decision', data: { decision, time: state.lastDecisionTime } });
  } catch (e) {
    log(`Trading loop error: ${e.message}`);
  }
}

function startTrading() {
  if (state.isRunning) return;
  state.isRunning = true;
  decisionInterval = setInterval(tradingLoop, CONFIG.decisionIntervalMs);
  log(`Trading started in ${CONFIG.tradingMode.toUpperCase()} mode | Balance: ${state.equity} USDT`);
}

function stopTrading() {
  state.isRunning = false;
  if (decisionInterval) clearInterval(decisionInterval);
  decisionInterval = null;
  log('Trading stopped');
}

// ============================================================
// EXPRESS SERVER + SSE
// ============================================================
const app = express();
const server = http.createServer(app);

app.use(express.json());
app.use(express.static(path.join(__dirname)));

function getPublicState() {
  return {
    currentPrice: state.currentPrice,
    equity: round(state.equity, 2),
    pnl: round(state.pnl, 2),
    openTrades: state.openTrades,
    closedTrades: state.closedTrades.slice(-20),
    indicators: state.indicators,
    lastDecision: state.lastDecision,
    lastDecisionTime: state.lastDecisionTime,
    isRunning: state.isRunning,
    tradingMode: CONFIG.tradingMode,
    symbol: CONFIG.symbol,
    logs: state.logs.slice(-50),
  };
}

// SSE endpoint
app.get('/events', (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    Connection: 'keep-alive',
  });
  sseClients.add(res);
  res.write(`data: ${JSON.stringify({ type: 'state', data: getPublicState() })}\n\n`);
  req.on('close', () => sseClients.delete(res));
});

// API endpoints
app.get('/api/state', (req, res) => res.json(getPublicState()));

app.post('/api/start', (req, res) => {
  startTrading();
  res.json({ ok: true, message: 'Trading started' });
});

app.post('/api/stop', (req, res) => {
  stopTrading();
  res.json({ ok: true, message: 'Trading stopped' });
});

app.post('/api/close-all', async (req, res) => {
  for (let i = state.openTrades.length - 1; i >= 0; i--) {
    await closeTrade(i, 'manual_close');
  }
  res.json({ ok: true, message: 'All trades closed' });
});

// Serve dashboard
app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'dashboard.html')));

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  log(`Server running on http://localhost:${PORT}`);
  log(`Trading mode: ${CONFIG.tradingMode.toUpperCase()}`);
  log(`Symbol: ${CONFIG.symbol} | Max balance: ${CONFIG.maxBalance} USDT`);
  connectBinanceWS();
});
