import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Backtest from './pages/Backtest'
import Trading from './pages/Trading'
import Positions from './pages/Positions'
import { Activity, TrendingUp, BarChart3, DollarSign } from 'lucide-react'

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
                <div className="ml-10 flex items-baseline space-x-4">
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
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
