'use client'

import { useEffect, useState } from 'react'
import { getTrends, type TrendsResponse } from '@/lib/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d']

export default function TrendsPage() {
  const [trends, setTrends] = useState<TrendsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [days, setDays] = useState(30)
  const [location, setLocation] = useState('') // 默认分析所有职位

  useEffect(() => {
    loadTrends()
  }, [days, location])

  const loadTrends = async () => {
    try {
      setLoading(true)
      // 确保空字符串不被发送
      const params: {
        days: number;
        location?: string;
      } = { days }
      
      if (location && location.trim()) {
        params.location = location
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

  const topKeywordsData = trends.top_keywords.slice(0, 20).map(kw => ({
    name: kw.term.length > 15 ? kw.term.substring(0, 15) + '...' : kw.term,
    fullName: kw.term,
    count: kw.count
  }))

  // 关键词增长数据（取top 10增长）
  const growthData = Object.entries(trends.keyword_growth)
    .sort((a, b) => b[1].percent_change - a[1].percent_change)
    .slice(0, 10)
    .map(([term, data]) => ({
      name: term.length > 15 ? term.substring(0, 15) + '...' : term,
      fullName: term,
      percent_change: data.percent_change,
      delta: data.delta
    }))

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">趋势分析</h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label>地点：</label>
            <select
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="p-2 border rounded"
            >
              <option value="">全部</option>
              <option value="Auckland">奥克兰</option>
              <option value="Wellington">惠灵顿</option>
              <option value="Christchurch">基督城</option>
              <option value="Sydney">悉尼</option>
              <option value="Brisbane">布里斯班</option>
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
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {roleFamilyData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
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
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {seniorityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
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
          <h2 className="text-xl font-semibold mb-4">Top 20 关键词</h2>
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

      {/* 文本列表：角色族关键词 */}
      {Object.keys(trends.top_keywords_by_role_family).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">各角色族Top关键词</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {Object.entries(trends.top_keywords_by_role_family).map(([roleFamily, keywords]) => (
              <div key={roleFamily}>
                <h3 className="font-semibold mb-2 capitalize">{roleFamily}</h3>
                <div className="flex flex-wrap gap-2">
                  {keywords.map((kw, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
                      title={`出现 ${kw.count} 次`}
                    >
                      {kw.term} ({kw.count})
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}