'use client'

interface IndustryAnalysisProps {
  days?: number
  role_family?: string
  seniority?: string
  location?: string
}

export default function IndustryAnalysis({ days = 30, role_family, seniority, location }: IndustryAnalysisProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-4">Industry Analysis</h3>
      <div className="text-center py-8 text-gray-500">
        Industry analysis coming soon...
      </div>
    </div>
  )
}
