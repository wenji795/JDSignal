'use client'

import { useEffect, useState } from 'react'
import { getTrends, type TrendsResponse } from '@/lib/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

// Role family colour mapping (consistent with jobs page)
const roleFamilyColors: Record<string, string> = {
  'testing': '#db2777',    // pink-600
  'ai': '#9333ea',         // purple-600
  'fullstack': '#4f46e5',  // indigo-600
  'frontend': '#0891b2',   // cyan-600
  'devops': '#059669',      // emerald-600
  'data': '#2563eb',        // blue-600
  'business analyst': '#d97706',  // amber-600
  'product manager': '#e11d48',  // rose-600
  'mobile': '#0d9488',      // teal-600
  '其他': '#6b7280'         // gray-500
}

// Seniority level colour mapping (consistent with jobs page)
const seniorityColors: Record<string, string> = {
  'graduate': '#84cc16',    // lime-500 (using slightly darker colour for visibility on pie chart)
  'junior': '#eab308',      // yellow-500
  'intermediate': '#f59e0b', // amber-500
  'mid': '#f59e0b',         // amber-500 (mapping for intermediate)
  'senior': '#f97316'       // orange-500
}

// Get role family colour
const getRoleFamilyColor = (roleFamily: string): string => {
  return roleFamilyColors[roleFamily.toLowerCase()] || '#6b7280' // gray-500 as default
}

// Get seniority level colour
const getSeniorityColor = (seniority: string): string => {
  const key = seniority.toLowerCase()
  // Handle display name to actual value mapping
  if (key === 'graduate') return seniorityColors['graduate']
  if (key === 'intermediate') return seniorityColors['intermediate']
  return seniorityColors[key] || '#6b7280' // gray-500 as default
}

export default function TrendsPage() {
  const [trends, setTrends] = useState<TrendsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [days, setDays] = useState(30)
  const [roleFamily, setRoleFamily] = useState('') // Role family filter

  // Role family options
  const roleFamilyOptions = [
    { value: '', label: 'All' },
    { value: 'testing', label: 'Software Testing' },
    { value: 'ai', label: 'AI/Machine Learning' },
    { value: 'fullstack', label: 'Full Stack' },
    { value: 'frontend', label: 'Frontend/UI/UX' },
    { value: 'devops', label: 'DevOps' },
    { value: 'data', label: 'Data' },
    { value: 'business analyst', label: 'Business Analyst' },
    { value: 'product manager', label: 'Product Manager' },
    { value: 'mobile', label: 'Mobile Development' },
    { value: '其他', label: 'Other' }
  ]
  
  // Role family display labels
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

  useEffect(() => {
    loadTrends()
  }, [days, roleFamily])

  const loadTrends = async () => {
    try {
      setLoading(true)
      // Ensure empty strings are not sent
      const params: {
        days: number;
        role_family?: string;
      } = { days }
      
      if (roleFamily && roleFamily.trim()) {
        params.role_family = roleFamily
      }
      
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
      <div className="text-center py-12">
        <div className="text-lg mb-2">Loading...</div>
        <div className="text-sm text-gray-500">Connecting to backend API (http://127.0.0.1:8000)</div>
      </div>
    )
  }

  if (error || !trends) {
    return (
      <div className="text-red-500 py-12">
        <div className="text-xl font-semibold mb-2">Error: {error || 'Failed to load trends'}</div>
        <div className="text-sm text-gray-600 mt-4">
          <p>Please check:</p>
          <ul className="list-disc list-inside mt-2">
            <li>Is the backend service running at http://127.0.0.1:8000</li>
            <li>Run command: <code className="bg-gray-100 px-2 py-1 rounded">cd backend && uvicorn app.main:app --reload</code></li>
            <li>Check browser console for more error information</li>
          </ul>
        </div>
      </div>
    )
  }

  // Prepare chart data
  const roleFamilyData = Object.entries(trends.count_by_role_family).map(([name, value]) => ({
    name,
    value
  }))

  const seniorityData = Object.entries(trends.count_by_seniority).map(([name, value]) => ({
    name,
    value
  }))

  // Show different top 20 keywords based on selected role family
  const keywordsToShow = roleFamily && trends.selected_role_family_top_keywords 
    ? trends.selected_role_family_top_keywords 
    : trends.top_keywords
  
  const topKeywordsData = keywordsToShow.slice(0, 20).map(kw => ({
    name: kw.term.length > 15 ? kw.term.substring(0, 15) + '...' : kw.term,
    fullName: kw.term,
    count: kw.count
  }))
  
  // Chart titles
  const roleFamilyLabel = roleFamilyOptions.find(opt => opt.value === roleFamily)?.label || roleFamily
  const keywordsChartTitle = roleFamily && trends.selected_role_family_top_keywords
    ? `${roleFamilyLabel} - Top 20 Keywords`
    : 'Top 20 Keywords (All)'

  // Keyword growth data (top 10 growth) - deprecated, using monthly_comparison instead
  const growthData: Array<{
    name: string
    fullName: string
    percent_change: number
    delta: number
  }> = []

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Trend Analysis</h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label>Role Family: </label>
            <select
              value={roleFamily}
              onChange={(e) => setRoleFamily(e.target.value)}
              className="p-2 border rounded"
            >
              {roleFamilyOptions.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label>Time Window: </label>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="p-2 border rounded"
            >
              <option value={7}>7 days</option>
              <option value={30}>30 days</option>
              <option value={60}>60 days</option>
              <option value={90}>90 days</option>
            </select>
          </div>
        </div>
      </div>

      {/* Total Jobs */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold text-blue-800">{trends.total_jobs}</div>
            <div className="text-blue-600">Total Jobs (with extraction)</div>
          </div>
          {trends.extraction_coverage && trends.extraction_coverage.total_jobs_all > trends.extraction_coverage.total_jobs_with_extraction && (
            <div className="text-right">
              <div className="text-sm text-gray-600">
                <div>Total: {trends.extraction_coverage.total_jobs_all}</div>
                <div className={`font-semibold ${trends.extraction_coverage.coverage_rate < 90 ? 'text-orange-600' : 'text-green-600'}`}>
                  Coverage: {trends.extraction_coverage.coverage_rate}%
                </div>
                {trends.extraction_coverage.coverage_rate < 100 && (
                  <div className="text-xs text-gray-500 mt-1">
                    {trends.extraction_coverage.total_jobs_all - trends.extraction_coverage.total_jobs_with_extraction} jobs pending extraction
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
        {trends.extraction_coverage && trends.extraction_coverage.coverage_rate < 100 && (
          <div className="mt-4 text-sm text-gray-600 bg-yellow-50 border border-yellow-200 rounded p-3">
            <p className="font-semibold text-yellow-800 mb-1">⚠️ 注意：数据可能不完整</p>
            <p className="text-yellow-700">
              当前有 {trends.extraction_coverage.total_jobs_all - trends.extraction_coverage.total_jobs_with_extraction} 个职位的关键词提取尚未完成。
              分析结果仅包含已完成提取的 {trends.extraction_coverage.total_jobs_with_extraction} 个职位（覆盖率 {trends.extraction_coverage.coverage_rate}%）。
              请等待提取完成后再查看完整分析结果。
            </p>
          </div>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-6">
        {/* Role Family Distribution */}
        {roleFamilyData.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Role Family Distribution</h2>
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
          </div>
        )}

        {/* Seniority Level Distribution */}
        {seniorityData.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Seniority Level Distribution</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={seniorityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => {
                    // Display friendly names
                    const displayName = name === 'junior' ? 'Junior' :
                                       name === 'mid' ? 'Intermediate' :
                                       name === 'senior' ? 'Senior' :
                                       name.charAt(0).toUpperCase() + name.slice(1)
                    return `${displayName} ${(percent * 100).toFixed(0)}%`
                  }}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {seniorityData.map((entry) => (
                    <Cell key={`cell-${entry.name}`} fill={getSeniorityColor(entry.name)} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Top Keywords */}
      {topKeywordsData.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">{keywordsChartTitle}</h2>
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
        </div>
      )}

      {/* Keyword Growth */}
      {growthData.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Keyword Growth Trends (Top 10)</h2>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={growthData}>
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
                    const data = payload[0].payload
                    return (
                      <div className="bg-white p-2 border rounded shadow">
                        <p className="font-semibold">{data.fullName}</p>
                        <p>Growth Rate: {data.percent_change.toFixed(2)}%</p>
                        <p>Change: {data.delta > 0 ? '+' : ''}{data.delta}</p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Bar 
                dataKey="percent_change" 
                fill={growthData.some(d => d.percent_change < 0) ? "#ff8042" : "#00c49f"} 
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Last Month vs This Month Keyword Comparison - Overall Top 7 */}
      {trends.monthly_comparison && trends.monthly_comparison.comparison.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Last Month vs This Month Keyword Comparison (Overall Top 7)</h2>
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
                {trends.monthly_comparison.comparison.map((item, idx) => {
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
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Monthly Comparison by Role Family - Top 5 per Role Family */}
      {trends.monthly_comparison && trends.monthly_comparison.by_role_family && Object.keys(trends.monthly_comparison.by_role_family).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Last Month vs This Month Keyword Comparison by Role Family (Top 5)</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {Object.entries(trends.monthly_comparison.by_role_family).map(([roleFamily, comparisons]) => {
              if (comparisons.length === 0) return null
              
              return (
                <div key={roleFamily} className="border rounded-lg p-4">
                  <h3 className="font-semibold mb-3 text-lg" style={{ color: getRoleFamilyColor(roleFamily) }}>
                    {roleFamilyLabels[roleFamily] || roleFamily}
                  </h3>
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
                        {comparisons.map((item, idx) => {
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
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Text List: Role Family Keywords */}
      {Object.keys(trends.top_keywords_by_role_family).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Top Keywords by Role Family</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {Object.entries(trends.top_keywords_by_role_family).map(([roleFamily, keywords]) => {
              // Get role family background and text colours
              const bgColor = roleFamilyColors[roleFamily.toLowerCase()] || '#4f46e5'
              // Use white text on dark background
              const textColor = '#ffffff'
              
              return (
                <div key={roleFamily}>
                  <h3 className="font-semibold mb-2">{roleFamilyLabels[roleFamily] || roleFamily}</h3>
                  <div className="flex flex-wrap gap-2">
                    {keywords.map((kw, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 rounded text-xs font-medium"
                        style={{ backgroundColor: bgColor, color: textColor }}
                        title={`Occurred ${kw.count} times`}
                      >
                        {kw.term} ({kw.count})
                      </span>
                    ))}
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