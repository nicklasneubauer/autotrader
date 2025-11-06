import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { BarChart3, TrendingUp, Plus, X } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'
import { compareStrategies } from '../services/api'

function StrategyComparison() {
  const [symbol, setSymbol] = useState('SPY')
  const [startDate, setStartDate] = useState('2023-01-01')
  const [endDate, setEndDate] = useState('2024-01-01')
  const [initialCapital, setInitialCapital] = useState(100000)
  const [strategies, setStrategies] = useState([
    { type: 'moving_average', params: { short_window: 20, long_window: 50, ma_type: 'sma' } },
  ])
  const [results, setResults] = useState(null)

  const comparisonMutation = useMutation({
    mutationFn: compareStrategies,
    onSuccess: (response) => {
      setResults(response.data)
    },
  })

  const handleAddStrategy = () => {
    setStrategies([
      ...strategies,
      { type: 'rsi', params: { period: 14, oversold: 30, overbought: 70 } },
    ])
  }

  const handleRemoveStrategy = (index) => {
    setStrategies(strategies.filter((_, i) => i !== index))
  }

  const handleStrategyTypeChange = (index, type) => {
    const newStrategies = [...strategies]
    newStrategies[index].type = type

    // Set default parameters based on strategy type
    const defaultParams = {
      moving_average: { short_window: 20, long_window: 50, ma_type: 'sma' },
      rsi: { period: 14, oversold: 30, overbought: 70 },
      macd: { fast_period: 12, slow_period: 26, signal_period: 9 },
      bollinger_bands: { period: 20, num_std: 2.0, ma_type: 'sma' },
      mean_reversion: { lookback_period: 20, entry_threshold: 2.0, exit_threshold: 0.5 },
      turtle_trading: { entry_period: 20, exit_period: 10, atr_period: 20 },
      vwap: { std_multiplier: 2.0, lookback_period: 0, use_bands: true },
      ichimoku: { tenkan_period: 9, kijun_period: 26, senkou_span_b_period: 52 },
    }

    newStrategies[index].params = defaultParams[type] || {}
    setStrategies(newStrategies)
  }

  const handleRunComparison = () => {
    comparisonMutation.mutate({
      symbol,
      start_date: startDate,
      end_date: endDate,
      initial_capital: initialCapital,
      strategies,
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-white">Strategy Comparison</h2>
        <p className="text-gray-400 mt-1">Compare multiple strategies side-by-side</p>
      </div>

      {/* Configuration */}
      <div className="bg-slate-800 shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4 flex items-center">
          <BarChart3 className="mr-2" size={20} />
          Configuration
        </h3>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-300">Symbol</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300">Initial Capital</label>
            <input
              type="number"
              value={initialCapital}
              onChange={(e) => setInitialCapital(parseFloat(e.target.value))}
              className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Strategies */}
        <div className="border-t border-slate-700 pt-4">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-medium text-gray-300">Strategies to Compare</h4>
            <button
              onClick={handleAddStrategy}
              disabled={strategies.length >= 6}
              className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
            >
              <Plus className="mr-1" size={16} />
              Add Strategy
            </button>
          </div>

          <div className="space-y-4">
            {strategies.map((strategy, index) => (
              <div key={index} className="bg-slate-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h5 className="text-md font-medium text-white">Strategy {index + 1}</h5>
                  {strategies.length > 1 && (
                    <button
                      onClick={() => handleRemoveStrategy(index)}
                      className="text-red-400 hover:text-red-300"
                    >
                      <X size={20} />
                    </button>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300">Strategy Type</label>
                  <select
                    value={strategy.type}
                    onChange={(e) => handleStrategyTypeChange(index, e.target.value)}
                    className="mt-1 block w-full pl-3 pr-10 py-2 bg-slate-600 border-slate-500 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
                  >
                    <optgroup label="Basic Strategies">
                      <option value="moving_average">Moving Average Crossover</option>
                      <option value="rsi">RSI Strategy</option>
                      <option value="macd">MACD Strategy</option>
                      <option value="bollinger_bands">Bollinger Bands</option>
                    </optgroup>
                    <optgroup label="Professional Strategies">
                      <option value="mean_reversion">Mean Reversion</option>
                      <option value="turtle_trading">Turtle Trading</option>
                      <option value="vwap">VWAP Strategy</option>
                      <option value="ichimoku">Ichimoku Cloud</option>
                    </optgroup>
                  </select>
                </div>

                <div className="text-xs text-gray-400 mt-2">
                  Parameters: {JSON.stringify(strategy.params)}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-6">
          <button
            onClick={handleRunComparison}
            disabled={comparisonMutation.isPending || strategies.length === 0}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <TrendingUp className="mr-2" size={16} />
            {comparisonMutation.isPending ? 'Running...' : 'Run Comparison'}
          </button>
        </div>
      </div>

      {/* Results */}
      {results && (
        <>
          {/* Comparison Table */}
          <div className="bg-slate-800 shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-white mb-4">Comparison Results</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-700">
                <thead className="bg-slate-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Strategy</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Total Return</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Sharpe Ratio</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Max Drawdown</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Win Rate</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Total Trades</th>
                  </tr>
                </thead>
                <tbody className="bg-slate-800 divide-y divide-slate-700">
                  {results.results?.map((result, idx) => (
                    <tr key={idx} className={idx === results.best_strategy_index ? 'bg-green-900 bg-opacity-20' : ''}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                        {result.strategy_name}
                        {idx === results.best_strategy_index && (
                          <span className="ml-2 text-xs bg-green-600 text-white px-2 py-1 rounded">BEST</span>
                        )}
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${result.total_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {result.total_return?.toFixed(2)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {result.sharpe_ratio?.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-red-400">
                        {result.max_drawdown?.toFixed(2)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {result.win_rate?.toFixed(2)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                        {result.total_trades}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Performance Chart */}
          <div className="bg-slate-800 shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-white mb-4">Equity Curves Comparison</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                  labelStyle={{ color: '#e5e7eb' }}
                />
                <Legend />
                {results.results?.map((result, idx) => (
                  <Line
                    key={idx}
                    type="monotone"
                    data={result.equity_curve}
                    dataKey="value"
                    stroke={['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'][idx]}
                    name={result.strategy_name}
                    strokeWidth={2}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Metrics Comparison Charts */}
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="bg-slate-800 shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-white mb-4">Total Return Comparison</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={results.results}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="strategy_name" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                    labelStyle={{ color: '#e5e7eb' }}
                  />
                  <Bar dataKey="total_return" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-slate-800 shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-white mb-4">Sharpe Ratio Comparison</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={results.results}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="strategy_name" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                    labelStyle={{ color: '#e5e7eb' }}
                  />
                  <Bar dataKey="sharpe_ratio" fill="#10b981" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default StrategyComparison
