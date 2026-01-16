'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getJobs, type Job } from '@/lib/api'

export default function JobsPage() {
  const router = useRouter()
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState({
    role_family: '',
    seniority: ''
  })

  const roleFamilies = [
    'testing',  // 软件测试（用户最关心）
    'ai',       // AI/机器学习
    'fullstack', 
    'devops', 
    'data',
    'mobile'
  ]
  
  // 角色族中文显示名称
  const roleFamilyLabels: Record<string, string> = {
    'testing': '软件测试',
    'ai': 'AI/机器学习',
    'fullstack': '全栈',
    'devops': 'DevOps',
    'data': '数据',
    'mobile': '移动开发'
  }
  const seniorities = ['junior', 'mid', 'senior', 'staff', 'principal', 'lead', 'manager']

  useEffect(() => {
    loadJobs()
  }, [filters])
  
  // 每30秒自动刷新一次职位列表
  useEffect(() => {
    const interval = setInterval(() => {
      loadJobs()
    }, 30000) // 30秒
    
    return () => clearInterval(interval)
  }, [filters])

  const loadJobs = async () => {
    try {
      setLoading(true)
      // 确保空字符串不被发送（后端会将其视为有效值）
      const params: {
        role_family?: string;
        seniority?: string;
      } = {}
      
      if (filters.role_family && filters.role_family.trim()) {
        params.role_family = filters.role_family
      }
      if (filters.seniority && filters.seniority.trim()) {
        params.seniority = filters.seniority
      }
      
      const data = await getJobs(params)
      setJobs(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs')
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

  if (error) {
    return (
      <div className="text-red-500 py-12">
        <div className="text-xl font-semibold mb-2">错误: {error}</div>
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

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">职位列表</h1>
        <button
          onClick={() => loadJobs()}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
        >
          {loading ? '刷新中...' : '刷新'}
        </button>
      </div>
      
      {/* 过滤器 */}
      <div className="bg-gray-50 p-4 rounded-lg mb-6 flex gap-4 items-end">
        <div className="flex-1">
          <label className="block text-sm font-medium mb-1">角色族</label>
          <select
            value={filters.role_family}
            onChange={(e) => setFilters({ ...filters, role_family: e.target.value })}
            className="w-full p-2 border rounded"
          >
            <option value="">全部</option>
            {roleFamilies.map(rf => (
              <option key={rf} value={rf}>{roleFamilyLabels[rf] || rf}</option>
            ))}
          </select>
        </div>
        
        <div className="flex-1">
          <label className="block text-sm font-medium mb-1">资历级别</label>
          <select
            value={filters.seniority}
            onChange={(e) => setFilters({ ...filters, seniority: e.target.value })}
            className="w-full p-2 border rounded"
          >
            <option value="">全部</option>
            {seniorities.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        
        <button
          onClick={() => setFilters({ role_family: '', seniority: '' })}
          className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
        >
          重置
        </button>
      </div>

      {/* 职位列表 */}
      {jobs.length === 0 ? (
        <div className="text-center py-12 text-gray-500">暂无职位</div>
      ) : (
        <div className="grid gap-4">
          {jobs.map(job => (
            <div
              key={job.id}
              onClick={() => router.push(`/jobs/${job.id}`)}
              className="border rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h2 className="text-xl font-semibold mb-2">{job.title}</h2>
                  <div className="flex gap-4 text-sm text-gray-600 mb-2">
                    {job.company && job.company.trim() && job.company.toLowerCase() !== 'unknown' ? (
                      <span>{job.company}</span>
                    ) : null}
                    {job.posted_date ? (
                      <span>📅 {new Date(job.posted_date).toLocaleDateString()}</span>
                    ) : null}
                    {job.location && <span>📍 {job.location}</span>}
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    {job.role_family && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                        {job.role_family}
                      </span>
                    )}
                    {job.seniority && (
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                        {job.seniority}
                      </span>
                    )}
                    <span className={`px-2 py-1 rounded text-xs ${
                      job.status === 'applied' ? 'bg-green-100 text-green-800' :
                      job.status === 'rejected' ? 'bg-red-100 text-red-800' :
                      job.status === 'accepted' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {job.status}
                    </span>
                  </div>
                </div>
                <div className="text-right text-sm text-gray-500">
                  <div>{new Date(job.captured_at).toLocaleDateString()}</div>
                  {job.extraction && (
                    <div className="mt-1 text-xs text-green-600">
                      {job.extraction.keywords_json.keywords.length} 关键词
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}