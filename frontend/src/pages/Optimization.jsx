import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Settings, Zap, TrendingUp } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts'
import { optimizeStrategy } from '../services/api'

function Optimization() {
  const [symbol, setSymbol] = useState('SPY')
  const [startDate, setStartDate] = useState('2023-01-01')
  const [endDate, setEndDate] = useState('2024-01-01')
  const [strategyType, setStrategyType] = useState('moving_average')
  const [optimizationMethod, setOptimizationMethod] = useState('grid_search')
  const [optimizationMetric, setOptimizationMetric] = useState('sharpe_ratio')
  const [results, setResults] = useState(null)

  const optimizeMutation = useMutation({
    mutationFn: optimizeStrategy,
    onSuccess: (response) => {
      setResults(response.data)
    },
  })

  const handleOptimize = () => {
    optimizeMutation.mutate({
      symbol,
      start_date: startDate,
      end_date: endDate,
      strategy_type: strategyType,
      method: optimizationMethod,
      metric: optimizationMetric,
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-white">Strategy Optimization</h2>
        <p className="text-gray-400 mt-1">Find optimal parameters for your trading strategies</p>
      </div>

      {/* Configuration */}
      <div className="bg-slate-800 shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4 flex items-center">
          <Settings className="mr-2" size={20} />
          Optimization Configuration
        </h3>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
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
            <label className="block text-sm font-medium text-gray-300">Strategy</label>
            <select
              value={strategyType}
              onChange={(e) => setStrategyType(e.target.value)}
              className="mt-1 block w-full pl-3 pr-10 py-2 bg-slate-700 border-slate-600 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
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
            <label className="block text-sm font-medium text-gray-300">Optimization Method</label>
            <select
              value={optimizationMethod}
              onChange={(e) => setOptimizationMethod(e.target.value)}
              className="mt-1 block w-full pl-3 pr-10 py-2 bg-slate-700 border-slate-600 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
            >
              <option value="grid_search">Grid Search (Exhaustive)</option>
              <option value="genetic">Genetic Algorithm (Fast)</option>
              <option value="random">Random Search</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300">Optimization Metric</label>
            <select
              value={optimizationMetric}
              onChange={(e) => setOptimizationMetric(e.target.value)}
              className="mt-1 block w-full pl-3 pr-10 py-2 bg-slate-700 border-slate-600 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
            >
              <option value="sharpe_ratio">Sharpe Ratio</option>
              <option value="total_return">Total Return</option>
              <option value="sortino_ratio">Sortino Ratio</option>
              <option value="calmar_ratio">Calmar Ratio</option>
              <option value="profit_factor">Profit Factor</option>
            </select>
          </div>
        </div>

        <div className="mt-6">
          <button
            onClick={handleOptimize}
            disabled={optimizeMutation.isPending}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <Zap className="mr-2" size={16} />
            {optimizeMutation.isPending ? 'Optimizing...' : 'Start Optimization'}
          </button>
        </div>

        {optimizeMutation.isPending && (
          <div className="mt-4 bg-blue-900 bg-opacity-20 border border-blue-700 rounded-lg p-4">
            <div className="flex items-center">
              <Zap className="text-blue-400 mr-2 animate-pulse" size={20} />
              <span className="text-blue-200">
                Running optimization... This may take a few minutes depending on the method and parameter space.
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      {results && (
        <>
          {/* Best Parameters */}
          <div className="bg-slate-800 shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-white mb-4 flex items-center">
              <TrendingUp className="mr-2" size={20} />
              Optimal Parameters Found
            </h3>
            <div className="bg-green-900 bg-opacity-20 border border-green-700 rounded-lg p-4 mb-4">
              <div className="text-sm text-green-200">
                Best {optimizationMetric.replace('_', ' ')}: <span className="font-bold">{results.best_score?.toFixed(4)}</span>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {Object.entries(results.best_parameters || {}).map(([key, value]) => (
                <div key={key} className="bg-slate-700 rounded-lg p-4">
                  <div className="text-sm text-gray-400 mb-1">{key.replace('_', ' ').toUpperCase()}</div>
                  <div className="text-xl font-semibold text-white">{value}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="bg-slate-800 shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-white mb-4">Performance with Optimal Parameters</h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <MetricCard title="Total Return" value={`${results.performance?.total_return?.toFixed(2) || 0}%`} />
              <MetricCard title="Sharpe Ratio" value={results.performance?.sharpe_ratio?.toFixed(2) || '0.00'} />
              <MetricCard title="Max Drawdown" value={`${results.performance?.max_drawdown?.toFixed(2) || 0}%`} />
              <MetricCard title="Win Rate" value={`${results.performance?.win_rate?.toFixed(2) || 0}%`} />
            </div>
          </div>

          {/* Parameter Space Exploration */}
          {results.all_results && results.all_results.length > 0 && (
            <div className="bg-slate-800 shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-white mb-4">Parameter Space Exploration</h3>
              <ResponsiveContainer width="100%" height={400}>
                <ScatterChart>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis
                    dataKey="iteration"
                    name="Iteration"
                    stroke="#9CA3AF"
                  />
                  <YAxis
                    dataKey="score"
                    name="Score"
                    stroke="#9CA3AF"
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                    labelStyle={{ color: '#e5e7eb' }}
                    cursor={{ strokeDasharray: '3 3' }}
                  />
                  <Scatter
                    name="Parameter Tests"
                    data={results.all_results.map((r, i) => ({ iteration: i, score: r.score }))}
                    fill="#3b82f6"
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Top 10 Parameter Combinations */}
          {results.top_combinations && results.top_combinations.length > 0 && (
            <div className="bg-slate-800 shadow rounded-lg">
              <div className="px-4 py-5 sm:px-6 border-b border-slate-700">
                <h3 className="text-lg leading-6 font-medium text-white">Top 10 Parameter Combinations</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-700">
                  <thead className="bg-slate-700">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Rank</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Score</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Parameters</th>
                    </tr>
                  </thead>
                  <tbody className="bg-slate-800 divide-y divide-slate-700">
                    {results.top_combinations.map((combo, idx) => (
                      <tr key={idx} className={idx === 0 ? 'bg-green-900 bg-opacity-20' : ''}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                          #{idx + 1}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-green-400 font-medium">
                          {combo.score?.toFixed(4)}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-300">
                          {JSON.stringify(combo.parameters)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function MetricCard({ title, value }) {
  return (
    <div className="bg-slate-700 rounded-lg p-4">
      <div className="text-sm text-gray-400">{title}</div>
      <div className="mt-1 text-2xl font-semibold text-white">{value}</div>
    </div>
  )
}

export default Optimization
