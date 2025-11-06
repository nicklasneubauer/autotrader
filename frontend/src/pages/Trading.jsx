import React, { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { startBot, stopBot, getBotStatus } from '../services/api'
import { Play, Square, Activity } from 'lucide-react'

function Trading() {
  const queryClient = useQueryClient()
  const [strategyType, setStrategyType] = useState('moving_average')
  const [symbols, setSymbols] = useState('SPY,AAPL')
  const [checkInterval, setCheckInterval] = useState(60)
  const [parameters, setParameters] = useState({
    short_window: 20,
    long_window: 50,
    ma_type: 'sma',
  })
  const [notifications, setNotifications] = useState(true)

  const { data: botStatus } = useQuery({
    queryKey: ['botStatus'],
    queryFn: async () => {
      const response = await getBotStatus()
      return response.data
    },
    refetchInterval: 5000,
  })

  const startMutation = useMutation({
    mutationFn: startBot,
    onSuccess: () => {
      queryClient.invalidateQueries(['botStatus'])
    },
  })

  const stopMutation = useMutation({
    mutationFn: stopBot,
    onSuccess: () => {
      queryClient.invalidateQueries(['botStatus'])
    },
  })

  const handleStart = () => {
    const symbolList = symbols.split(',').map((s) => s.trim())
    startMutation.mutate({
      strategy_type: strategyType,
      parameters,
      symbols: symbolList,
      check_interval: checkInterval,
    })
  }

  const handleStop = () => {
    stopMutation.mutate()
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
    } else if (type === 'macd') {
      setParameters({
        fast_period: 12,
        slow_period: 26,
        signal_period: 9,
        threshold: 0,
      })
    } else if (type === 'bollinger_bands') {
      setParameters({
        period: 20,
        num_std: 2.0,
        ma_type: 'sma',
      })
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-white">Trading Bot</h2>
        <p className="text-gray-400 mt-1">Configure and control automated trading</p>
      </div>

      {/* Bot Status */}
      <div className="bg-slate-800 shadow rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-white flex items-center">
              <Activity className="mr-2" size={20} />
              Bot Status
            </h3>
            <p className="mt-2 text-sm text-gray-400">
              {botStatus?.is_running ? (
                <>
                  <span className="inline-block w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                  Running - {botStatus.strategy} on {botStatus.symbols?.join(', ')}
                </>
              ) : (
                <>
                  <span className="inline-block w-2 h-2 bg-gray-400 rounded-full mr-2"></span>
                  Stopped
                </>
              )}
            </p>
          </div>
          <div>
            {botStatus?.is_running ? (
              <button
                onClick={handleStop}
                disabled={stopMutation.isPending}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
              >
                <Square className="mr-2" size={16} />
                Stop Bot
              </button>
            ) : (
              <button
                onClick={handleStart}
                disabled={startMutation.isPending}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
              >
                <Play className="mr-2" size={16} />
                Start Bot
              </button>
            )}
          </div>
        </div>

        {botStatus?.is_running && (
          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="bg-slate-700 rounded-lg p-4">
              <div className="text-sm text-gray-400">Current Value</div>
              <div className="mt-1 text-2xl font-semibold text-white">
                ${botStatus.current_portfolio_value?.toFixed(2)}
              </div>
            </div>
            <div className="bg-slate-700 rounded-lg p-4">
              <div className="text-sm text-gray-400">P&L</div>
              <div
                className={`mt-1 text-2xl font-semibold ${
                  botStatus.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                }`}
              >
                ${botStatus.pnl?.toFixed(2)}
              </div>
            </div>
            <div className="bg-slate-700 rounded-lg p-4">
              <div className="text-sm text-gray-400">P&L %</div>
              <div
                className={`mt-1 text-2xl font-semibold ${
                  botStatus.pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {botStatus.pnl_pct?.toFixed(2)}%
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Configuration */}
      {!botStatus?.is_running && (
        <div className="bg-slate-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Configuration</h3>

          <div className="space-y-4">
            {/* Strategy Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-300">Strategy</label>
              <select
                value={strategyType}
                onChange={(e) => handleStrategyChange(e.target.value)}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base bg-slate-700 border-slate-600 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
              >
                <option value="moving_average">Moving Average Crossover</option>
                <option value="rsi">RSI Strategy</option>
                <option value="macd">MACD Strategy</option>
                <option value="bollinger_bands">Bollinger Bands</option>
              </select>
            </div>

            {/* Symbols */}
            <div>
              <label className="block text-sm font-medium text-gray-300">
                Symbols (comma-separated)
              </label>
              <input
                type="text"
                value={symbols}
                onChange={(e) => setSymbols(e.target.value)}
                className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="SPY,AAPL,MSFT"
              />
            </div>

            {/* Check Interval */}
            <div>
              <label className="block text-sm font-medium text-gray-300">
                Check Interval (seconds)
              </label>
              <input
                type="number"
                value={checkInterval}
                onChange={(e) => setCheckInterval(parseInt(e.target.value))}
                className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Notifications Toggle */}
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={notifications}
                  onChange={(e) => setNotifications(e.target.checked)}
                  className="rounded bg-slate-700 border-slate-600 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-300">Enable Notifications (Telegram/Email)</span>
              </label>
            </div>

            {/* Strategy Parameters */}
            <div className="border-t border-slate-700 pt-4">
              <h4 className="text-sm font-medium text-gray-300 mb-3">Strategy Parameters</h4>

              {strategyType === 'moving_average' ? (
                <div className="space-y-3">
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
                      <option value="sma">SMA (Simple)</option>
                      <option value="ema">EMA (Exponential)</option>
                    </select>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
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
                </div>
              ) : strategyType === 'macd' ? (
                <>
                  <div>
                    <label className="block text-sm text-gray-400">Fast Period</label>
                    <input
                      type="number"
                      value={parameters.fast_period}
                      onChange={(e) =>
                        setParameters({ ...parameters, fast_period: parseInt(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400">Slow Period</label>
                    <input
                      type="number"
                      value={parameters.slow_period}
                      onChange={(e) =>
                        setParameters({ ...parameters, slow_period: parseInt(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400">Signal Period</label>
                    <input
                      type="number"
                      value={parameters.signal_period}
                      onChange={(e) =>
                        setParameters({ ...parameters, signal_period: parseInt(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </>
              ) : strategyType === 'bollinger_bands' ? (
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
                    <label className="block text-sm text-gray-400">Standard Deviations</label>
                    <input
                      type="number"
                      step="0.1"
                      value={parameters.num_std}
                      onChange={(e) =>
                        setParameters({ ...parameters, num_std: parseFloat(e.target.value) })
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
                      <option value="sma">SMA (Simple)</option>
                      <option value="ema">EMA (Exponential)</option>
                    </select>
                  </div>
                </>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Trading
