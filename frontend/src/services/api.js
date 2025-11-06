import axios from 'axios'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Account endpoints
export const getAccount = () => api.get('/account')
export const getPositions = () => api.get('/positions')
export const getPosition = (symbol) => api.get(`/positions/${symbol}`)

// Trading endpoints
export const placeOrder = (orderData) => api.post('/orders', orderData)
export const closePosition = (symbol) => api.delete(`/positions/${symbol}`)

// Strategy endpoints
export const analyzeStrategy = (symbol, strategyType, parameters) =>
  api.post('/strategies/analyze', null, {
    params: { symbol, strategy_type: strategyType, parameters: JSON.stringify(parameters) },
  })

// Backtest endpoints
export const runBacktest = (backtestData) => api.post('/backtest', backtestData)

// Bot endpoints
export const startBot = (botConfig) => api.post('/bot/start', botConfig)
export const stopBot = () => api.post('/bot/stop')
export const getBotStatus = () => api.get('/bot/status')

// Data endpoints
export const getHistoricalData = (dataRequest) =>
  api.post('/data/historical', dataRequest)

// Analytics endpoints
export const getAnalytics = (timeframe = 'all') => api.get(`/analytics?timeframe=${timeframe}`)
export const getTrades = (strategyFilter = 'all') => api.get(`/trades?strategy=${strategyFilter}`)
export const getPortfolioHistory = (period = '7d') => api.get(`/portfolio/history?period=${period}`)
export const getRecentActivity = (maxItems = 10) => api.get(`/activity/recent?max=${maxItems}`)

// Strategy comparison endpoint
export const compareStrategies = (comparisonData) => api.post('/strategies/compare', comparisonData)

// Optimization endpoint
export const optimizeStrategy = (optimizationData) => api.post('/strategies/optimize', optimizationData)

// Watchlist endpoints
export const getWatchlist = () => api.get('/watchlist')
export const addToWatchlist = (symbol) => api.post('/watchlist', { symbol })
export const removeFromWatchlist = (symbol) => api.delete(`/watchlist/${symbol}`)
export const getQuote = (symbol) => api.get(`/quotes/${symbol}`)

// WebSocket connection
export const createWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws`
  return new WebSocket(wsUrl)
}

export default api
