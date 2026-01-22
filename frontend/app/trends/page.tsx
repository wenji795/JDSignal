'use client'

import { useEffect, useState } from 'react'
import { getTrends, type TrendsResponse } from '@/lib/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

// 角色族颜色映射（与jobs页面保持一致）
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

// 资历级别颜色映射（与jobs页面保持一致）
const seniorityColors: Record<string, string> = {
  'graduate': '#84cc16',    // lime-500 (使用稍深一点的颜色以便在饼图上可见)
  'junior': '#eab308',      // yellow-500
  'intermediate': '#f59e0b', // amber-500
  'mid': '#f59e0b',         // amber-500 (intermediate的映射)
  'senior': '#f97316'       // orange-500
}

// 获取角色族颜色
const getRoleFamilyColor = (roleFamily: string): string => {
  return roleFamilyColors[roleFamily.toLowerCase()] || '#6b7280' // gray-500作为默认
}

// 获取资历级别颜色
const getSeniorityColor = (seniority: string): string => {
  const key = seniority.toLowerCase()
  // 处理显示名称到实际值的映射
  if (key === 'graduate') return seniorityColors['graduate']
  if (key === 'intermediate') return seniorityColors['intermediate']
  return seniorityColors[key] || '#6b7280' // gray-500作为默认
}

export default function TrendsPage() {
  const [trends, setTrends] = useState<TrendsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [days, setDays] = useState(30)
  const [roleFamily, setRoleFamily] = useState('') // 角色族筛选

  // 角色族选项
  const roleFamilyOptions = [
    { value: '', label: '全部' },
    { value: 'testing', label: '软件测试' },
    { value: 'ai', label: 'AI/机器学习' },
    { value: 'fullstack', label: '全栈' },
    { value: 'frontend', label: '前端/UI/UX' },
    { value: 'devops', label: 'DevOps' },
    { value: 'data', label: '数据' },
    { value: 'business analyst', label: '业务分析师' },
    { value: 'product manager', label: '产品经理' },
    { value: 'mobile', label: '移动开发' },
    { value: '其他', label: '其他' }
  ]
  
  // 角色族中文显示名称映射
  const roleFamilyLabels: Record<string, string> = {
    'testing': '软件测试',
    'ai': 'AI/机器学习',
    'fullstack': '全栈',
    'frontend': '前端/UI/UX',
    'devops': 'DevOps',
    'data': '数据',
    'business analyst': '业务分析师',
    'product manager': '产品经理',
    'mobile': '移动开发',
    '其他': '其他'
  }

  useEffect(() => {
    loadTrends()
  }, [days, roleFamily])

  const loadTrends = async () => {
    try {
      setLoading(true)
      // 确保空字符串不被发送
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
        <div className="text-lg mb-2">加载中...</div>
        <div className="text-sm text-gray-500">正在连接后端API (http://127.0.0.1:8000)</div>
      </div>
    )
  }

  if (error || !trends) {
    return (
      <div className="text-red-500 py-12">
        <div className="text-xl font-semibold mb-2">错误: {error || 'Failed to load trends'}</div>
        <div className="text-sm text-gray-600 mt-4">
          <p>请检查：</p>
          <ul className="list-disc list-inside mt-2">
            <li>后端服务是否运行在 http://127.0.0.1:8000</li>
            <li>运行命令: <code className="bg-gray-100 px-2 py-1 rounded">cd backend && uvicorn app.main:app --reload</code></li>
            <li>浏览器控制台是否有更多错误信息</li>
          </ul>
        </div>
      </div>
    )
  }

  // 准备图表数据
  const roleFamilyData = Object.entries(trends.count_by_role_family).map(([name, value]) => ({
    name,
    value
  }))

  const seniorityData = Object.entries(trends.count_by_seniority).map(([name, value]) => ({
    name,
    value
  }))

  // 根据是否选择了角色族，显示不同的top20关键词
  const keywordsToShow = roleFamily && trends.selected_role_family_top_keywords 
    ? trends.selected_role_family_top_keywords 
    : trends.top_keywords
  
  const topKeywordsData = keywordsToShow.slice(0, 20).map(kw => ({
    name: kw.term.length > 15 ? kw.term.substring(0, 15) + '...' : kw.term,
    fullName: kw.term,
    count: kw.count
  }))
  
  // 图表标题
  const roleFamilyLabel = roleFamilyOptions.find(opt => opt.value === roleFamily)?.label || roleFamily
  const keywordsChartTitle = roleFamily && trends.selected_role_family_top_keywords
    ? `${roleFamilyLabel} - Top 20 关键词`
    : 'Top 20 关键词（全部）'

  // 关键词增长数据（取top 10增长）- 已废弃，使用monthly_comparison代替
  const growthData: Array<{
    name: string
    fullName: string
    percent_change: number
    delta: number
  }> = []

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">趋势分析</h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label>角色族：</label>
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
            <label>时间窗口：</label>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="p-2 border rounded"
            >
              <option value={7}>7天</option>
              <option value={30}>30天</option>
              <option value={60}>60天</option>
              <option value={90}>90天</option>
            </select>
          </div>
        </div>
      </div>

      {/* 总职位数 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
        <div className="text-2xl font-bold text-blue-800">{trends.total_jobs}</div>
        <div className="text-blue-600">总职位数</div>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-6">
        {/* 角色族分布 */}
        {roleFamilyData.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">角色族分布</h2>
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

        {/* 资历级别分布 */}
        {seniorityData.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">资历级别分布</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={seniorityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => {
                    // 显示友好的名称
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

      {/* Top关键词 */}
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
                        <p>出现次数: {payload[0].value}</p>
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

      {/* 关键词增长 */}
      {growthData.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">关键词增长趋势（Top 10）</h2>
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
                        <p>增长率: {data.percent_change.toFixed(2)}%</p>
                        <p>变化量: {data.delta > 0 ? '+' : ''}{data.delta}</p>
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

      {/* 上月vs本月关键词比较 - 总体Top 7 */}
      {trends.monthly_comparison && trends.monthly_comparison.comparison.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">上月 vs 本月关键词对比（总体 Top 7）</h2>
          <div className="mb-4 text-sm text-gray-600">
            <p>
              本月 ({new Date(trends.monthly_comparison.current_month.start).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long' })}): 
              <span className="font-semibold ml-1">{trends.monthly_comparison.current_month.job_count}</span> 个职位
            </p>
            <p>
              上月 ({new Date(trends.monthly_comparison.last_month.start).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long' })}): 
              <span className="font-semibold ml-1">{trends.monthly_comparison.last_month.job_count}</span> 个职位
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">关键词</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">上月</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">本月</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">变化</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">变化率</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
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
                    'new': '新增',
                    'increased': '增长',
                    'decreased': '下降',
                    'unchanged': '不变'
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

      {/* 按角色族的月度对比 - 每个角色族Top 5 */}
      {trends.monthly_comparison && trends.monthly_comparison.by_role_family && Object.keys(trends.monthly_comparison.by_role_family).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">各角色族上月 vs 本月关键词对比（Top 5）</h2>
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
                          <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase">关键词</th>
                          <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase">上月</th>
                          <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase">本月</th>
                          <th className="px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase">变化</th>
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
                            'new': '新增',
                            'increased': '增长',
                            'decreased': '下降',
                            'unchanged': '不变'
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

      {/* 文本列表：角色族关键词 */}
      {Object.keys(trends.top_keywords_by_role_family).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">各角色族Top关键词</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {Object.entries(trends.top_keywords_by_role_family).map(([roleFamily, keywords]) => {
              // 获取角色族的背景色和文字色
              const bgColor = roleFamilyColors[roleFamily.toLowerCase()] || '#4f46e5'
              // 深色背景使用白色文字
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
                        title={`出现 ${kw.count} 次`}
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