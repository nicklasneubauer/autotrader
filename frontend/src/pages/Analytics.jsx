import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BarChart3, TrendingUp, TrendingDown, DollarSign, Target, AlertTriangle } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { getAnalytics, getTrades } from '../services/api'

function Analytics() {
  const [timeframe, setTimeframe] = useState('all')
  const [strategyFilter, setStrategyFilter] = useState('all')

  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ['analytics', timeframe],
    queryFn: async () => {
      const response = await getAnalytics(timeframe)
      return response.data
    },
    refetchInterval: 30000,
  })

  const { data: trades, isLoading: tradesLoading } = useQuery({
    queryKey: ['trades', strategyFilter],
    queryFn: async () => {
      const response = await getTrades(strategyFilter)
      return response.data
    },
    refetchInterval: 30000,
  })

  if (analyticsLoading || tradesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading analytics...</div>
      </div>
    )
  }

  const returnMetrics = analytics?.returns || {}
  const riskMetrics = analytics?.risk || {}
  const tradeMetrics = analytics?.trades || {}
  const timeMetrics = analytics?.time || {}

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-white">Performance Analytics</h2>
        <p className="text-gray-400 mt-1">Comprehensive performance metrics and trade analysis</p>
      </div>

      {/* Filters */}
      <div className="bg-slate-800 shadow rounded-lg p-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-300">Timeframe</label>
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="mt-1 block w-full pl-3 pr-10 py-2 bg-slate-700 border-slate-600 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
            >
              <option value="all">All Time</option>
              <option value="1y">Last Year</option>
              <option value="6m">Last 6 Months</option>
              <option value="3m">Last 3 Months</option>
              <option value="1m">Last Month</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300">Strategy Filter</label>
            <select
              value={strategyFilter}
              onChange={(e) => setStrategyFilter(e.target.value)}
              className="mt-1 block w-full pl-3 pr-10 py-2 bg-slate-700 border-slate-600 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
            >
              <option value="all">All Strategies</option>
              <option value="moving_average">Moving Average</option>
              <option value="rsi">RSI</option>
              <option value="macd">MACD</option>
              <option value="bollinger_bands">Bollinger Bands</option>
              <option value="mean_reversion">Mean Reversion</option>
              <option value="turtle_trading">Turtle Trading</option>
              <option value="pairs_trading">Pairs Trading</option>
              <option value="vwap">VWAP</option>
              <option value="ichimoku">Ichimoku</option>
            </select>
          </div>
        </div>
      </div>

      {/* Returns Metrics */}
      <div className="bg-slate-800 shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4 flex items-center">
          <TrendingUp className="mr-2" size={20} />
          Returns Metrics
        </h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard title="Total Return" value={`${returnMetrics.total_return?.toFixed(2) || 0}%`} color={returnMetrics.total_return >= 0 ? 'green' : 'red'} />
          <MetricCard title="CAGR" value={`${returnMetrics.cagr?.toFixed(2) || 0}%`} color={returnMetrics.cagr >= 0 ? 'green' : 'red'} />
          <MetricCard title="Avg Monthly Return" value={`${returnMetrics.avg_monthly?.toFixed(2) || 0}%`} color={returnMetrics.avg_monthly >= 0 ? 'green' : 'red'} />
          <MetricCard title="Best Month" value={`${returnMetrics.best_month?.toFixed(2) || 0}%`} color="green" />
        </div>
      </div>

      {/* Risk Metrics */}
      <div className="bg-slate-800 shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4 flex items-center">
          <AlertTriangle className="mr-2" size={20} />
          Risk Metrics
        </h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <MetricCard title="Sharpe Ratio" value={riskMetrics.sharpe_ratio?.toFixed(2) || '0.00'} color={riskMetrics.sharpe_ratio > 1 ? 'green' : 'yellow'} />
          <MetricCard title="Sortino Ratio" value={riskMetrics.sortino_ratio?.toFixed(2) || '0.00'} color={riskMetrics.sortino_ratio > 1 ? 'green' : 'yellow'} />
          <MetricCard title="Calmar Ratio" value={riskMetrics.calmar_ratio?.toFixed(2) || '0.00'} color={riskMetrics.calmar_ratio > 1 ? 'green' : 'yellow'} />
          <MetricCard title="Max Drawdown" value={`${riskMetrics.max_drawdown?.toFixed(2) || 0}%`} color="red" />
          <MetricCard title="Volatility" value={`${riskMetrics.volatility?.toFixed(2) || 0}%`} color="blue" />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 mt-4">
          <MetricCard title="VaR (95%)" value={`${riskMetrics.var_95?.toFixed(2) || 0}%`} color="orange" />
          <MetricCard title="CVaR (95%)" value={`${riskMetrics.cvar_95?.toFixed(2) || 0}%`} color="orange" />
          <MetricCard title="Beta" value={riskMetrics.beta?.toFixed(2) || '0.00'} color="blue" />
        </div>
      </div>

      {/* Trade Metrics */}
      <div className="bg-slate-800 shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4 flex items-center">
          <Target className="mr-2" size={20} />
          Trade Metrics
        </h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard title="Total Trades" value={tradeMetrics.total_trades || 0} color="blue" />
          <MetricCard title="Win Rate" value={`${tradeMetrics.win_rate?.toFixed(2) || 0}%`} color={tradeMetrics.win_rate >= 50 ? 'green' : 'red'} />
          <MetricCard title="Profit Factor" value={tradeMetrics.profit_factor?.toFixed(2) || '0.00'} color={tradeMetrics.profit_factor >= 1 ? 'green' : 'red'} />
          <MetricCard title="Avg Win/Loss" value={tradeMetrics.avg_win_loss_ratio?.toFixed(2) || '0.00'} color={tradeMetrics.avg_win_loss_ratio >= 1 ? 'green' : 'red'} />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 mt-4">
          <MetricCard title="Avg Trade P&L" value={`$${tradeMetrics.avg_trade_pnl?.toFixed(2) || 0}`} color={tradeMetrics.avg_trade_pnl >= 0 ? 'green' : 'red'} />
          <MetricCard title="Best Trade" value={`$${tradeMetrics.best_trade?.toFixed(2) || 0}`} color="green" />
          <MetricCard title="Worst Trade" value={`$${tradeMetrics.worst_trade?.toFixed(2) || 0}`} color="red" />
        </div>
      </div>

      {/* Equity Curve */}
      {analytics?.equity_curve && (
        <div className="bg-slate-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Equity Curve</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analytics.equity_curve}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                labelStyle={{ color: '#e5e7eb' }}
              />
              <Legend />
              <Line type="monotone" dataKey="portfolio_value" stroke="#3b82f6" strokeWidth={2} name="Portfolio Value" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Monthly Performance */}
      {timeMetrics?.monthly_returns && (
        <div className="bg-slate-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Monthly Returns</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={timeMetrics.monthly_returns}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="month" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                labelStyle={{ color: '#e5e7eb' }}
              />
              <Bar dataKey="return" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Trade History */}
      <div className="bg-slate-800 shadow rounded-lg">
        <div className="px-4 py-5 sm:px-6 border-b border-slate-700">
          <h3 className="text-lg leading-6 font-medium text-white">Trade History</h3>
        </div>
        <div className="overflow-x-auto">
          {trades && trades.length > 0 ? (
            <table className="min-w-full divide-y divide-slate-700">
              <thead className="bg-slate-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Symbol</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Side</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Quantity</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">P&L</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Strategy</th>
                </tr>
              </thead>
              <tbody className="bg-slate-800 divide-y divide-slate-700">
                {trades.map((trade, idx) => (
                  <tr key={idx}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {new Date(trade.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                      {trade.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 rounded text-xs ${trade.side === 'buy' ? 'bg-green-900 text-green-200' : 'bg-red-900 text-red-200'}`}>
                        {trade.side.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {trade.quantity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      ${trade.price?.toFixed(2)}
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {trade.pnl ? `$${trade.pnl.toFixed(2)}` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                      {trade.strategy || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="px-6 py-12 text-center text-gray-400">
              No trades yet
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function MetricCard({ title, value, color }) {
  const colorClasses = {
    blue: 'bg-blue-900 text-blue-400',
    green: 'bg-green-900 text-green-400',
    red: 'bg-red-900 text-red-400',
    yellow: 'bg-yellow-900 text-yellow-400',
    orange: 'bg-orange-900 text-orange-400',
    purple: 'bg-purple-900 text-purple-400',
  }

  return (
    <div className="bg-slate-700 rounded-lg p-4">
      <div className="text-sm text-gray-400">{title}</div>
      <div className={`mt-1 text-2xl font-semibold ${colorClasses[color]?.split(' ')[1] || 'text-white'}`}>
        {value}
      </div>
    </div>
  )
}

export default Analytics
