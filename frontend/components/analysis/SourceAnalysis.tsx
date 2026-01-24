'use client'

import { useEffect, useState } from 'react'
import { getSourceAnalysis, type SourceAnalysisResponse } from '@/lib/api'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface SourceAnalysisProps {
  days?: number
  role_family?: string
  seniority?: string
  location?: string
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8']

export default function SourceAnalysis({ days = 30, role_family, seniority, location }: SourceAnalysisProps) {
  const [data, setData] = useState<SourceAnalysisResponse | null>(null)
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

      const result = await getSourceAnalysis(params)
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load source analysis')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-8">Loading source analysis...</div>
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

  // 准备质量对比数据
  const qualityData = Object.entries(data.source_quality).map(([source, quality]) => ({
    source,
    ...quality
  }))

  return (
    <div className="space-y-6">
      {/* Source Distribution */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Data Source Distribution</h3>
        {data.source_distribution.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data.source_distribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ source, percent }) => `${source} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
              >
                {data.source_distribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-8 text-gray-500">No source data available</div>
        )}
      </div>

      {/* Source Quality */}
      {qualityData.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-semibold mb-4">Extraction Success Rate by Source</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={qualityData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="source" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="success_rate" fill="#8884d8" name="Success Rate (%)" />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-4 text-sm text-gray-600">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Source</th>
                  <th className="text-right py-2">Total Jobs</th>
                  <th className="text-right py-2">Extracted</th>
                  <th className="text-right py-2">Success Rate</th>
                </tr>
              </thead>
              <tbody>
                {qualityData.map((item) => (
                  <tr key={item.source} className="border-b">
                    <td className="py-2">{item.source}</td>
                    <td className="text-right py-2">{item.total_jobs}</td>
                    <td className="text-right py-2">{item.extracted_jobs}</td>
                    <td className="text-right py-2 font-semibold">{item.success_rate}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
