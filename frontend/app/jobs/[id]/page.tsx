'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { getJob, getExtraction, type Job, type Extraction } from '@/lib/api'

export default function JobDetailPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = params.id as string
  
  const [job, setJob] = useState<Job | null>(null)
  const [extraction, setExtraction] = useState<Extraction | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showJD, setShowJD] = useState(false)

  useEffect(() => {
    loadJobData()
  }, [jobId])

  const loadJobData = async () => {
    try {
      setLoading(true)
      const [jobData, extractionData] = await Promise.all([
        getJob(jobId),
        getExtraction(jobId).catch(() => null)
      ])
      setJob(jobData)
      setExtraction(extractionData || jobData.extraction)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load job')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading...</div>
  }

  if (error || !job) {
    return <div className="text-red-500 py-12">Error: {error || 'Job not found'}</div>
  }

  const keywords = extraction?.keywords_json.keywords || []
  const mustHaveKeywords = extraction?.must_have_json.keywords || []
  const niceToHaveKeywords = extraction?.nice_to_have_json.keywords || []
  const certifications = extraction?.certifications_json.certifications || []

  return (
    <div>
      <button
        onClick={() => router.back()}
        className="mb-4 text-blue-600 hover:underline"
      >
        ← Back to List
      </button>

      <div className="bg-white rounded-lg shadow-lg p-6">
        {/* Basic Information */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-4">{job.title}</h1>
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-semibold">Company: </span>
              {job.company}
            </div>
            {job.location && (
              <div>
                <span className="font-semibold">Location: </span>
                {job.location}
              </div>
            )}
            <div>
              <span className="font-semibold">Source: </span>
              {job.source}
            </div>
            {job.url && (
              <div>
                <span className="font-semibold">URL: </span>
                <a href={job.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                  View Original
                </a>
              </div>
            )}
            {job.role_family && (
              <div>
                <span className="font-semibold">Role Family: </span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  job.role_family === 'testing' ? 'bg-pink-600 text-white' :
                  job.role_family === 'ai' ? 'bg-purple-600 text-white' :
                  job.role_family === 'fullstack' ? 'bg-indigo-600 text-white' :
                  job.role_family === 'frontend' ? 'bg-cyan-600 text-white' :
                  job.role_family === 'devops' ? 'bg-emerald-600 text-white' :
                  job.role_family === 'data' ? 'bg-blue-600 text-white' :
                  job.role_family === 'business analyst' ? 'bg-amber-600 text-white' :
                  job.role_family === 'product manager' ? 'bg-rose-600 text-white' :
                  job.role_family === 'mobile' ? 'bg-teal-600 text-white' :
                  job.role_family === '其他' ? 'bg-gray-600 text-white' :
                  'bg-gray-600 text-white'
                }`}>
                  {job.role_family}
                </span>
              </div>
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
                <div>
                  <span className="font-semibold">Seniority Level: </span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    colorKey === 'graduate' ? 'bg-lime-100 text-lime-900' :
                    colorKey === 'junior' ? 'bg-yellow-100 text-yellow-900' :
                    colorKey === 'intermediate' || colorKey === 'mid' ? 'bg-amber-100 text-amber-900' :
                    colorKey === 'senior' ? 'bg-orange-100 text-orange-900' :
                    colorKey === 'manager' ? 'bg-purple-100 text-purple-900' :
                    colorKey === 'lead' ? 'bg-indigo-100 text-indigo-900' :
                    colorKey === 'architect' ? 'bg-cyan-100 text-cyan-900' :
                    colorKey === 'unknown' ? 'bg-gray-100 text-gray-900' :
                    'bg-gray-100 text-gray-900'
                  }`}>
                    {displaySeniority}
                  </span>
                </div>
              );
            })()}
            <div>
              <span className="font-semibold">Status: </span>
              <span className={`px-2 py-1 rounded text-xs ${
                job.status === 'applied' ? 'bg-green-100 text-green-800' :
                job.status === 'rejected' ? 'bg-red-100 text-red-800' :
                job.status === 'accepted' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {job.status}
              </span>
            </div>
            {job.posted_date ? (
              <div>
                <span className="font-semibold">Posted At: </span>
                {new Date(job.posted_date).toLocaleString('en-GB')}
              </div>
            ) : (
              <div>
                <span className="font-semibold">Captured At: </span>
                {new Date(job.captured_at).toLocaleString('en-GB')}
              </div>
            )}
          </div>
        </div>

        {/* Extraction Summary */}
        {extraction && (
          <div className="bg-gray-50 p-4 rounded-lg mb-6">
            <h2 className="font-semibold mb-2">Extraction Summary</h2>
            <div className="grid md:grid-cols-3 gap-4 text-sm">
              {extraction.years_required && (
                <div>
                  <span className="font-semibold">Years of Experience: </span>
                  {extraction.years_required} years
                </div>
              )}
              {extraction.degree_required && (
                <div>
                  <span className="font-semibold">Degree Required: </span>
                  {extraction.degree_required}
                </div>
              )}
              {certifications.length > 0 && (
                <div>
                  <span className="font-semibold">Certifications: </span>
                  {certifications.join(', ')}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Original JD Text */}
        <div className="mb-6">
          <button
            onClick={() => setShowJD(!showJD)}
            className="flex items-center justify-between w-full p-3 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            <span className="font-semibold">Job Description (JD Text)</span>
            <span>{showJD ? '▼' : '▶'}</span>
          </button>
          {showJD && (
            <div className="mt-2 p-4 bg-gray-50 rounded border border-gray-200">
              <pre className="whitespace-pre-wrap text-sm">{job.jd_text}</pre>
            </div>
          )}
        </div>

        {/* All Keywords */}
        {keywords.length > 0 && (
          <div className="mb-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Extracted Keywords</h2>
              <div className="text-sm text-gray-600">
                <span className="font-medium">Sorted by Weight</span>
                <span className="ml-2 text-xs">(higher score = more important)</span>
              </div>
            </div>
            
            {/* Colour Legend */}
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <div className="text-sm font-medium mb-2">Keyword Category Colour Guide:</div>
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">Programming Languages</span>
                <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded">Frameworks/Libraries</span>
                <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded">Cloud Platforms</span>
                <span className="px-2 py-1 bg-green-100 text-green-800 rounded">DevOps Tools</span>
                <span className="px-2 py-1 bg-pink-100 text-pink-800 rounded">Testing Tools</span>
                <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded">Platforms/Systems</span>
                <span className="px-2 py-1 bg-indigo-100 text-indigo-800 rounded">Data/Databases</span>
                <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded">Other</span>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-2">
              {keywords.map((kw, idx) => (
                <span
                  key={idx}
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    kw.category === 'language' ? 'bg-blue-100 text-blue-800' :
                    kw.category === 'framework' ? 'bg-purple-100 text-purple-800' :
                    kw.category === 'cloud' ? 'bg-yellow-100 text-yellow-800' :
                    kw.category === 'devops' ? 'bg-green-100 text-green-800' :
                    kw.category === 'testing' ? 'bg-pink-100 text-pink-800' :
                    kw.category === 'platform' ? 'bg-orange-100 text-orange-800' :
                    kw.category === 'data' ? 'bg-indigo-100 text-indigo-800' :
                    'bg-gray-100 text-gray-800'
                  }`}
                  title={`Category: ${kw.category} | Weight Score: ${kw.score} | Occurrences: ${kw.count || 1}`}
                >
                  {kw.term}
                  <span className="ml-1 text-xs opacity-70">({kw.score})</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Must-Have Skills */}
        {mustHaveKeywords.length > 0 && (
          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-4 text-red-700">Must-Have Skills</h2>
            <div className="flex flex-wrap gap-2">
              {mustHaveKeywords.map((kw, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm"
                >
                  {kw}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Nice to Have */}
        {niceToHaveKeywords.length > 0 && (
          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-4 text-green-700">Nice to Have</h2>
            <div className="flex flex-wrap gap-2">
              {niceToHaveKeywords.map((kw, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                >
                  {kw}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Certifications */}
        {certifications.length > 0 && (
          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-4">Certifications</h2>
            <div className="flex flex-wrap gap-2">
              {certifications.map((cert, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm"
                >
                  {cert}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}