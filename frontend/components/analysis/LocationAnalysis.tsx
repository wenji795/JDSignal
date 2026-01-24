'use client'

import { useEffect, useState } from 'react'
import { getLocationAnalysis, type LocationAnalysisResponse } from '@/lib/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Legend } from 'recharts'

interface LocationAnalysisProps {
  days?: number
  role_family?: string
  seniority?: string
  location?: string
}

export default function LocationAnalysis({ days = 30, role_family, seniority, location }: LocationAnalysisProps) {
  const [data, setData] = useState<LocationAnalysisResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [days, role_family, seniority, location])

  const loadData = async () => {
    try {
      setLoading(true)
      const params: any = { days }
      if (role_family) params.role_family = role_family
      if (seniority) params.seniority = seniority
      if (location) params.location = location

      const result = await getLocationAnalysis(params)
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load location analysis')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-8">Loading location analysis...</div>
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
      {/* Location Distribution */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Location Distribution (Top 20)</h3>
        {data.location_distribution.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={data.location_distribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="location" 
                angle={-45}
                textAnchor="end"
                height={100}
              />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-8 text-gray-500">No location data available</div>
        )}
      </div>

      {/* Location Trends */}
      {Object.keys(data.location_trends).length > 0 && (() => {
        const top5Cities = Object.entries(data.location_trends).slice(0, 5)
        
        // 合并所有日期，创建统一的数据结构
        const allWeeks = new Set<string>()
        top5Cities.forEach(([, trendData]) => {
          trendData.forEach(item => allWeeks.add(item.week))
        })
        // 确保日期按时间顺序排序
        const sortedWeeks = Array.from(allWeeks).sort((a, b) => a.localeCompare(b))
        
        // 创建合并后的数据
        const mergedData = sortedWeeks.map(week => {
          const item: any = { week }
          top5Cities.forEach(([city, trendData]) => {
            const found = trendData.find(d => d.week === week)
            item[city] = found ? found.count : 0
          })
          return item
        })
        
        return (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-semibold mb-4">Location Trends (Top 5 Cities)</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={mergedData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="week" 
                  angle={-45}
                  textAnchor="end"
                  height={100}
                />
                <YAxis />
                <Tooltip />
                <Legend />
                {top5Cities.map(([city], index) => (
                  <Line
                    key={city}
                    type="monotone"
                    dataKey={city}
                    stroke={`hsl(${(index * 360) / 5}, 70%, 50%)`}
                    strokeWidth={2}
                    name={city}
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
