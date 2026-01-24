'use client'

import { useEffect } from 'react'

interface SkillCombinationAnalysisProps {
  days?: number
  role_family?: string
  seniority?: string
  location?: string
}

export default function SkillCombinationAnalysis({ days = 30, role_family, seniority, location }: SkillCombinationAnalysisProps) {
  useEffect(() => {
    console.log('SkillCombinationAnalysis component loaded', { days, role_family, seniority, location })
  }, [days, role_family, seniority, location])

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-4">Skill Combination Analysis</h3>
      <div className="text-center py-8 text-gray-500">
        Skill combination analysis coming soon...
        <div className="text-xs mt-2 text-gray-400">
          Filters: days={days}, role_family={role_family || 'all'}, seniority={seniority || 'all'}, location={location || 'all'}
        </div>
      </div>
    </div>
  )
}
