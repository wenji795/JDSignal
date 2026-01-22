'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

const API_BASE_URL = 'http://127.0.0.1:8000'

export default function ManualJobPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    title: '',
    company: '',
    location: '',
    url: '',
    jd_text: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(false)

    try {
      const response = await fetch(`${API_BASE_URL}/manual-job`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: formData.title,
          company: formData.company || undefined,
          location: formData.location || undefined,
          url: formData.url || undefined,
          jd_text: formData.jd_text
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setSuccess(true)
      setJobId(data.id)
      
      // Redirect to job detail page after 3 seconds
      setTimeout(() => {
        router.push(`/jobs/${data.id}`)
      }, 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submission failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto mt-8">
      <h1 className="text-3xl font-bold mb-6">Manual Job JD Input</h1>
      
      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <p className="text-green-800 font-semibold">✓ Job successfully created!</p>
          <p className="text-green-600 text-sm mt-1">
            Redirecting to job detail page... (auto-redirect in 3 seconds)
          </p>
          {jobId && (
            <p className="text-green-600 text-sm mt-1">
              Job ID: {jobId}
            </p>
          )}
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800 font-semibold">✗ Error</p>
          <p className="text-red-600 text-sm mt-1">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Job Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full p-2 border rounded"
              required
              placeholder="e.g., Senior Python Developer"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Company Name</label>
            <input
              type="text"
              value={formData.company}
              onChange={(e) => setFormData({ ...formData, company: e.target.value })}
              className="w-full p-2 border rounded"
              placeholder="e.g., TechCorp Inc"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Location</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              className="w-full p-2 border rounded"
              placeholder="e.g., Auckland, New Zealand"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Job URL (Optional)</label>
            <input
              type="url"
              value={formData.url}
              onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              className="w-full p-2 border rounded"
              placeholder="e.g., https://www.seek.co.nz/job/12345678"
            />
            <p className="text-xs text-gray-500 mt-1">
              If URL is provided, the system will check for duplicates to avoid repetition
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Job Description (JD Text) <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.jd_text}
              onChange={(e) => setFormData({ ...formData, jd_text: e.target.value })}
              className="w-full p-2 border rounded"
              rows={15}
              required
              placeholder="Paste job description text..."
            />
            <p className="text-xs text-gray-500 mt-1">
              The system will automatically extract keywords, infer role family and seniority level
            </p>
          </div>

          <div className="flex gap-4">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              {loading ? 'Submitting...' : 'Submit'}
            </button>
            <button
              type="button"
              onClick={() => router.push('/jobs')}
              className="px-6 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
            >
              Back to Job List
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
