import type { Metadata } from 'next'
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
            <h1 className="text-xl font-bold">Job JD Tracker</h1>
            <div className="flex gap-4">
              <a href="/jobs" className="hover:text-gray-300">职位列表</a>
              <a href="/trends" className="hover:text-gray-300">趋势分析</a>
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