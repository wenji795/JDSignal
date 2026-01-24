'use client'

import { useEffect, useState } from 'react'
import { getTrends, type TrendsResponse } from '@/lib/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface KeywordStatsProps {
  days?: number
  role_family?: string
  seniority?: string
  location?: string
}

export default function KeywordStats({ days = 30, role_family, seniority, location }: KeywordStatsProps) {
  const [trends, setTrends] = useState<TrendsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadTrends()
  }, [days, role_family, seniority, location])

  const loadTrends = async () => {
    try {
      setLoading(true)
      const params: any = { days }
      if (role_family) params.role_family = role_family
      if (seniority) params.seniority = seniority
      if (location) params.location = location

      const data = await getTrends(params)
      setTrends(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load trends')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-8">Loading keyword statistics...</div>
      </div>
    )
  }

  if (error || !trends) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-red-500">Error: {error || 'Failed to load data'}</div>
      </div>
    )
  }

  // Show different top 20 keywords based on selected role family
  const keywordsToShow = role_family && trends.selected_role_family_top_keywords 
    ? trends.selected_role_family_top_keywords 
    : trends.top_keywords
  
  const topKeywordsData = keywordsToShow.slice(0, 20).map(kw => ({
    name: kw.term.length > 15 ? kw.term.substring(0, 15) + '...' : kw.term,
    fullName: kw.term,
    count: kw.count
  }))

  const roleFamilyLabel = role_family || 'All'
  const keywordsChartTitle = role_family && trends.selected_role_family_top_keywords
    ? `${roleFamilyLabel} - Top 20 Keywords`
    : 'Top 20 Keywords (All)'

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-4">{keywordsChartTitle}</h3>
      {topKeywordsData.length > 0 ? (
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={topKeywordsData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="name" 
              angle={-45}
              textAnchor="end"
              height={100}
            />
            <YAxis />
            <Tooltip 
              content={({ active, payload }) => {
                if (active && payload && payload[0]) {
                  return (
                    <div className="bg-white p-2 border rounded shadow">
                      <p className="font-semibold">{payload[0].payload.fullName}</p>
                      <p>Occurrences: {payload[0].value}</p>
                    </div>
                  )
                }
                return null
              }}
            />
            <Bar dataKey="count" fill="#8884d8" />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <div className="text-center py-8 text-gray-500">No keyword data available</div>
      )}
    </div>
  )
}
