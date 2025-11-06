import React, { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Eye, Plus, X, TrendingUp, TrendingDown, ShoppingCart } from 'lucide-react'
import { getWatchlist, addToWatchlist, removeFromWatchlist, getQuote, placeOrder } from '../services/api'

function Watchlist() {
  const queryClient = useQueryClient()
  const [newSymbol, setNewSymbol] = useState('')
  const [orderModal, setOrderModal] = useState(null)
  const [orderSide, setOrderSide] = useState('buy')
  const [orderQty, setOrderQty] = useState(1)

  const { data: watchlist } = useQuery({
    queryKey: ['watchlist'],
    queryFn: async () => {
      const response = await getWatchlist()
      return response.data
    },
    refetchInterval: 5000, // Refresh every 5 seconds
  })

  const addMutation = useMutation({
    mutationFn: addToWatchlist,
    onSuccess: () => {
      queryClient.invalidateQueries(['watchlist'])
      setNewSymbol('')
    },
  })

  const removeMutation = useMutation({
    mutationFn: removeFromWatchlist,
    onSuccess: () => {
      queryClient.invalidateQueries(['watchlist'])
    },
  })

  const orderMutation = useMutation({
    mutationFn: placeOrder,
    onSuccess: () => {
      setOrderModal(null)
      setOrderQty(1)
      queryClient.invalidateQueries(['positions'])
    },
  })

  const handleAddSymbol = () => {
    if (newSymbol.trim()) {
      addMutation.mutate(newSymbol.trim().toUpperCase())
    }
  }

  const handleQuickTrade = () => {
    if (orderModal) {
      orderMutation.mutate({
        symbol: orderModal.symbol,
        qty: orderQty,
        side: orderSide,
        type: 'market',
      })
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-white">Watchlist</h2>
        <p className="text-gray-400 mt-1">Monitor your favorite symbols with live prices</p>
      </div>

      {/* Add Symbol */}
      <div className="bg-slate-800 shadow rounded-lg p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={newSymbol}
            onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
            onKeyPress={(e) => e.key === 'Enter' && handleAddSymbol()}
            placeholder="Add symbol (e.g., AAPL)"
            className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
          <button
            onClick={handleAddSymbol}
            disabled={addMutation.isPending || !newSymbol.trim()}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            <Plus className="mr-2" size={16} />
            Add
          </button>
        </div>
      </div>

      {/* Watchlist Table */}
      <div className="bg-slate-800 shadow rounded-lg">
        <div className="px-4 py-5 sm:px-6 border-b border-slate-700">
          <h3 className="text-lg leading-6 font-medium text-white flex items-center">
            <Eye className="mr-2" size={20} />
            Your Watchlist
          </h3>
        </div>
        <div className="overflow-x-auto">
          {watchlist && watchlist.length > 0 ? (
            <table className="min-w-full divide-y divide-slate-700">
              <thead className="bg-slate-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Symbol</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Change</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Change %</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Volume</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">High</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Low</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-slate-800 divide-y divide-slate-700">
                {watchlist.map((item) => (
                  <tr key={item.symbol} className="hover:bg-slate-750">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                      {item.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      ${item.price?.toFixed(2)}
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${item.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      <div className="flex items-center">
                        {item.change >= 0 ? <TrendingUp size={16} className="mr-1" /> : <TrendingDown size={16} className="mr-1" />}
                        ${Math.abs(item.change || 0).toFixed(2)}
                      </div>
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${item.change_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {item.change_percent?.toFixed(2)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {item.volume?.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      ${item.high?.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      ${item.low?.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                      <button
                        onClick={() => setOrderModal(item)}
                        className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-white bg-blue-600 hover:bg-blue-700"
                      >
                        <ShoppingCart size={14} className="mr-1" />
                        Trade
                      </button>
                      <button
                        onClick={() => removeMutation.mutate(item.symbol)}
                        className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-white bg-red-600 hover:bg-red-700"
                      >
                        <X size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="px-6 py-12 text-center text-gray-400">
              No symbols in watchlist. Add some symbols to start monitoring!
            </div>
          )}
        </div>
      </div>

      {/* Quick Trade Modal */}
      {orderModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-white">Quick Trade - {orderModal.symbol}</h3>
              <button
                onClick={() => setOrderModal(null)}
                className="text-gray-400 hover:text-white"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Current Price</label>
                <div className="text-2xl font-bold text-white">${orderModal.price?.toFixed(2)}</div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Side</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setOrderSide('buy')}
                    className={`flex-1 py-2 rounded-md font-medium ${
                      orderSide === 'buy'
                        ? 'bg-green-600 text-white'
                        : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
                    }`}
                  >
                    Buy
                  </button>
                  <button
                    onClick={() => setOrderSide('sell')}
                    className={`flex-1 py-2 rounded-md font-medium ${
                      orderSide === 'sell'
                        ? 'bg-red-600 text-white'
                        : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
                    }`}
                  >
                    Sell
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Quantity</label>
                <input
                  type="number"
                  min="1"
                  value={orderQty}
                  onChange={(e) => setOrderQty(parseInt(e.target.value) || 1)}
                  className="mt-1 block w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="bg-slate-700 rounded-lg p-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">Estimated Total:</span>
                  <span className="text-white font-medium">
                    ${((orderModal.price || 0) * orderQty).toFixed(2)}
                  </span>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setOrderModal(null)}
                  className="flex-1 px-4 py-2 border border-slate-600 text-sm font-medium rounded-md text-white hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  onClick={handleQuickTrade}
                  disabled={orderMutation.isPending}
                  className={`flex-1 px-4 py-2 text-sm font-medium rounded-md text-white ${
                    orderSide === 'buy'
                      ? 'bg-green-600 hover:bg-green-700'
                      : 'bg-red-600 hover:bg-red-700'
                  } disabled:opacity-50`}
                >
                  {orderMutation.isPending ? 'Placing...' : `${orderSide === 'buy' ? 'Buy' : 'Sell'} ${orderQty} Share${orderQty > 1 ? 's' : ''}`}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Watchlist
