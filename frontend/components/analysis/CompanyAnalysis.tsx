'use client'

import { useEffect, useState } from 'react'
import { getCompanyAnalysis, type CompanyAnalysisResponse } from '@/lib/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Legend } from 'recharts'

interface CompanyAnalysisProps {
  days?: number
  role_family?: string
  seniority?: string
  location?: string
}

export default function CompanyAnalysis({ days = 30, role_family, seniority, location }: CompanyAnalysisProps) {
  const [data, setData] = useState<CompanyAnalysisResponse | null>(null)
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

      const result = await getCompanyAnalysis(params)
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load company analysis')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-8">Loading company analysis...</div>
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
      {/* Top Companies */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Top 20 Companies</h3>
        {data.top_companies.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={data.top_companies}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="company" 
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
          <div className="text-center py-8 text-gray-500">No company data available</div>
        )}
      </div>

      {/* Company Trends */}
      {Object.keys(data.company_trends).length > 0 && (() => {
        const companies = Object.entries(data.company_trends)
        
        // 合并所有日期，创建统一的数据结构
        const allWeeks = new Set<string>()
        companies.forEach(([, trendData]) => {
          trendData.forEach(item => allWeeks.add(item.week))
        })
        // 确保日期按时间顺序排序
        const sortedWeeks = Array.from(allWeeks).sort((a, b) => a.localeCompare(b))
        
        // 创建合并后的数据
        const mergedData = sortedWeeks.map(week => {
          const item: any = { week }
          companies.forEach(([company, trendData]) => {
            const found = trendData.find(d => d.week === week)
            item[company] = found ? found.count : 0
          })
          return item
        })
        
        return (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-semibold mb-4">Company Hiring Trends (Top 10)</h3>
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
                {companies.map(([company], index) => (
                  <Line
                    key={company}
                    type="monotone"
                    dataKey={company}
                    stroke={`hsl(${(index * 360) / companies.length}, 70%, 50%)`}
                    strokeWidth={2}
                    name={company.length > 20 ? company.substring(0, 20) + '...' : company}
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
