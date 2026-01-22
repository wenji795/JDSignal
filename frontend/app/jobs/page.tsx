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
    'testing',  // Software Testing
    'ai',       // AI/Machine Learning
    'fullstack', 
    'frontend', // Frontend/UI/UX
    'devops', 
    'data',
    'business analyst', // Business Analyst
    'product manager', // Product Manager
    'mobile',
    '其他'      // Other roles
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
  // Only show: graduate, junior, intermediate (mapped to mid), senior, manager, lead, architect, unknown
  const seniorities = ['graduate', 'junior', 'intermediate', 'senior', 'manager', 'lead', 'architect', 'unknown']
  
  // Seniority level display labels
  const seniorityLabels: Record<string, string> = {
    'graduate': 'Graduate',
    'junior': 'Junior',
    'intermediate': 'Intermediate',
    'senior': 'Senior',
    'manager': 'Manager',
    'lead': 'Lead',
    'architect': 'Architect',
    'unknown': 'Unknown'
  }
  
  // Role family colour mapping (dark background + white text)
  const roleFamilyColors: Record<string, string> = {
    'testing': 'bg-pink-600 text-white',
    'ai': 'bg-purple-600 text-white',
    'fullstack': 'bg-indigo-600 text-white',
    'frontend': 'bg-cyan-600 text-white',
    'devops': 'bg-emerald-600 text-white',
    'data': 'bg-blue-600 text-white',
    'business analyst': 'bg-amber-600 text-white',
    'product manager': 'bg-rose-600 text-white',
    'mobile': 'bg-teal-600 text-white',
    '其他': 'bg-gray-600 text-white'
  }
  
  // Seniority level colour mapping (light background + dark text)
  const seniorityColors: Record<string, string> = {
    'graduate': 'bg-lime-100 text-lime-900',
    'junior': 'bg-yellow-100 text-yellow-900',
    'intermediate': 'bg-amber-100 text-amber-900',
    'senior': 'bg-orange-100 text-orange-900',
    'manager': 'bg-purple-100 text-purple-900',
    'lead': 'bg-indigo-100 text-indigo-900',
    'architect': 'bg-cyan-100 text-cyan-900',
    'unknown': 'bg-gray-100 text-gray-900',
    'mid': 'bg-amber-100 text-amber-900' // mapping for intermediate
  }

  useEffect(() => {
    loadJobs()
  }, [filters])
  
  // Auto-refresh job list every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      loadJobs()
    }, 30000) // 30 seconds
    
    return () => clearInterval(interval)
  }, [filters])

  const loadJobs = async () => {
    try {
      setLoading(true)
      // Ensure empty strings are not sent (backend will treat them as valid values)
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
        <div className="text-lg mb-2">Loading...</div>
        <div className="text-sm text-gray-500">Connecting to backend API (http://127.0.0.1:8000)</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-red-500 py-12">
        <div className="text-xl font-semibold mb-2">Error: {error}</div>
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

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Job List</h1>
        <button
          onClick={() => loadJobs()}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>
      
      {/* Filters */}
      <div className="bg-gray-50 p-4 rounded-lg mb-6 flex gap-4 items-end">
        <div className="flex-1">
          <label className="block text-sm font-medium mb-1">Role Family</label>
          <select
            value={filters.role_family}
            onChange={(e) => setFilters({ ...filters, role_family: e.target.value })}
            className="w-full p-2 border rounded"
          >
            <option value="">All</option>
            {roleFamilies.map(rf => (
              <option key={rf} value={rf}>{roleFamilyLabels[rf] || rf}</option>
            ))}
          </select>
        </div>
        
        <div className="flex-1">
          <label className="block text-sm font-medium mb-1">Seniority Level</label>
          <select
            value={filters.seniority}
            onChange={(e) => setFilters({ ...filters, seniority: e.target.value })}
            className="w-full p-2 border rounded"
          >
            <option value="">All</option>
            {seniorities.map(s => (
              <option key={s} value={s === 'intermediate' ? 'mid' : s}>
                {seniorityLabels[s] || s}
              </option>
            ))}
          </select>
        </div>
        
        <button
          onClick={() => setFilters({ role_family: '', seniority: '' })}
          className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
        >
          Reset
        </button>
      </div>

      {/* Job list */}
      {jobs.length === 0 ? (
        <div className="text-center py-12 text-gray-500">No jobs available</div>
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
                      <span className={`px-2 py-1 rounded text-xs font-medium ${roleFamilyColors[job.role_family] || 'bg-gray-600 text-white'}`}>
                        {roleFamilyLabels[job.role_family] || job.role_family}
                      </span>
                    )}
                    {job.seniority && (() => {
                      const displaySeniority = job.seniority === 'graduate' ? 'Graduate' :
                                               job.seniority === 'junior' ? 'Junior' :
                                               job.seniority === 'mid' ? 'Intermediate' :
                                               job.seniority === 'senior' ? 'Senior' :
                                               job.seniority === 'manager' ? 'Manager' :
                                               job.seniority === 'lead' ? 'Lead' :
                                               job.seniority === 'architect' ? 'Architect' :
                                               job.seniority === 'unknown' ? 'Unknown' :
                                               job.seniority;
                      const colorKey = displaySeniority.toLowerCase() === 'graduate' ? 'graduate' :
                                       displaySeniority.toLowerCase() === 'intermediate' ? 'intermediate' :
                                       displaySeniority.toLowerCase() === 'unknown' ? 'unknown' :
                                       job.seniority;
                      return (
                        <span className={`px-2 py-1 rounded text-xs font-medium ${seniorityColors[colorKey] || 'bg-gray-100 text-gray-900'}`}>
                          {displaySeniority}
                        </span>
                      );
                    })()}
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
                      {job.extraction.keywords_json.keywords.length} keywords
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