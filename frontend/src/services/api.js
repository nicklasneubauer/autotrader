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

// WebSocket connection
export const createWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws`
  return new WebSocket(wsUrl)
}

export default api
