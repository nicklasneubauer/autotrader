import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Backtest from './pages/Backtest'
import Trading from './pages/Trading'
import Positions from './pages/Positions'
import Analytics from './pages/Analytics'
import StrategyComparison from './pages/StrategyComparison'
import Watchlist from './pages/Watchlist'
import Optimization from './pages/Optimization'
import { Activity, TrendingUp, BarChart3, DollarSign, Target, Eye, Settings, GitCompare } from 'lucide-react'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-900">
        <nav className="bg-slate-800 border-b border-slate-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <h1 className="text-2xl font-bold text-blue-400">
                    <Activity className="inline-block mr-2" size={28} />
                    Autotrader
                  </h1>
                </div>
                <div className="ml-10 flex items-baseline space-x-2">
                  <Link
                    to="/"
                    className="text-gray-300 hover:bg-slate-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
                  >
                    <TrendingUp className="inline-block mr-1" size={16} />
                    Dashboard
                  </Link>
                  <Link
                    to="/trading"
                    className="text-gray-300 hover:bg-slate-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
                  >
                    <Activity className="inline-block mr-1" size={16} />
                    Trading Bot
                  </Link>
                  <Link
                    to="/backtest"
                    className="text-gray-300 hover:bg-slate-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
                  >
                    <BarChart3 className="inline-block mr-1" size={16} />
                    Backtest
                  </Link>
                  <Link
                    to="/positions"
                    className="text-gray-300 hover:bg-slate-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
                  >
                    <DollarSign className="inline-block mr-1" size={16} />
                    Positions
                  </Link>
                  <Link
                    to="/analytics"
                    className="text-gray-300 hover:bg-slate-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
                  >
                    <Target className="inline-block mr-1" size={16} />
                    Analytics
                  </Link>
                  <Link
                    to="/comparison"
                    className="text-gray-300 hover:bg-slate-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
                  >
                    <GitCompare className="inline-block mr-1" size={16} />
                    Compare
                  </Link>
                  <Link
                    to="/watchlist"
                    className="text-gray-300 hover:bg-slate-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
                  >
                    <Eye className="inline-block mr-1" size={16} />
                    Watchlist
                  </Link>
                  <Link
                    to="/optimize"
                    className="text-gray-300 hover:bg-slate-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
                  >
                    <Settings className="inline-block mr-1" size={16} />
                    Optimize
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </nav>

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/trading" element={<Trading />} />
            <Route path="/backtest" element={<Backtest />} />
            <Route path="/positions" element={<Positions />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/comparison" element={<StrategyComparison />} />
            <Route path="/watchlist" element={<Watchlist />} />
            <Route path="/optimize" element={<Optimization />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
