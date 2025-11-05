import React, { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { runBacktest } from '../services/api'
import { BarChart3, TrendingUp } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

function Backtest() {
  const [symbol, setSymbol] = useState('SPY')
  const [strategyType, setStrategyType] = useState('moving_average')
  const [startDate, setStartDate] = useState('2023-01-01')
  const [endDate, setEndDate] = useState('2024-01-01')
  const [initialCapital, setInitialCapital] = useState(100000)
  const [parameters, setParameters] = useState({
    short_window: 20,
    long_window: 50,
    ma_type: 'sma',
  })
  const [results, setResults] = useState(null)

  const backtestMutation = useMutation({
    mutationFn: runBacktest,
    onSuccess: (response) => {
      setResults(response.data)
    },
  })

  const handleRun = () => {
    backtestMutation.mutate({
      strategy_type: strategyType,
      parameters,
      symbol,
      start_date: startDate,
      end_date: endDate,
      initial_capital: initialCapital,
      position_size: 1.0,
    })
  }

  const handleStrategyChange = (type) => {
    setStrategyType(type)
    if (type === 'moving_average') {
      setParameters({
        short_window: 20,
        long_window: 50,
        ma_type: 'sma',
      })
    } else if (type === 'rsi') {
      setParameters({
        period: 14,
        oversold: 30,
        overbought: 70,
      })
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-white">Backtest</h2>
        <p className="text-gray-400 mt-1">Test your strategies on historical data</p>
      </div>

      {/* Configuration */}
      <div className="bg-slate-800 shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4 flex items-center">
          <BarChart3 className="mr-2" size={20} />
          Configuration
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
              onChange={(e) => handleStrategyChange(e.target.value)}
              className="mt-1 block w-full pl-3 pr-10 py-2 bg-slate-700 border-slate-600 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
            >
              <option value="moving_average">Moving Average Crossover</option>
              <option value="rsi">RSI Strategy</option>
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
            <label className="block text-sm font-medium text-gray-300">Initial Capital</label>
            <input
              type="number"
              value={initialCapital}
              onChange={(e) => setInitialCapital(parseFloat(e.target.value))}
              className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Strategy Parameters */}
        <div className="mt-6 border-t border-slate-700 pt-4">
          <h4 className="text-sm font-medium text-gray-300 mb-3">Strategy Parameters</h4>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {strategyType === 'moving_average' ? (
              <>
                <div>
                  <label className="block text-sm text-gray-400">Short Window</label>
                  <input
                    type="number"
                    value={parameters.short_window}
                    onChange={(e) =>
                      setParameters({ ...parameters, short_window: parseInt(e.target.value) })
                    }
                    className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400">Long Window</label>
                  <input
                    type="number"
                    value={parameters.long_window}
                    onChange={(e) =>
                      setParameters({ ...parameters, long_window: parseInt(e.target.value) })
                    }
                    className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400">MA Type</label>
                  <select
                    value={parameters.ma_type}
                    onChange={(e) => setParameters({ ...parameters, ma_type: e.target.value })}
                    className="mt-1 block w-full pl-3 pr-10 py-2 bg-slate-700 border-slate-600 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
                  >
                    <option value="sma">SMA</option>
                    <option value="ema">EMA</option>
                  </select>
                </div>
              </>
            ) : (
              <>
                <div>
                  <label className="block text-sm text-gray-400">Period</label>
                  <input
                    type="number"
                    value={parameters.period}
                    onChange={(e) =>
                      setParameters({ ...parameters, period: parseInt(e.target.value) })
                    }
                    className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400">Oversold</label>
                  <input
                    type="number"
                    value={parameters.oversold}
                    onChange={(e) =>
                      setParameters({ ...parameters, oversold: parseFloat(e.target.value) })
                    }
                    className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400">Overbought</label>
                  <input
                    type="number"
                    value={parameters.overbought}
                    onChange={(e) =>
                      setParameters({ ...parameters, overbought: parseFloat(e.target.value) })
                    }
                    className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </>
            )}
          </div>
        </div>

        <div className="mt-6">
          <button
            onClick={handleRun}
            disabled={backtestMutation.isPending}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <TrendingUp className="mr-2" size={16} />
            {backtestMutation.isPending ? 'Running...' : 'Run Backtest'}
          </button>
        </div>
      </div>

      {/* Results */}
      {results && (
        <div className="bg-slate-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Results</h3>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
            <ResultCard
              title="Total Return"
              value={`${results.total_return.toFixed(2)}%`}
              color={results.total_return >= 0 ? 'green' : 'red'}
            />
            <ResultCard
              title="Sharpe Ratio"
              value={results.sharpe_ratio.toFixed(2)}
              color="blue"
            />
            <ResultCard
              title="Max Drawdown"
              value={`${results.max_drawdown.toFixed(2)}%`}
              color="red"
            />
            <ResultCard title="Win Rate" value={`${results.win_rate.toFixed(2)}%`} color="green" />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 mb-6">
            <div className="bg-slate-700 rounded-lg p-4">
              <div className="text-sm text-gray-400">Final Value</div>
              <div className="mt-1 text-lg font-semibold text-white">
                ${results.final_value.toFixed(2)}
              </div>
            </div>
            <div className="bg-slate-700 rounded-lg p-4">
              <div className="text-sm text-gray-400">Number of Trades</div>
              <div className="mt-1 text-lg font-semibold text-white">{results.num_trades}</div>
            </div>
            <div className="bg-slate-700 rounded-lg p-4">
              <div className="text-sm text-gray-400">Win/Loss</div>
              <div className="mt-1 text-lg font-semibold text-white">
                {results.winning_trades}/{results.losing_trades}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ResultCard({ title, value, color }) {
  const colorClasses = {
    green: 'text-green-400',
    red: 'text-red-400',
    blue: 'text-blue-400',
  }

  return (
    <div className="bg-slate-700 rounded-lg p-4">
      <div className="text-sm text-gray-400">{title}</div>
      <div className={`mt-1 text-2xl font-semibold ${colorClasses[color]}`}>{value}</div>
    </div>
  )
}

export default Backtest
