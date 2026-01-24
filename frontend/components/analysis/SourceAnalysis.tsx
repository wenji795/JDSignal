'use client'

interface SourceAnalysisProps {
  days?: number
  role_family?: string
  seniority?: string
  location?: string
}

export default function SourceAnalysis({ days = 30, role_family, seniority, location }: SourceAnalysisProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-4">Data Source Analysis</h3>
      <div className="text-center py-8 text-gray-500">
        Source analysis coming soon...
      </div>
    </div>
  )
}
