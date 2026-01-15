import Link from 'next/link'

export default function Home() {
  return (
    <div className="max-w-4xl mx-auto mt-12">
      <h1 className="text-4xl font-bold mb-6">Job JD Tracker & ATS Keyword Extractor</h1>
      <p className="text-xl text-gray-600 mb-8">
        本地优先的职位JD追踪和ATS关键词提取系统
      </p>
      
      <div className="grid md:grid-cols-2 gap-6 mt-8">
        <Link href="/jobs" className="p-6 border rounded-lg hover:shadow-lg transition-shadow">
          <h2 className="text-2xl font-semibold mb-2">职位列表</h2>
          <p className="text-gray-600">查看所有职位，筛选和管理职位信息</p>
        </Link>
        
        <Link href="/trends" className="p-6 border rounded-lg hover:shadow-lg transition-shadow">
          <h2 className="text-2xl font-semibold mb-2">趋势分析</h2>
          <p className="text-gray-600">查看关键词趋势和统计分析</p>
        </Link>
      </div>
    </div>
  )
}