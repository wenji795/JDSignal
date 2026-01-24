'use client'

import { useEffect, useState } from 'react'
import { getEducationAnalysis, type EducationAnalysisResponse } from '@/lib/api'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface EducationAnalysisProps {
  days?: number
  role_family?: string
  seniority?: string
  location?: string
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8']

export default function EducationAnalysis({ days = 30, role_family, seniority, location }: EducationAnalysisProps) {
  const [data, setData] = useState<EducationAnalysisResponse | null>(null)
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

      const result = await getEducationAnalysis(params)
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load education analysis')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-8">Loading education analysis...</div>
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
      {/* Degree Distribution */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">
          Degree Requirements Distribution ({data.jobs_with_degree} jobs with degree requirements)
        </h3>
        {data.degree_distribution.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data.degree_distribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ degree, percent }) => `${degree} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
              >
                {data.degree_distribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-8 text-gray-500">No degree data available</div>
        )}
      </div>

      {/* Certifications Distribution */}
      {data.certifications_distribution.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-semibold mb-4">
            Top Certifications ({data.jobs_with_certifications} jobs with certifications)
          </h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={data.certifications_distribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="certification" 
                angle={-45}
                textAnchor="end"
                height={100}
              />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
