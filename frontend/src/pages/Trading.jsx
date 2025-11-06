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
    } else if (type === 'mean_reversion') {
      setParameters({
        lookback_period: 20,
        entry_threshold: 2.0,
        exit_threshold: 0.5,
        use_zscore: true,
      })
    } else if (type === 'turtle_trading') {
      setParameters({
        entry_period: 20,
        exit_period: 10,
        atr_period: 20,
        use_system_2: false,
      })
    } else if (type === 'pairs_trading') {
      setParameters({
        lookback_period: 20,
        entry_threshold: 2.0,
        exit_threshold: 0.5,
        hedge_ratio_period: 60,
      })
    } else if (type === 'vwap') {
      setParameters({
        std_multiplier: 2.0,
        lookback_period: 0,
        use_bands: true,
      })
    } else if (type === 'ichimoku') {
      setParameters({
        tenkan_period: 9,
        kijun_period: 26,
        senkou_span_b_period: 52,
      })
    } else if (type === 'multi_strategy') {
      setParameters({
        strategies: ['moving_average', 'rsi', 'macd'],
        weights: [0.4, 0.3, 0.3],
        voting_method: 'weighted',
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
                <optgroup label="Basic Strategies">
                  <option value="moving_average">Moving Average Crossover</option>
                  <option value="rsi">RSI Strategy</option>
                  <option value="macd">MACD Strategy</option>
                  <option value="bollinger_bands">Bollinger Bands</option>
                </optgroup>
                <optgroup label="Professional Strategies">
                  <option value="mean_reversion">Mean Reversion (Renaissance Tech)</option>
                  <option value="turtle_trading">Turtle Trading System</option>
                  <option value="pairs_trading">Pairs Trading (Stat Arb)</option>
                  <option value="vwap">VWAP Strategy (Institutional)</option>
                  <option value="ichimoku">Ichimoku Cloud</option>
                  <option value="multi_strategy">Multi-Strategy Portfolio</option>
                </optgroup>
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

              {strategyType === 'moving_average' && (
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
              )}

              {strategyType === 'rsi' && (
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
              )}

              {strategyType === 'macd' && (
                <div className="space-y-3">
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
                </div>
              )}

              {strategyType === 'bollinger_bands' && (
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
                </div>
              )}

              {strategyType === 'mean_reversion' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-gray-400">Lookback Period</label>
                    <input
                      type="number"
                      value={parameters.lookback_period}
                      onChange={(e) =>
                        setParameters({ ...parameters, lookback_period: parseInt(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400">Entry Threshold (Std Dev)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={parameters.entry_threshold}
                      onChange={(e) =>
                        setParameters({ ...parameters, entry_threshold: parseFloat(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400">Exit Threshold (Std Dev)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={parameters.exit_threshold}
                      onChange={(e) =>
                        setParameters({ ...parameters, exit_threshold: parseFloat(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={parameters.use_zscore}
                        onChange={(e) => setParameters({ ...parameters, use_zscore: e.target.checked })}
                        className="rounded bg-slate-700 border-slate-600 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-400">Use Z-Score</span>
                    </label>
                  </div>
                </div>
              )}

              {strategyType === 'turtle_trading' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-gray-400">Entry Period (Breakout)</label>
                    <input
                      type="number"
                      value={parameters.entry_period}
                      onChange={(e) =>
                        setParameters({ ...parameters, entry_period: parseInt(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400">Exit Period</label>
                    <input
                      type="number"
                      value={parameters.exit_period}
                      onChange={(e) =>
                        setParameters({ ...parameters, exit_period: parseInt(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400">ATR Period</label>
                    <input
                      type="number"
                      value={parameters.atr_period}
                      onChange={(e) =>
                        setParameters({ ...parameters, atr_period: parseInt(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={parameters.use_system_2}
                        onChange={(e) => setParameters({ ...parameters, use_system_2: e.target.checked })}
                        className="rounded bg-slate-700 border-slate-600 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-400">Use System 2 (55-day entry)</span>
                    </label>
                  </div>
                </div>
              )}

              {strategyType === 'pairs_trading' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-gray-400">Lookback Period</label>
                    <input
                      type="number"
                      value={parameters.lookback_period}
                      onChange={(e) =>
                        setParameters({ ...parameters, lookback_period: parseInt(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400">Entry Threshold</label>
                    <input
                      type="number"
                      step="0.1"
                      value={parameters.entry_threshold}
                      onChange={(e) =>
                        setParameters({ ...parameters, entry_threshold: parseFloat(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400">Exit Threshold</label>
                    <input
                      type="number"
                      step="0.1"
                      value={parameters.exit_threshold}
                      onChange={(e) =>
                        setParameters({ ...parameters, exit_threshold: parseFloat(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400">Hedge Ratio Period</label>
                    <input
                      type="number"
                      value={parameters.hedge_ratio_period}
                      onChange={(e) =>
                        setParameters({ ...parameters, hedge_ratio_period: parseInt(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
              )}

              {strategyType === 'vwap' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-gray-400">Std Multiplier (for bands)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={parameters.std_multiplier}
                      onChange={(e) =>
                        setParameters({ ...parameters, std_multiplier: parseFloat(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400">Lookback Period (0 = intraday)</label>
                    <input
                      type="number"
                      value={parameters.lookback_period}
                      onChange={(e) =>
                        setParameters({ ...parameters, lookback_period: parseInt(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={parameters.use_bands}
                        onChange={(e) => setParameters({ ...parameters, use_bands: e.target.checked })}
                        className="rounded bg-slate-700 border-slate-600 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-400">Use VWAP Bands</span>
                    </label>
                  </div>
                </div>
              )}

              {strategyType === 'ichimoku' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-gray-400">Tenkan Period (Conversion Line)</label>
                    <input
                      type="number"
                      value={parameters.tenkan_period}
                      onChange={(e) =>
                        setParameters({ ...parameters, tenkan_period: parseInt(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400">Kijun Period (Base Line)</label>
                    <input
                      type="number"
                      value={parameters.kijun_period}
                      onChange={(e) =>
                        setParameters({ ...parameters, kijun_period: parseInt(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400">Senkou Span B Period</label>
                    <input
                      type="number"
                      value={parameters.senkou_span_b_period}
                      onChange={(e) =>
                        setParameters({ ...parameters, senkou_span_b_period: parseInt(e.target.value) })
                      }
                      className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
              )}

              {strategyType === 'multi_strategy' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-gray-400">Voting Method</label>
                    <select
                      value={parameters.voting_method}
                      onChange={(e) => setParameters({ ...parameters, voting_method: e.target.value })}
                      className="mt-1 block w-full pl-3 pr-10 py-2 bg-slate-700 border-slate-600 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
                    >
                      <option value="weighted">Weighted Average</option>
                      <option value="majority">Majority Vote</option>
                      <option value="unanimous">Unanimous</option>
                    </select>
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    Note: Multi-strategy combines MA, RSI, and MACD with weights [0.4, 0.3, 0.3]
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Trading
