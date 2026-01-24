'use client'

import { useState } from 'react'
import KeywordStats from '@/components/analysis/KeywordStats'
import RoleFamilyDistribution from '@/components/analysis/RoleFamilyDistribution'
import MonthlyComparison from '@/components/analysis/MonthlyComparison'
import TimeTrends from '@/components/analysis/TimeTrends'
import LocationAnalysis from '@/components/analysis/LocationAnalysis'
import CompanyAnalysis from '@/components/analysis/CompanyAnalysis'
import SkillCombinationAnalysis from '@/components/analysis/SkillCombinationAnalysis'
import ExperienceAnalysis from '@/components/analysis/ExperienceAnalysis'
import EducationAnalysis from '@/components/analysis/EducationAnalysis'
import IndustryAnalysis from '@/components/analysis/IndustryAnalysis'
import SourceAnalysis from '@/components/analysis/SourceAnalysis'
import { ErrorBoundary } from '@/components/analysis/ErrorBoundary'

export default function AnalysisPage() {
  const [days, setDays] = useState(30)
  const [roleFamily, setRoleFamily] = useState('')
  const [seniority, setSeniority] = useState('')
  const [location, setLocation] = useState('')

  // Role family options
  const roleFamilyOptions = [
    { value: '', label: 'All' },
    { value: 'testing', label: 'Software Testing' },
    { value: 'ai', label: 'AI/Machine Learning' },
    { value: 'fullstack', label: 'Full Stack' },
    { value: 'frontend', label: 'Frontend/UI/UX' },
    { value: 'devops', label: 'DevOps' },
    { value: 'data', label: 'Data' },
    { value: 'business analyst', label: 'Business Analyst' },
    { value: 'product manager', label: 'Product Manager' },
    { value: 'mobile', label: 'Mobile Development' },
    { value: '其他', label: 'Other' }
  ]

  // Seniority options
  const seniorityOptions = [
    { value: '', label: 'All' },
    { value: 'graduate', label: 'Graduate' },
    { value: 'junior', label: 'Junior' },
    { value: 'intermediate', label: 'Intermediate' },
    { value: 'senior', label: 'Senior' }
  ]

  const filterParams = {
    days,
    role_family: roleFamily || undefined,
    seniority: seniority || undefined,
    location: location || undefined
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-4">Job Market Analysis</h1>
        
        {/* Filters */}
        <div className="flex flex-wrap gap-4 items-end bg-white p-4 rounded-lg shadow">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Time Window:</label>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="p-2 border rounded text-sm"
            >
              <option value={7}>7 days</option>
              <option value={30}>30 days</option>
              <option value={60}>60 days</option>
              <option value={90}>90 days</option>
            </select>
          </div>
          
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Role Family:</label>
            <select
              value={roleFamily}
              onChange={(e) => setRoleFamily(e.target.value)}
              className="p-2 border rounded text-sm"
            >
              {roleFamilyOptions.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Seniority:</label>
            <select
              value={seniority}
              onChange={(e) => setSeniority(e.target.value)}
              className="p-2 border rounded text-sm"
            >
              {seniorityOptions.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Location:</label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g., Auckland, NZ"
              className="p-2 border rounded text-sm"
            />
          </div>
        </div>
      </div>

      {/* Analysis Sections */}
      <div className="space-y-8">
        {/* Section 0: Current Features */}
        <section>
          <h2 className="text-2xl font-semibold mb-4">Keyword Analysis</h2>
          <div className="grid gap-6">
            <KeywordStats {...filterParams} />
            <RoleFamilyDistribution {...filterParams} />
            <MonthlyComparison {...filterParams} />
          </div>
        </section>

        {/* Section 1: Time Trends */}
        <section>
          <h2 className="text-2xl font-semibold mb-4">Time Trends</h2>
          <TimeTrends {...filterParams} />
        </section>

        {/* Section 2: Location Analysis */}
        <section id="location-analysis">
          <h2 className="text-2xl font-semibold mb-4">Location Analysis</h2>
          <ErrorBoundary componentName="Location Analysis">
            <LocationAnalysis {...filterParams} />
          </ErrorBoundary>
        </section>

        {/* Section 3: Company Analysis */}
        <section id="company-analysis">
          <h2 className="text-2xl font-semibold mb-4">Company Analysis</h2>
          <ErrorBoundary componentName="Company Analysis">
            <CompanyAnalysis {...filterParams} />
          </ErrorBoundary>
        </section>

        {/* Section 4: Skill Combination Analysis */}
        <section id="skill-combination-analysis">
          <h2 className="text-2xl font-semibold mb-4">Skill Combination Analysis</h2>
          <ErrorBoundary componentName="Skill Combination Analysis">
            <SkillCombinationAnalysis {...filterParams} />
          </ErrorBoundary>
        </section>

        {/* Section 5: Experience Analysis */}
        <section id="experience-analysis">
          <h2 className="text-2xl font-semibold mb-4">Experience Requirements</h2>
          <ErrorBoundary componentName="Experience Analysis">
            <ExperienceAnalysis {...filterParams} />
          </ErrorBoundary>
        </section>

        {/* Section 6: Education Analysis */}
        <section id="education-analysis">
          <h2 className="text-2xl font-semibold mb-4">Education Requirements</h2>
          <ErrorBoundary componentName="Education Analysis">
            <EducationAnalysis {...filterParams} />
          </ErrorBoundary>
        </section>

        {/* Section 7: Industry Analysis */}
        <section id="industry-analysis">
          <h2 className="text-2xl font-semibold mb-4">Industry Analysis</h2>
          <ErrorBoundary componentName="Industry Analysis">
            <IndustryAnalysis {...filterParams} />
          </ErrorBoundary>
        </section>

        {/* Section 8: Source Analysis */}
        <section id="source-analysis">
          <h2 className="text-2xl font-semibold mb-4">Data Source Analysis</h2>
          <ErrorBoundary componentName="Source Analysis">
            <SourceAnalysis {...filterParams} />
          </ErrorBoundary>
        </section>
      </div>
    </div>
  )
}
