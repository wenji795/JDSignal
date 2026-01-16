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

  // 获取当前职位数量
  const fetchJobCount = async () => {
    try {
      const jobs = await getJobs()
      return jobs.length
    } catch (error) {
      console.error('获取职位数量失败:', error)
      return null
    }
  }

  // 清理定时器
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
      // 记录抓取前的职位数量
      const countBefore = await fetchJobCount()
      setJobCountBefore(countBefore)

      // 触发抓取任务
      const result = await triggerScrape({
        max_per_keyword: 20,
        headless: true,
        browser: 'firefox'
      })

      setScrapeStatus('running')
      setScrapeMessage('✓ 抓取任务已启动，正在后台运行...')

      // 开始定期检查职位数量变化
      let checkCount = 0
      const maxChecks = 30 // 最多检查30次（5分钟）
      const interval = setInterval(async () => {
        checkCount++
        const currentCount = await fetchJobCount()
        
        if (currentCount !== null && countBefore !== null) {
          const newJobs = currentCount - countBefore
          if (newJobs > 0) {
            setJobCountAfter(currentCount)
            setScrapeMessage(`✓ 抓取进行中... 已发现 ${newJobs} 个新职位`)
          } else {
            setScrapeMessage(`✓ 抓取进行中... 正在处理关键词（${checkCount * 10}秒）`)
          }
        }

        // 5分钟后停止检查，假设任务已完成
        if (checkCount >= maxChecks) {
          clearInterval(interval)
          setCheckInterval(null)
          setScrapeStatus('completed')
          const finalCount = await fetchJobCount()
          if (finalCount !== null && countBefore !== null) {
            const totalNewJobs = finalCount - countBefore
            if (totalNewJobs > 0) {
              setScrapeMessage(`✓ 抓取任务已完成！共抓取 ${totalNewJobs} 个新职位`)
            } else {
              setScrapeMessage('✓ 抓取任务已完成（未发现新职位，可能都是重复的）')
            }
          } else {
            setScrapeMessage('✓ 抓取任务已完成，请查看职位列表确认结果')
          }
          setScraping(false)
        }
      }, 10000) // 每10秒检查一次

      setCheckInterval(interval)

    } catch (error) {
      setScrapeStatus('error')
      setScrapeMessage(`✗ 错误: ${error instanceof Error ? error.message : '未知错误'}`)
      setScraping(false)
      // 清理定时器（如果已设置）
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
        本地优先的职位JD追踪和ATS关键词提取系统
      </p>
      
      {/* 手动触发抓取按钮 */}
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
              <h3 className="font-semibold text-blue-900 mb-1">立即抓取最新职位</h3>
              <p className="text-sm text-blue-700 mb-2">
                手动触发一次增量抓取任务，抓取新西兰Seek上的最新职位（自动去重）
              </p>
              
              {/* 状态信息 */}
              {scrapeStatus !== 'idle' && (
                <div className="mt-3 space-y-2">
                  {scrapeStatus === 'running' && (
                    <div className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      <p className="text-sm font-medium text-blue-800">
                        任务正在后台运行中...
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

                  {/* 职位数量变化 */}
                  {jobCountBefore !== null && (
                    <div className="text-xs text-gray-600 mt-2">
                      <span>抓取前: {jobCountBefore} 个职位</span>
                      {jobCountAfter !== null && (
                        <span className="ml-4">当前: {jobCountAfter} 个职位</span>
                      )}
                    </div>
                  )}

                  {/* 提示信息 */}
                  {scrapeStatus === 'running' && (
                    <div className="mt-3 p-3 bg-blue-100 rounded text-xs text-blue-800">
                      <p className="font-medium mb-1">💡 提示：</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>抓取任务在后台运行，可能需要几分钟时间</li>
                        <li>系统会自动检查新职位并更新显示</li>
                        <li>您可以继续使用其他功能，无需等待</li>
                        <li>完成后可以前往"职位列表"查看新抓取的职位</li>
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
                    运行中
                  </span>
                ) : (
                  '开始抓取'
                )}
              </button>
              
              {/* 完成后显示查看职位列表按钮 */}
              {scrapeStatus === 'completed' && (
                <Link
                  href="/jobs"
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm transition-colors"
                >
                  查看职位列表 →
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
      
      <div className="grid md:grid-cols-3 gap-6 mt-8">
        <Link href="/jobs" className="p-6 border rounded-lg hover:shadow-lg transition-shadow">
          <h2 className="text-2xl font-semibold mb-2">职位列表</h2>
          <p className="text-gray-600">查看所有职位，筛选和管理职位信息</p>
        </Link>
        
        <Link href="/trends" className="p-6 border rounded-lg hover:shadow-lg transition-shadow">
          <h2 className="text-2xl font-semibold mb-2">趋势分析</h2>
          <p className="text-gray-600">查看关键词趋势和统计分析</p>
        </Link>
        
        <Link href="/manual-job" className="p-6 border rounded-lg hover:shadow-lg transition-shadow">
          <h2 className="text-2xl font-semibold mb-2">手动输入JD</h2>
          <p className="text-gray-600">通过纯文本形式手动输入职位JD</p>
        </Link>
      </div>
    </div>
  )
}