'use client'

import { useEffect, useState } from 'react'
import { getTrends, type TrendsResponse } from '@/lib/api'

interface MonthlyComparisonProps {
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

export default function MonthlyComparison({ days = 30, role_family, seniority, location }: MonthlyComparisonProps) {
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
        <div className="text-center py-8">Loading monthly comparison...</div>
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

  if (!trends.monthly_comparison || trends.monthly_comparison.comparison.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Monthly Keyword Comparison</h3>
        <div className="text-center py-8 text-gray-500">No monthly comparison data available</div>
      </div>
    )
  }

  const statusColors = {
    'new': 'bg-green-100 text-green-800',
    'increased': 'bg-blue-100 text-blue-800',
    'decreased': 'bg-red-100 text-red-800',
    'unchanged': 'bg-gray-100 text-gray-800'
  }

  const statusLabels = {
    'new': 'New',
    'increased': 'Increased',
    'decreased': 'Decreased',
    'unchanged': 'Unchanged'
  }

  return (
    <div className="space-y-6">
      {/* Overall Top 7 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">
          Last Month vs This Month Keyword Comparison (Overall Top 7)
        </h3>
        <div className="mb-4 text-sm text-gray-600">
          <p>
            This Month ({new Date(trends.monthly_comparison.current_month.start).toLocaleDateString('en-GB', { year: 'numeric', month: 'long' })}): 
            <span className="font-semibold ml-1">{trends.monthly_comparison.current_month.job_count}</span> jobs
          </p>
          <p>
            Last Month ({new Date(trends.monthly_comparison.last_month.start).toLocaleDateString('en-GB', { year: 'numeric', month: 'long' })}): 
            <span className="font-semibold ml-1">{trends.monthly_comparison.last_month.job_count}</span> jobs
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Keyword</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Month</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">This Month</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Change</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Change Rate</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {trends.monthly_comparison.comparison.map((item, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{item.term}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{item.last_month_count}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 font-semibold">{item.current_month_count}</td>
                  <td className={`px-4 py-3 whitespace-nowrap text-sm font-semibold ${item.delta > 0 ? 'text-green-600' : item.delta < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                    {item.delta > 0 ? '+' : ''}{item.delta}
                  </td>
                  <td className={`px-4 py-3 whitespace-nowrap text-sm ${item.percent_change > 0 ? 'text-green-600' : item.percent_change < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                    {item.percent_change > 0 ? '+' : ''}{item.percent_change.toFixed(1)}%
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColors[item.status]}`}>
                      {statusLabels[item.status]}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* By Role Family */}
      {trends.monthly_comparison.by_role_family && Object.keys(trends.monthly_comparison.by_role_family).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-semibold mb-4">Monthly Comparison by Role Family (Top 5)</h3>
          <div className="grid md:grid-cols-2 gap-6">
            {Object.entries(trends.monthly_comparison.by_role_family).map(([roleFamily, comparisons]) => {
              if (comparisons.length === 0) return null
              
              return (
                <div key={roleFamily} className="border rounded-lg p-4">
                  <h4 className="font-semibold mb-3 text-lg" style={{ color: getRoleFamilyColor(roleFamily) }}>
                    {roleFamilyLabels[roleFamily] || roleFamily}
                  </h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase">Keyword</th>
                          <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase">Last Month</th>
                          <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase">This Month</th>
                          <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase">Change</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {comparisons.map((item, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-2 py-2 whitespace-nowrap text-sm font-medium text-gray-900">{item.term}</td>
                            <td className="px-2 py-2 whitespace-nowrap text-sm text-gray-500">{item.last_month_count}</td>
                            <td className="px-2 py-2 whitespace-nowrap text-sm text-gray-900 font-semibold">{item.current_month_count}</td>
                            <td className={`px-2 py-2 whitespace-nowrap text-sm font-semibold ${item.delta > 0 ? 'text-green-600' : item.delta < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                              {item.delta > 0 ? '+' : ''}{item.delta}
                              <span className={`ml-2 px-1.5 py-0.5 text-xs rounded-full ${statusColors[item.status]}`}>
                                {statusLabels[item.status]}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
