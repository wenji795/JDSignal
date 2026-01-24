'use client'

import { useEffect, useState } from 'react'
import { getExperienceAnalysis, type ExperienceAnalysisResponse } from '@/lib/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'

interface ExperienceAnalysisProps {
  days?: number
  role_family?: string
  seniority?: string
  location?: string
}

export default function ExperienceAnalysis({ days = 30, role_family, seniority, location }: ExperienceAnalysisProps) {
  const [data, setData] = useState<ExperienceAnalysisResponse | null>(null)
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

      const result = await getExperienceAnalysis(params)
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load experience analysis')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-8">Loading experience analysis...</div>
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
      {/* Experience Distribution */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">
          Experience Distribution ({data.jobs_with_experience} jobs with experience requirements)
        </h3>
        {data.experience_distribution.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.experience_distribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-8 text-gray-500">No experience data available</div>
        )}
      </div>

      {/* Experience Trends */}
      {data.experience_trends.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-semibold mb-4">Average Experience Requirements Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data.experience_trends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="week" 
                angle={-45}
                textAnchor="end"
                height={100}
              />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="average_years" stroke="#8884d8" strokeWidth={2} name="Average Years" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
