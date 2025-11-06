import React, { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getAccount, getPositions, getBotStatus, createWebSocket, getPortfolioHistory } from '../services/api'
import { TrendingUp, TrendingDown, DollarSign, Activity } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts'
import ActivityFeed from '../components/ActivityFeed'

function Dashboard() {
  const [wsData, setWsData] = useState(null)

  const { data: account, isLoading: accountLoading } = useQuery({
    queryKey: ['account'],
    queryFn: async () => {
      const response = await getAccount()
      return response.data
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  const { data: positions, isLoading: positionsLoading } = useQuery({
    queryKey: ['positions'],
    queryFn: async () => {
      const response = await getPositions()
      return response.data
    },
    refetchInterval: 30000,
  })

  const { data: botStatus } = useQuery({
    queryKey: ['botStatus'],
    queryFn: async () => {
      const response = await getBotStatus()
      return response.data
    },
    refetchInterval: 5000,
  })

  const { data: portfolioHistory } = useQuery({
    queryKey: ['portfolioHistory'],
    queryFn: async () => {
      const response = await getPortfolioHistory('7d')
      return response.data
    },
    refetchInterval: 60000, // Refresh every minute
  })

  // WebSocket connection
  useEffect(() => {
    const ws = createWebSocket()

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setWsData(data)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    return () => {
      ws.close()
    }
  }, [])

  if (accountLoading || positionsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading...</div>
      </div>
    )
  }

  const totalPnL = positions?.reduce((sum, pos) => sum + pos.unrealized_pl, 0) || 0
  const totalValue = positions?.reduce((sum, pos) => sum + pos.market_value, 0) || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-white">Dashboard</h2>
        <p className="text-gray-400 mt-1">Overview of your trading account</p>
      </div>

      {/* Bot Status Alert */}
      {botStatus?.is_running && (
        <div className="bg-green-900 border border-green-700 rounded-lg p-4">
          <div className="flex items-center">
            <Activity className="text-green-400 mr-2" size={20} />
            <span className="text-green-200 font-medium">
              Trading Bot Active - {botStatus.strategy} strategy running on {botStatus.symbols?.join(', ')}
            </span>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Portfolio Value"
          value={`$${account?.portfolio_value?.toFixed(2) || '0.00'}`}
          icon={<DollarSign />}
          color="blue"
        />
        <StatCard
          title="Buying Power"
          value={`$${account?.buying_power?.toFixed(2) || '0.00'}`}
          icon={<TrendingUp />}
          color="green"
        />
        <StatCard
          title="Cash"
          value={`$${account?.cash?.toFixed(2) || '0.00'}`}
          icon={<DollarSign />}
          color="purple"
        />
        <StatCard
          title="Total P&L"
          value={`$${totalPnL.toFixed(2)}`}
          icon={totalPnL >= 0 ? <TrendingUp /> : <TrendingDown />}
          color={totalPnL >= 0 ? 'green' : 'red'}
        />
      </div>

      {/* Portfolio Performance Chart */}
      {portfolioHistory && portfolioHistory.length > 0 && (
        <div className="bg-slate-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Portfolio Performance (7 Days)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={portfolioHistory}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="timestamp"
                stroke="#9CA3AF"
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                labelStyle={{ color: '#e5e7eb' }}
                labelFormatter={(value) => new Date(value).toLocaleString()}
              />
              <Area
                type="monotone"
                dataKey="portfolio_value"
                stroke="#3b82f6"
                fillOpacity={1}
                fill="url(#colorValue)"
                name="Portfolio Value"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* P&L Chart */}
      {portfolioHistory && portfolioHistory.length > 0 && (
        <div className="bg-slate-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Profit & Loss</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={portfolioHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="timestamp"
                stroke="#9CA3AF"
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                labelStyle={{ color: '#e5e7eb' }}
                labelFormatter={(value) => new Date(value).toLocaleString()}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="pnl"
                stroke="#10b981"
                strokeWidth={2}
                name="P&L ($)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Activity Feed */}
      <ActivityFeed maxItems={15} />

      {/* Positions */}
      <div className="bg-slate-800 shadow rounded-lg">
        <div className="px-4 py-5 sm:px-6 border-b border-slate-700">
          <h3 className="text-lg leading-6 font-medium text-white">Open Positions</h3>
        </div>
        <div className="overflow-x-auto">
          {positions && positions.length > 0 ? (
            <table className="min-w-full divide-y divide-slate-700">
              <thead className="bg-slate-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Symbol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Avg Entry
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Current Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Market Value
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    P&L
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    P&L %
                  </th>
                </tr>
              </thead>
              <tbody className="bg-slate-800 divide-y divide-slate-700">
                {positions.map((position) => (
                  <tr key={position.symbol}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                      {position.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {position.qty}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      ${position.avg_entry_price.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      ${position.current_price.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      ${position.market_value.toFixed(2)}
                    </td>
                    <td
                      className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                        position.unrealized_pl >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}
                    >
                      ${position.unrealized_pl.toFixed(2)}
                    </td>
                    <td
                      className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                        position.unrealized_plpc >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}
                    >
                      {(position.unrealized_plpc * 100).toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="px-6 py-12 text-center text-gray-400">
              No open positions
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, icon, color }) {
  const colorClasses = {
    blue: 'bg-blue-900 text-blue-400',
    green: 'bg-green-900 text-green-400',
    purple: 'bg-purple-900 text-purple-400',
    red: 'bg-red-900 text-red-400',
  }

  return (
    <div className="bg-slate-800 overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className={`flex-shrink-0 rounded-md p-3 ${colorClasses[color]}`}>
            {icon}
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-400 truncate">{title}</dt>
              <dd className="text-lg font-semibold text-white">{value}</dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
