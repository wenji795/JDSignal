'use client'

import { useEffect, useState } from 'react'
import { getSkillCombinationAnalysis, type SkillCombinationAnalysisResponse } from '@/lib/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts'

interface SkillCombinationAnalysisProps {
  days?: number
  role_family?: string
  seniority?: string
  location?: string
}

const roleFamilyColors: Record<string, string> = {
  'testing': '#db2777',
  'ai': '#9333ea',
  'fullstack': '#4f46e5',
  'frontend': '#0891b2',
  'devops': '#059669',
  'data': '#2563eb',
  'business analyst': '#d97706',
  'product manager': '#e11d48',
  'mobile': '#0d9488',
  '其他': '#6b7280'
}

export default function SkillCombinationAnalysis({ days = 30, role_family, seniority, location }: SkillCombinationAnalysisProps) {
  const [data, setData] = useState<SkillCombinationAnalysisResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [days, role_family, seniority, location])

  const loadData = async () => {
    try {
      setLoading(true)
      const params: any = { days }
      if (role_family) params.role_family = role_family
      if (seniority) params.seniority = seniority
      if (location) params.location = location

      const result = await getSkillCombinationAnalysis(params)
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load skill combination analysis')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-8">Loading skill combination analysis...</div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-red-500">Error: {error || 'Failed to load data'}</div>
      </div>
    )
  }

  // 准备技能共现数据（显示为 "Skill1 + Skill2"）
  const cooccurrenceData = data.skill_cooccurrence.map(item => ({
    combination: `${item.skill1} + ${item.skill2}`,
    count: item.count
  }))

  return (
    <div className="space-y-6">
      {/* Skill Co-occurrence */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Top Skill Combinations (Co-occurrence)</h3>
        {cooccurrenceData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={cooccurrenceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="combination" 
                angle={-45}
                textAnchor="end"
                height={120}
              />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-8 text-gray-500">No skill co-occurrence data available</div>
        )}
      </div>

      {/* Must-have vs Nice-to-have */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Must-have vs Nice-to-have Skills (Top 20)</h3>
        {data.must_have_vs_nice_to_have.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={data.must_have_vs_nice_to_have.slice(0, 20)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="skill" 
                angle={-45}
                textAnchor="end"
                height={120}
              />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="must_have_count" stackId="a" fill="#ef4444" name="Must-have" />
              <Bar dataKey="nice_to_have_count" stackId="a" fill="#3b82f6" name="Nice-to-have" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-8 text-gray-500">No must-have/nice-to-have data available</div>
        )}
      </div>

      {/* Skill Intensity by Role Family */}
      {Object.keys(data.skill_intensity_by_role_family).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-semibold mb-4">Top Skills by Role Family</h3>
          <div className="grid md:grid-cols-2 gap-6">
            {Object.entries(data.skill_intensity_by_role_family).map(([roleFamily, skills]) => (
              <div key={roleFamily} className="border rounded-lg p-4">
                <h4 className="font-semibold mb-3 text-lg" style={{ color: roleFamilyColors[roleFamily.toLowerCase()] || '#6b7280' }}>
                  {roleFamily}
                </h4>
                <div className="space-y-2">
                  {skills.map((skillItem, idx) => (
                    <div key={idx} className="flex items-center justify-between">
                      <span className="text-sm">{skillItem.skill}</span>
                      <span className="text-sm font-semibold" style={{ color: roleFamilyColors[roleFamily.toLowerCase()] || '#6b7280' }}>
                        {skillItem.count}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
