'use client'

interface ExperienceAnalysisProps {
  days?: number
  role_family?: string
  seniority?: string
  location?: string
}

export default function ExperienceAnalysis({ days = 30, role_family, seniority, location }: ExperienceAnalysisProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-4">Experience Requirements Analysis</h3>
      <div className="text-center py-8 text-gray-500">
        Experience analysis coming soon...
      </div>
    </div>
  )
}
