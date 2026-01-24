'use client'

import { useEffect, useState } from 'react'
import { getTrends, type TrendsResponse } from '@/lib/api'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

interface RoleFamilyDistributionProps {
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

const roleFamilyLabels: Record<string, string> = {
  'testing': 'Software Testing',
  'ai': 'AI/Machine Learning',
  'fullstack': 'Full Stack',
  'frontend': 'Frontend/UI/UX',
  'devops': 'DevOps',
  'data': 'Data',
  'business analyst': 'Business Analyst',
  'product manager': 'Product Manager',
  'mobile': 'Mobile Development',
  '其他': 'Other'
}

const getRoleFamilyColor = (roleFamily: string): string => {
  return roleFamilyColors[roleFamily.toLowerCase()] || '#6b7280'
}

export default function RoleFamilyDistribution({ days = 30, role_family, seniority, location }: RoleFamilyDistributionProps) {
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
        <div className="text-center py-8">Loading role family distribution...</div>
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

  const roleFamilyData = Object.entries(trends.count_by_role_family).map(([name, value]) => ({
    name,
    value
  }))

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-4">Role Family Distribution</h3>
      {roleFamilyData.length > 0 ? (
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={roleFamilyData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => {
                const displayName = roleFamilyLabels[name] || name
                return `${displayName} ${(percent * 100).toFixed(0)}%`
              }}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {roleFamilyData.map((entry) => (
                <Cell key={`cell-${entry.name}`} fill={getRoleFamilyColor(entry.name)} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      ) : (
        <div className="text-center py-8 text-gray-500">No role family data available</div>
      )}
    </div>
  )
}
