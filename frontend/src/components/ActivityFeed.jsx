import React, { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Activity, TrendingUp, TrendingDown, AlertCircle, CheckCircle, Bell } from 'lucide-react'
import { getRecentActivity } from '../services/api'

function ActivityFeed({ maxItems = 10 }) {
  const [activities, setActivities] = useState([])

  const { data: recentActivity } = useQuery({
    queryKey: ['recentActivity'],
    queryFn: async () => {
      const response = await getRecentActivity(maxItems)
      return response.data
    },
    refetchInterval: 5000, // Refresh every 5 seconds
  })

  useEffect(() => {
    if (recentActivity) {
      setActivities(recentActivity)
    }
  }, [recentActivity])

  const getActivityIcon = (type) => {
    switch (type) {
      case 'trade_buy':
        return <TrendingUp size={16} className="text-green-400" />
      case 'trade_sell':
        return <TrendingDown size={16} className="text-red-400" />
      case 'signal':
        return <Bell size={16} className="text-blue-400" />
      case 'risk_alert':
        return <AlertCircle size={16} className="text-yellow-400" />
      case 'bot_started':
      case 'bot_stopped':
        return <Activity size={16} className="text-purple-400" />
      default:
        return <CheckCircle size={16} className="text-gray-400" />
    }
  }

  const getActivityColor = (type) => {
    switch (type) {
      case 'trade_buy':
        return 'border-green-700 bg-green-900 bg-opacity-20'
      case 'trade_sell':
        return 'border-red-700 bg-red-900 bg-opacity-20'
      case 'signal':
        return 'border-blue-700 bg-blue-900 bg-opacity-20'
      case 'risk_alert':
        return 'border-yellow-700 bg-yellow-900 bg-opacity-20'
      case 'bot_started':
      case 'bot_stopped':
        return 'border-purple-700 bg-purple-900 bg-opacity-20'
      default:
        return 'border-slate-700 bg-slate-800'
    }
  }

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return date.toLocaleString()
  }

  return (
    <div className="bg-slate-800 shadow rounded-lg">
      <div className="px-4 py-5 sm:px-6 border-b border-slate-700">
        <h3 className="text-lg leading-6 font-medium text-white flex items-center">
          <Activity className="mr-2" size={20} />
          Live Activity Feed
        </h3>
      </div>
      <div className="p-4 max-h-96 overflow-y-auto">
        {activities && activities.length > 0 ? (
          <div className="space-y-3">
            {activities.map((activity, idx) => (
              <div
                key={idx}
                className={`border rounded-lg p-3 ${getActivityColor(activity.type)}`}
              >
                <div className="flex items-start">
                  <div className="flex-shrink-0 mt-1">
                    {getActivityIcon(activity.type)}
                  </div>
                  <div className="ml-3 flex-1">
                    <p className="text-sm text-white font-medium">
                      {activity.title}
                    </p>
                    {activity.message && (
                      <p className="text-xs text-gray-400 mt-1">
                        {activity.message}
                      </p>
                    )}
                    {activity.details && (
                      <div className="text-xs text-gray-500 mt-2 font-mono">
                        {JSON.stringify(activity.details)}
                      </div>
                    )}
                  </div>
                  <div className="flex-shrink-0 ml-2">
                    <span className="text-xs text-gray-500">
                      {formatTimestamp(activity.timestamp)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
            No recent activity
          </div>
        )}
      </div>
    </div>
  )
}

export default ActivityFeed
