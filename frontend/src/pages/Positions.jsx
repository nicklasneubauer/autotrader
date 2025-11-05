import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getPositions, closePosition, placeOrder } from '../services/api'
import { DollarSign, X, ShoppingCart } from 'lucide-react'

function Positions() {
  const queryClient = useQueryClient()
  const [showOrderForm, setShowOrderForm] = useState(false)
  const [orderData, setOrderData] = useState({
    symbol: '',
    qty: 1,
    side: 'buy',
    order_type: 'market',
    limit_price: null,
  })

  const { data: positions, isLoading } = useQuery({
    queryKey: ['positions'],
    queryFn: async () => {
      const response = await getPositions()
      return response.data
    },
    refetchInterval: 10000,
  })

  const closeMutation = useMutation({
    mutationFn: closePosition,
    onSuccess: () => {
      queryClient.invalidateQueries(['positions'])
      queryClient.invalidateQueries(['account'])
    },
  })

  const orderMutation = useMutation({
    mutationFn: placeOrder,
    onSuccess: () => {
      queryClient.invalidateQueries(['positions'])
      queryClient.invalidateQueries(['account'])
      setShowOrderForm(false)
      setOrderData({
        symbol: '',
        qty: 1,
        side: 'buy',
        order_type: 'market',
        limit_price: null,
      })
    },
  })

  const handleClose = (symbol) => {
    if (confirm(`Are you sure you want to close position for ${symbol}?`)) {
      closeMutation.mutate(symbol)
    }
  }

  const handlePlaceOrder = () => {
    orderMutation.mutate(orderData)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white">Positions</h2>
          <p className="text-gray-400 mt-1">Manage your open positions and place orders</p>
        </div>
        <button
          onClick={() => setShowOrderForm(!showOrderForm)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <ShoppingCart className="mr-2" size={16} />
          Place Order
        </button>
      </div>

      {/* Order Form */}
      {showOrderForm && (
        <div className="bg-slate-800 shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">New Order</h3>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-300">Symbol</label>
              <input
                type="text"
                value={orderData.symbol}
                onChange={(e) => setOrderData({ ...orderData, symbol: e.target.value })}
                className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., AAPL"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300">Quantity</label>
              <input
                type="number"
                value={orderData.qty}
                onChange={(e) => setOrderData({ ...orderData, qty: parseFloat(e.target.value) })}
                className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300">Side</label>
              <select
                value={orderData.side}
                onChange={(e) => setOrderData({ ...orderData, side: e.target.value })}
                className="mt-1 block w-full pl-3 pr-10 py-2 bg-slate-700 border-slate-600 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
              >
                <option value="buy">Buy</option>
                <option value="sell">Sell</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300">Order Type</label>
              <select
                value={orderData.order_type}
                onChange={(e) => setOrderData({ ...orderData, order_type: e.target.value })}
                className="mt-1 block w-full pl-3 pr-10 py-2 bg-slate-700 border-slate-600 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 rounded-md"
              >
                <option value="market">Market</option>
                <option value="limit">Limit</option>
              </select>
            </div>

            {orderData.order_type === 'limit' && (
              <div>
                <label className="block text-sm font-medium text-gray-300">Limit Price</label>
                <input
                  type="number"
                  step="0.01"
                  value={orderData.limit_price || ''}
                  onChange={(e) =>
                    setOrderData({ ...orderData, limit_price: parseFloat(e.target.value) })
                  }
                  className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            )}
          </div>

          <div className="mt-6 flex space-x-3">
            <button
              onClick={handlePlaceOrder}
              disabled={orderMutation.isPending}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
            >
              Place Order
            </button>
            <button
              onClick={() => setShowOrderForm(false)}
              className="inline-flex items-center px-4 py-2 border border-slate-600 text-sm font-medium rounded-md text-gray-300 bg-slate-700 hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Positions Table */}
      <div className="bg-slate-800 shadow rounded-lg">
        <div className="px-4 py-5 sm:px-6 border-b border-slate-700">
          <h3 className="text-lg leading-6 font-medium text-white flex items-center">
            <DollarSign className="mr-2" size={20} />
            Open Positions
          </h3>
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
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Actions
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      <button
                        onClick={() => handleClose(position.symbol)}
                        disabled={closeMutation.isPending}
                        className="text-red-400 hover:text-red-300 disabled:opacity-50"
                      >
                        <X size={18} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="px-6 py-12 text-center text-gray-400">No open positions</div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Positions
