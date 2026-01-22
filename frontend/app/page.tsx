'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
import { triggerScrape, getJobs } from '@/lib/api'

export default function Home() {
  const [scraping, setScraping] = useState(false)
  const [scrapeStatus, setScrapeStatus] = useState<'idle' | 'starting' | 'running' | 'completed' | 'error'>('idle')
  const [scrapeMessage, setScrapeMessage] = useState<string | null>(null)
  const [jobCountBefore, setJobCountBefore] = useState<number | null>(null)
  const [jobCountAfter, setJobCountAfter] = useState<number | null>(null)
  const [checkInterval, setCheckInterval] = useState<NodeJS.Timeout | null>(null)

  // Get current job count
  const fetchJobCount = async () => {
    try {
      const jobs = await getJobs()
      return jobs.length
    } catch (error) {
      console.error('Failed to fetch job count:', error)
      return null
    }
  }

  // Clean up interval
  useEffect(() => {
    return () => {
      if (checkInterval) {
        clearInterval(checkInterval)
      }
    }
  }, [checkInterval])

  const handleTriggerScrape = async () => {
    setScraping(true)
    setScrapeStatus('starting')
    setScrapeMessage(null)
    setJobCountAfter(null)

    try {
      // Record job count before scraping
      const countBefore = await fetchJobCount()
      setJobCountBefore(countBefore)

      // Trigger scraping task
      const result = await triggerScrape({
        max_per_keyword: 20,
        headless: true,
        browser: 'firefox'
      })

      setScrapeStatus('running')
      setScrapeMessage('✓ Scraping task started, running in background...')

      // Start periodic checks for job count changes
      let checkCount = 0
      const maxChecks = 30 // Maximum 30 checks (5 minutes)
      const interval = setInterval(async () => {
        checkCount++
        const currentCount = await fetchJobCount()
        
        if (currentCount !== null && countBefore !== null) {
          const newJobs = currentCount - countBefore
          if (newJobs > 0) {
            setJobCountAfter(currentCount)
            setScrapeMessage(`✓ Scraping in progress... Found ${newJobs} new jobs`)
          } else {
            setScrapeMessage(`✓ Scraping in progress... Processing keywords (${checkCount * 10}s)`)
          }
        }

        // Stop checking after 5 minutes, assume task completed
        if (checkCount >= maxChecks) {
          clearInterval(interval)
          setCheckInterval(null)
          setScrapeStatus('completed')
          const finalCount = await fetchJobCount()
          if (finalCount !== null && countBefore !== null) {
            const totalNewJobs = finalCount - countBefore
            if (totalNewJobs > 0) {
              setScrapeMessage(`✓ Scraping task completed! Scraped ${totalNewJobs} new jobs`)
            } else {
              setScrapeMessage('✓ Scraping task completed (no new jobs found, may all be duplicates)')
            }
          } else {
            setScrapeMessage('✓ Scraping task completed, please check job list to confirm results')
          }
          setScraping(false)
        }
      }, 10000) // Check every 10 seconds

      setCheckInterval(interval)

    } catch (error) {
      setScrapeStatus('error')
      setScrapeMessage(`✗ Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
      setScraping(false)
      // Clean up interval (if set)
      if (checkInterval) {
        clearInterval(checkInterval)
        setCheckInterval(null)
      }
    }
  }

  return (
    <div className="max-w-4xl mx-auto mt-12">
      <h1 className="text-4xl font-bold mb-6">Job JD Tracker & ATS Keyword Extractor</h1>
      <p className="text-xl text-gray-600 mb-8">
        Local-first job JD tracking and ATS keyword extraction system
      </p>
      
      {/* Manual scrape trigger button */}
      <div className={`border rounded-lg p-6 mb-8 transition-colors ${
        scrapeStatus === 'running' 
          ? 'bg-blue-50 border-blue-300' 
          : scrapeStatus === 'completed'
          ? 'bg-green-50 border-green-300'
          : scrapeStatus === 'error'
          ? 'bg-red-50 border-red-300'
          : 'bg-blue-50 border-blue-200'
      }`}>
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h3 className="font-semibold text-blue-900 mb-1">Scrape Latest Jobs Now</h3>
              <p className="text-sm text-blue-700 mb-2">
                Manually trigger an incremental scraping task to fetch the latest jobs from Seek NZ (automatic deduplication)
              </p>
              
              {/* Status information */}
              {scrapeStatus !== 'idle' && (
                <div className="mt-3 space-y-2">
                  {scrapeStatus === 'running' && (
                    <div className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      <p className="text-sm font-medium text-blue-800">
                        Task running in background...
                      </p>
                    </div>
                  )}
                  
                  {scrapeMessage && (
                    <p className={`text-sm ${
                      scrapeStatus === 'completed' ? 'text-green-700 font-medium' :
                      scrapeStatus === 'error' ? 'text-red-700 font-medium' :
                      'text-blue-700'
                    }`}>
                      {scrapeMessage}
                    </p>
                  )}

                  {/* Job count changes */}
                  {jobCountBefore !== null && (
                    <div className="text-xs text-gray-600 mt-2">
                      <span>Before scraping: {jobCountBefore} jobs</span>
                      {jobCountAfter !== null && (
                        <span className="ml-4">Current: {jobCountAfter} jobs</span>
                      )}
                    </div>
                  )}

                  {/* Tips */}
                  {scrapeStatus === 'running' && (
                    <div className="mt-3 p-3 bg-blue-100 rounded text-xs text-blue-800">
                      <p className="font-medium mb-1">💡 Tips:</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>Scraping task runs in background and may take several minutes</li>
                        <li>System will automatically check for new jobs and update display</li>
                        <li>You can continue using other features without waiting</li>
                        <li>After completion, go to "Job List" to view newly scraped jobs</li>
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
            
            <div className="flex flex-col items-end gap-2 ml-4">
              <button
                onClick={handleTriggerScrape}
                disabled={scraping}
                className={`px-6 py-2 text-white rounded transition-colors disabled:cursor-not-allowed ${
                  scraping
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {scraping ? (
                  <span className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Running
                  </span>
                ) : (
                  'Start Scraping'
                )}
              </button>
              
              {/* Show view job list button after completion */}
              {scrapeStatus === 'completed' && (
                <Link
                  href="/jobs"
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm transition-colors"
                >
                  View Job List →
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
      
      <div className="grid md:grid-cols-3 gap-6 mt-8">
        <Link href="/jobs" className="p-6 border rounded-lg hover:shadow-lg transition-shadow">
          <h2 className="text-2xl font-semibold mb-2">Job List</h2>
          <p className="text-gray-600">View all jobs, filter and manage job information</p>
        </Link>
        
        <Link href="/trends" className="p-6 border rounded-lg hover:shadow-lg transition-shadow">
          <h2 className="text-2xl font-semibold mb-2">Trend Analysis</h2>
          <p className="text-gray-600">View keyword trends and statistical analysis</p>
        </Link>
        
        <Link href="/manual-job" className="p-6 border rounded-lg hover:shadow-lg transition-shadow">
          <h2 className="text-2xl font-semibold mb-2">Manual JD Input</h2>
          <p className="text-gray-600">Manually input job JD via plain text</p>
        </Link>
      </div>
    </div>
  )
}