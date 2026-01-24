'use client'

interface EducationAnalysisProps {
  days?: number
  role_family?: string
  seniority?: string
  location?: string
}

export default function EducationAnalysis({ days = 30, role_family, seniority, location }: EducationAnalysisProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-4">Education Requirements Analysis</h3>
      <div className="text-center py-8 text-gray-500">
        Education analysis coming soon...
      </div>
    </div>
  )
}
