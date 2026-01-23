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
  const [elapsedTime, setElapsedTime] = useState(0)
  const [newJobsCount, setNewJobsCount] = useState(0)

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

  // Timer for elapsed time
  useEffect(() => {
    let timer: NodeJS.Timeout | null = null
    if (scrapeStatus === 'running' || scrapeStatus === 'starting') {
      timer = setInterval(() => {
        setElapsedTime(prev => prev + 1)
      }, 1000)
    } else {
      setElapsedTime(0)
    }
    return () => {
      if (timer) clearInterval(timer)
    }
  }, [scrapeStatus])

  const handleTriggerScrape = async () => {
    setScraping(true)
    setScrapeStatus('starting')
    setScrapeMessage(null)
    setJobCountAfter(null)
    setNewJobsCount(0)
    setElapsedTime(0)

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
      setScrapeMessage('任务已启动，正在后台运行...')

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
            setNewJobsCount(newJobs)
            setScrapeMessage(`正在抓取中... 已发现 ${newJobs} 个新职位`)
          } else {
            const elapsedSeconds = checkCount * 10
            setScrapeMessage(`正在处理关键词提取中... (${elapsedSeconds}秒)`)
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
            setNewJobsCount(totalNewJobs)
            if (totalNewJobs > 0) {
              setScrapeMessage(`✓ 抓取任务完成！共抓取 ${totalNewJobs} 个新职位`)
            } else {
              setScrapeMessage('✓ 抓取任务完成（未发现新职位，可能都是重复的）')
            }
          } else {
            setScrapeMessage('✓ 抓取任务完成，请查看职位列表确认结果')
          }
          setScraping(false)
        }
      }, 10000) // Check every 10 seconds

      setCheckInterval(interval)

    } catch (error) {
      setScrapeStatus('error')
      setScrapeMessage(`✗ 错误: ${error instanceof Error ? error.message : '未知错误'}`)
      setScraping(false)
      // Clean up interval (if set)
      if (checkInterval) {
        clearInterval(checkInterval)
        setCheckInterval(null)
      }
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="max-w-4xl mx-auto mt-12">
      <h1 className="text-4xl font-bold mb-6">Job JD Tracker & ATS Keyword Extractor</h1>
      <p className="text-xl text-gray-600 mb-8">
        Local-first job JD tracking and ATS keyword extraction system
      </p>
      
      {/* Manual scrape trigger button */}
      <div className={`border-2 rounded-xl p-6 mb-8 transition-all duration-300 shadow-sm ${
        scrapeStatus === 'running' 
          ? 'bg-gradient-to-br from-blue-50 to-blue-100 border-blue-400 shadow-blue-200' 
          : scrapeStatus === 'completed'
          ? 'bg-gradient-to-br from-green-50 to-green-100 border-green-400 shadow-green-200'
          : scrapeStatus === 'error'
          ? 'bg-gradient-to-br from-red-50 to-red-100 border-red-400 shadow-red-200'
          : 'bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200'
      }`}>
        <div className="flex flex-col gap-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="text-xl font-bold text-gray-900">立即抓取最新职位</h3>
                {scrapeStatus === 'running' && (
                  <span className="px-2 py-1 bg-blue-200 text-blue-800 text-xs font-semibold rounded-full animate-pulse">
                    运行中
                  </span>
                )}
                {scrapeStatus === 'completed' && (
                  <span className="px-2 py-1 bg-green-200 text-green-800 text-xs font-semibold rounded-full">
                    已完成
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-600 mb-4">
                手动触发增量抓取任务，从 Seek NZ 获取最新职位（自动去重）
              </p>
              
              {/* Status information */}
              {scrapeStatus !== 'idle' && (
                <div className="mt-4 space-y-3">
                  {/* Progress indicator */}
                  {scrapeStatus === 'running' && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
                          <span className="font-medium text-blue-800">正在抓取中...</span>
                        </div>
                        <span className="text-blue-600 font-mono">{formatTime(elapsedTime)}</span>
                      </div>
                      {/* Progress bar */}
                      <div className="w-full bg-blue-200 rounded-full h-2 overflow-hidden">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-500 ease-out"
                          style={{ 
                            width: `${Math.min((elapsedTime / 300) * 100, 95)}%` 
                          }}
                        ></div>
                      </div>
                    </div>
                  )}
                  
                  {/* Status message */}
                  {scrapeMessage && (
                    <div className={`p-3 rounded-lg ${
                      scrapeStatus === 'completed' 
                        ? 'bg-green-100 border border-green-300' 
                        : scrapeStatus === 'error' 
                        ? 'bg-red-100 border border-red-300'
                        : 'bg-blue-100 border border-blue-300'
                    }`}>
                      <p className={`text-sm font-medium ${
                        scrapeStatus === 'completed' ? 'text-green-800' :
                        scrapeStatus === 'error' ? 'text-red-800' :
                        'text-blue-800'
                      }`}>
                        {scrapeMessage}
                      </p>
                    </div>
                  )}

                  {/* Statistics */}
                  {(jobCountBefore !== null || newJobsCount > 0) && (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {jobCountBefore !== null && (
                        <div className="bg-white/60 backdrop-blur-sm p-3 rounded-lg border border-gray-200">
                          <p className="text-xs text-gray-500 mb-1">抓取前</p>
                          <p className="text-lg font-bold text-gray-800">{jobCountBefore}</p>
                          <p className="text-xs text-gray-500">个职位</p>
                        </div>
                      )}
                      {jobCountAfter !== null && (
                        <div className="bg-white/60 backdrop-blur-sm p-3 rounded-lg border border-gray-200">
                          <p className="text-xs text-gray-500 mb-1">当前总数</p>
                          <p className="text-lg font-bold text-blue-600">{jobCountAfter}</p>
                          <p className="text-xs text-gray-500">个职位</p>
                        </div>
                      )}
                      {newJobsCount > 0 && (
                        <div className="bg-white/60 backdrop-blur-sm p-3 rounded-lg border border-green-300">
                          <p className="text-xs text-gray-500 mb-1">新增职位</p>
                          <p className="text-lg font-bold text-green-600">+{newJobsCount}</p>
                          <p className="text-xs text-gray-500">个职位</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Tips */}
                  {scrapeStatus === 'running' && (
                    <div className="mt-4 p-4 bg-white/70 backdrop-blur-sm rounded-lg border border-blue-200">
                      <div className="flex items-start gap-2">
                        <span className="text-lg">💡</span>
                        <div className="flex-1">
                          <p className="text-xs font-semibold text-blue-900 mb-2">提示：</p>
                          <ul className="text-xs text-blue-800 space-y-1.5">
                            <li className="flex items-start gap-2">
                              <span className="text-blue-500 mt-0.5">•</span>
                              <span>抓取任务在后台运行，可能需要几分钟时间</span>
                            </li>
                            <li className="flex items-start gap-2">
                              <span className="text-blue-500 mt-0.5">•</span>
                              <span>系统会自动检查新职位并更新显示</span>
                            </li>
                            <li className="flex items-start gap-2">
                              <span className="text-blue-500 mt-0.5">•</span>
                              <span>您可以继续使用其他功能，无需等待</span>
                            </li>
                            <li className="flex items-start gap-2">
                              <span className="text-blue-500 mt-0.5">•</span>
                              <span>完成后，前往"职位列表"查看新抓取的职位</span>
                            </li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
            
            <div className="flex flex-col items-end gap-3">
              <button
                onClick={handleTriggerScrape}
                disabled={scraping}
                className={`px-6 py-3 text-white rounded-lg font-semibold transition-all duration-200 disabled:cursor-not-allowed shadow-md ${
                  scraping
                    ? 'bg-gray-400 cursor-not-allowed shadow-none'
                    : 'bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 hover:shadow-lg transform hover:scale-105 active:scale-95'
                }`}
              >
                {scraping ? (
                  <span className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                    <span>运行中</span>
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <span>开始抓取</span>
                  </span>
                )}
              </button>
              
              {/* Show view job list button after completion */}
              {scrapeStatus === 'completed' && (
                <Link
                  href="/jobs"
                  className="px-5 py-2.5 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-lg hover:from-green-700 hover:to-green-800 text-sm font-semibold transition-all duration-200 shadow-md hover:shadow-lg transform hover:scale-105 active:scale-95 flex items-center gap-2"
                >
                  <span>查看职位列表</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
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