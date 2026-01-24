'use client'

import { useEffect, useState } from 'react'
import { getIndustryAnalysis, type IndustryAnalysisResponse } from '@/lib/api'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Legend } from 'recharts'

interface IndustryAnalysisProps {
  days?: number
  role_family?: string
  seniority?: string
  location?: string
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#ff7300']

export default function IndustryAnalysis({ days = 30, role_family, seniority, location }: IndustryAnalysisProps) {
  const [data, setData] = useState<IndustryAnalysisResponse | null>(null)
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

      const result = await getIndustryAnalysis(params)
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load industry analysis')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-8">Loading industry analysis...</div>
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
      {/* Industry Distribution */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Industry Distribution (Top 20)</h3>
        {data.industry_distribution.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={data.industry_distribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="industry" 
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
          <div className="text-center py-8 text-gray-500">No industry data available</div>
        )}
      </div>

      {/* Industry Trends */}
      {Object.keys(data.industry_trends).length > 0 && (() => {
        const topIndustries = Object.entries(data.industry_trends).slice(0, 5)
        
        // 合并所有日期
        const allWeeks = new Set<string>()
        topIndustries.forEach(([, trendData]) => {
          trendData.forEach(item => allWeeks.add(item.week))
        })
        const sortedWeeks = Array.from(allWeeks).sort((a, b) => a.localeCompare(b))
        
        // 创建合并后的数据
        const mergedData = sortedWeeks.map(week => {
          const item: any = { week }
          topIndustries.forEach(([industry, trendData]) => {
            const found = trendData.find(d => d.week === week)
            item[industry] = found ? found.count : 0
          })
          return item
        })
        
        return (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-semibold mb-4">Industry Trends (Top 5)</h3>
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
                {topIndustries.map(([industry], index) => (
                  <Line
                    key={industry}
                    type="monotone"
                    dataKey={industry}
                    stroke={COLORS[index % COLORS.length]}
                    strokeWidth={2}
                    name={industry.length > 30 ? industry.substring(0, 30) + '...' : industry}
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
