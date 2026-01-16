import type { Metadata } from 'next'
import Link from 'next/link'
import './globals.css'

export const metadata: Metadata = {
  title: 'Job JD Tracker & ATS Keyword Extractor',
  description: '本地优先的职位JD追踪和ATS关键词提取系统',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        <nav className="bg-gray-900 text-white p-4">
          <div className="container mx-auto flex items-center justify-between">
            <Link href="/" className="text-xl font-bold hover:text-gray-300 transition-colors">
              Job JD Tracker
            </Link>
            <div className="flex gap-4 items-center">
              <Link href="/" className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded transition-colors">
                首页
              </Link>
              <Link href="/jobs" className="hover:text-gray-300 transition-colors">职位列表</Link>
              <Link href="/trends" className="hover:text-gray-300 transition-colors">趋势分析</Link>
            </div>
          </div>
        </nav>
        <main className="container mx-auto p-6">
          {children}
        </main>
      </body>
    </html>
  )
}