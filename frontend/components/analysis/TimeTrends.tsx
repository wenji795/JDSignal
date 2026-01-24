'use client'

import { useEffect, useState } from 'react'
import { getTimeTrends, type TimeTrendsResponse } from '@/lib/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface TimeTrendsProps {
  days?: number
  role_family?: string
  seniority?: string
  location?: string
}

const roleFamilyColors: Record<string, string> = {
  'testing': '#db2777',
  'ai': '#9333ea',
  'fullstack': '#4f46e5',
  'frontend': '#0891b2',
  'devops': '#059669',
  'data': '#2563eb',
  'business analyst': '#d97706',
  'product manager': '#e11d48',
  'mobile': '#0d9488',
  '其他': '#6b7280'
}

export default function TimeTrends({ days = 90, role_family, seniority, location }: TimeTrendsProps) {
  const [data, setData] = useState<TimeTrendsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [granularity, setGranularity] = useState<'day' | 'week' | 'month'>('day')

  useEffect(() => {
    loadTrends()
  }, [days, granularity, role_family, seniority, location])

  const loadTrends = async () => {
    try {
      setLoading(true)
      const params: any = { days, granularity }
      if (role_family) params.role_family = role_family
      if (seniority) params.seniority = seniority
      if (location) params.location = location

      const result = await getTimeTrends(params)
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load time trends')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-8">Loading time trends...</div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-red-500">Error: {error || 'Failed to load data'}</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium">Granularity:</label>
          <select
            value={granularity}
            onChange={(e) => setGranularity(e.target.value as 'day' | 'week' | 'month')}
            className="p-2 border rounded text-sm"
          >
            <option value="day">Day</option>
            <option value="week">Week</option>
            <option value="month">Month</option>
          </select>
        </div>
      </div>

      {/* Job Count Trend */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Job Count Trend</h3>
        {data.job_count_trend.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart 
              data={[...data.job_count_trend].sort((a, b) => a.date.localeCompare(b.date))}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                angle={-45}
                textAnchor="end"
                height={100}
              />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="count" stroke="#8884d8" strokeWidth={2} name="Job Count" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-8 text-gray-500">No data available</div>
        )}
      </div>

      {/* Role Family Trends */}
      {Object.keys(data.role_family_trends).length > 0 && (() => {
        // 合并所有日期，创建统一的数据结构
        const allDates = new Set<string>()
        Object.values(data.role_family_trends).forEach(trendData => {
          trendData.forEach(item => allDates.add(item.date))
        })
        // 确保日期按时间顺序排序
        const sortedDates = Array.from(allDates).sort((a, b) => a.localeCompare(b))
        
        // 创建合并后的数据
        const mergedData = sortedDates.map(date => {
          const item: any = { date }
          Object.entries(data.role_family_trends).forEach(([roleFamily, trendData]) => {
            const found = trendData.find(d => d.date === date)
            item[roleFamily] = found ? found.count : 0
          })
          return item
        })
        
        return (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-semibold mb-4">Role Family Trends</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={mergedData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  angle={-45}
                  textAnchor="end"
                  height={100}
                />
                <YAxis />
                <Tooltip />
                <Legend />
                {Object.keys(data.role_family_trends).map((roleFamily) => (
                  <Line
                    key={roleFamily}
                    type="monotone"
                    dataKey={roleFamily}
                    stroke={roleFamilyColors[roleFamily.toLowerCase()] || '#6b7280'}
                    strokeWidth={2}
                    name={roleFamily}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )
      })()}

      {/* Keyword Trends */}
      {Object.keys(data.keyword_trends).length > 0 && (() => {
        const topKeywords = Object.entries(data.keyword_trends).slice(0, 10)
        
        // 合并所有日期，创建统一的数据结构
        const allDates = new Set<string>()
        topKeywords.forEach(([, trendData]) => {
          trendData.forEach(item => allDates.add(item.date))
        })
        // 确保日期按时间顺序排序
        const sortedDates = Array.from(allDates).sort((a, b) => a.localeCompare(b))
        
        // 创建合并后的数据
        const mergedData = sortedDates.map(date => {
          const item: any = { date }
          topKeywords.forEach(([keyword, trendData]) => {
            const found = trendData.find(d => d.date === date)
            item[keyword] = found ? found.count : 0
          })
          return item
        })
        
        return (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-semibold mb-4">Top 10 Keyword Trends</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={mergedData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  angle={-45}
                  textAnchor="end"
                  height={100}
                />
                <YAxis />
                <Tooltip />
                <Legend />
                {topKeywords.map(([keyword], index) => (
                  <Line
                    key={keyword}
                    type="monotone"
                    dataKey={keyword}
                    stroke={`hsl(${(index * 360) / 10}, 70%, 50%)`}
                    strokeWidth={2}
                    name={keyword}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )
      })()}
    </div>
  )
}
