/** API客户端 - 与FastAPI后端通信 */
const API_BASE_URL = 'http://127.0.0.1:8000';

export interface Job {
  id: string;
  source: string;
  url: string | null;
  title: string;
  company: string;
  location: string | null;
  posted_date: string | null;
  captured_at: string;
  jd_text: string;
  status: string;
  role_family: string | null;
  seniority: string | null;
  extraction: Extraction | null;
}

export interface Extraction {
  id: string;
  job_id: string;
  keywords_json: {
    keywords: Keyword[];
  };
  must_have_json: {
    keywords: string[];
  };
  nice_to_have_json: {
    keywords: string[];
  };
  years_required: number | null;
  degree_required: string | null;
  certifications_json: {
    certifications: string[];
  };
  extracted_at: string;
}

export interface Keyword {
  term: string;
  category: string;
  score: number;
  count?: number;  // 出现次数
}

export interface TrendsResponse {
  total_jobs: number;
  count_by_role_family: Record<string, number>;
  count_by_seniority: Record<string, number>;
  top_keywords: Array<{ term: string; count: number }>;
  top_keywords_by_role_family: Record<string, Array<{ term: string; count: number }>>;
  selected_role_family_top_keywords?: Array<{ term: string; count: number }>;
  keyword_growth: Record<string, {
    first_half_count: number;
    second_half_count: number;
    delta: number;
    percent_change: number;
  }>;
  monthly_comparison?: {
    current_month: {
      start: string;
      end: string;
      job_count: number;
    };
    last_month: {
      start: string;
      end: string;
      job_count: number;
    };
    comparison: Array<{
      term: string;
      current_month_count: number;
      last_month_count: number;
      delta: number;
      percent_change: number;
      status: 'new' | 'increased' | 'decreased' | 'unchanged';
    }>;
    by_role_family?: Record<string, Array<{
      term: string;
      current_month_count: number;
      last_month_count: number;
      delta: number;
      percent_change: number;
      status: 'new' | 'increased' | 'decreased' | 'unchanged';
    }>>;
  };
  extraction_coverage?: {
    total_jobs_all: number;
    total_jobs_with_extraction: number;
    coverage_rate: number;
  };
}

export interface TimeTrendsResponse {
  granularity: 'day' | 'week' | 'month';
  time_range: {
    start: string;
    end: string;
    days: number;
  };
  job_count_trend: Array<{ date: string; count: number }>;
  role_family_trends: Record<string, Array<{ date: string; count: number }>>;
  keyword_trends: Record<string, Array<{ date: string; count: number }>>;
  activity_summary: {
    weekly: Array<{ week: string; count: number }>;
    monthly: Array<{ month: string; count: number }>;
  };
  total_jobs: number;
}

export interface LocationAnalysisResponse {
  location_distribution: Array<{ location: string; count: number }>;
  location_by_role_family: Record<string, Record<string, number>>;
  location_trends: Record<string, Array<{ week: string; count: number }>>;
  total_jobs: number;
}

export interface CompanyAnalysisResponse {
  top_companies: Array<{ company: string; count: number }>;
  company_trends: Record<string, Array<{ week: string; count: number }>>;
  company_role_family_preference: Record<string, Record<string, number>>;
  total_jobs: number;
}

export interface ExperienceAnalysisResponse {
  experience_distribution: Array<{ range: string; count: number }>;
  experience_by_role_family: Record<string, Record<string, number>>;
  experience_trends: Array<{ week: string; average_years: number; count: number }>;
  total_jobs: number;
  jobs_with_experience: number;
}

export interface EducationAnalysisResponse {
  degree_distribution: Array<{ degree: string; count: number }>;
  degree_by_role_family: Record<string, Record<string, number>>;
  certifications_distribution: Array<{ certification: string; count: number }>;
  total_jobs: number;
  jobs_with_degree: number;
  jobs_with_certifications: number;
}

export interface IndustryAnalysisResponse {
  industry_distribution: Array<{ industry: string; count: number }>;
  industry_by_role_family: Record<string, Record<string, number>>;
  industry_trends: Record<string, Array<{ week: string; count: number }>>;
  total_jobs: number;
}

export interface SourceAnalysisResponse {
  source_distribution: Array<{ source: string; count: number }>;
  source_quality: Record<string, {
    total_jobs: number;
    extracted_jobs: number;
    success_rate: number;
  }>;
  total_jobs: number;
}

export interface SkillCombinationAnalysisResponse {
  skill_cooccurrence: Array<{ skill1: string; skill2: string; count: number }>;
  must_have_vs_nice_to_have: Array<{
    skill: string;
    must_have_count: number;
    nice_to_have_count: number;
    total_count: number;
  }>;
  skill_intensity_by_role_family: Record<string, Array<{ skill: string; count: number }>>;
  total_jobs: number;
}

/**
 * 获取所有职位
 */
export async function getJobs(params?: {
  status?: string;
  role_family?: string | string[];
  seniority?: string | string[];
  keyword?: string;
  location?: string;
}): Promise<Job[]> {
  const queryParams = new URLSearchParams();
  if (params?.status) queryParams.append('status', params.status);
  if (params?.role_family) {
    if (Array.isArray(params.role_family)) {
      params.role_family.forEach(rf => queryParams.append('role_family', rf));
    } else {
      queryParams.append('role_family', params.role_family);
    }
  }
  if (params?.seniority) {
    if (Array.isArray(params.seniority)) {
      params.seniority.forEach(s => queryParams.append('seniority', s));
    } else {
      queryParams.append('seniority', params.seniority);
    }
  }
  if (params?.keyword) queryParams.append('keyword', params.keyword);
  if (params?.location) queryParams.append('location', params.location);
  
  const url = `${API_BASE_URL}/jobs${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10秒超时
    
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to fetch jobs: ${response.status} ${response.statusText} - ${errorText}`);
    }
    
    return response.json();
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('请求超时，请检查后端服务是否运行在 http://127.0.0.1:8000');
    }
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('无法连接到后端API，请确保后端服务正在运行 (http://127.0.0.1:8000)');
    }
    throw error;
  }
}

/**
 * 获取特定职位详情
 */
export async function getJob(id: string): Promise<Job> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    
    const response = await fetch(`${API_BASE_URL}/jobs/${id}`, {
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch job: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('请求超时，请检查后端服务是否运行');
    }
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('无法连接到后端API，请确保后端服务正在运行');
    }
    throw error;
  }
}

/**
 * 获取职位的提取结果
 */
export async function getExtraction(id: string): Promise<Extraction> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    
    const response = await fetch(`${API_BASE_URL}/jobs/${id}/extraction`, {
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      // 404是正常的，表示还没有提取结果
      if (response.status === 404) {
        throw new Error('Extraction not found');
      }
      throw new Error(`Failed to fetch extraction: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('请求超时，请检查后端服务是否运行');
    }
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('无法连接到后端API，请确保后端服务正在运行');
    }
    throw error;
  }
}

/**
 * 获取趋势分析
 */
export async function getTrends(params?: {
  days?: number;
  role_family?: string;
  seniority?: string;
  location?: string;
}): Promise<TrendsResponse> {
  const queryParams = new URLSearchParams();
  if (params?.days) queryParams.append('days', params.days.toString());
  if (params?.role_family) queryParams.append('role_family', params.role_family);
  if (params?.seniority) queryParams.append('seniority', params.seniority);
  if (params?.location) queryParams.append('location', params.location);
  
  const url = `${API_BASE_URL}/analytics/trends${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to fetch trends: ${response.status} ${response.statusText} - ${errorText}`);
    }
    
    return response.json();
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('请求超时，请检查后端服务是否运行在 http://127.0.0.1:8000');
    }
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('无法连接到后端API，请确保后端服务正在运行 (http://127.0.0.1:8000)');
    }
    throw error;
  }
}

/**
 * 获取时间趋势分析
 */
export async function getTimeTrends(params?: {
  days?: number;
  granularity?: 'day' | 'week' | 'month';
  role_family?: string;
  seniority?: string;
  location?: string;
}): Promise<TimeTrendsResponse> {
  const queryParams = new URLSearchParams();
  if (params?.days) queryParams.append('days', params.days.toString());
  if (params?.granularity) queryParams.append('granularity', params.granularity);
  if (params?.role_family) queryParams.append('role_family', params.role_family);
  if (params?.seniority) queryParams.append('seniority', params.seniority);
  if (params?.location) queryParams.append('location', params.location);
  
  const url = `${API_BASE_URL}/analytics/time-trends${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30秒超时
    
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to fetch time trends: ${response.status} ${response.statusText} - ${errorText}`);
    }
    
    return response.json();
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('请求超时，请检查后端服务是否运行在 http://127.0.0.1:8000');
    }
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('无法连接到后端API，请确保后端服务正在运行 (http://127.0.0.1:8000)');
    }
    throw error;
  }
}

/**
 * 获取地理位置分析
 */
export async function getLocationAnalysis(params?: {
  days?: number;
  role_family?: string;
  seniority?: string;
  location?: string;
}): Promise<LocationAnalysisResponse> {
  const queryParams = new URLSearchParams();
  if (params?.days) queryParams.append('days', params.days.toString());
  if (params?.role_family) queryParams.append('role_family', params.role_family);
  if (params?.seniority) queryParams.append('seniority', params.seniority);
  if (params?.location) queryParams.append('location', params.location);
  
  const url = `${API_BASE_URL}/analytics/location${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  
  try {
    const response = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch location analysis: ${response.status}`);
    }
    
    return response.json();
  } catch (error) {
    throw error;
  }
}

/**
 * 获取公司分析
 */
export async function getCompanyAnalysis(params?: {
  days?: number;
  role_family?: string;
  seniority?: string;
  location?: string;
}): Promise<CompanyAnalysisResponse> {
  const queryParams = new URLSearchParams();
  if (params?.days) queryParams.append('days', params.days.toString());
  if (params?.role_family) queryParams.append('role_family', params.role_family);
  if (params?.seniority) queryParams.append('seniority', params.seniority);
  if (params?.location) queryParams.append('location', params.location);
  
  const url = `${API_BASE_URL}/analytics/company${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  
  try {
    const response = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch company analysis: ${response.status}`);
    }
    
    return response.json();
  } catch (error) {
    throw error;
  }
}

/**
 * 获取经验要求分析
 */
export async function getExperienceAnalysis(params?: {
  days?: number;
  role_family?: string;
  seniority?: string;
  location?: string;
}): Promise<ExperienceAnalysisResponse> {
  const queryParams = new URLSearchParams();
  if (params?.days) queryParams.append('days', params.days.toString());
  if (params?.role_family) queryParams.append('role_family', params.role_family);
  if (params?.seniority) queryParams.append('seniority', params.seniority);
  if (params?.location) queryParams.append('location', params.location);
  
  const url = `${API_BASE_URL}/analytics/experience${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  
  try {
    const response = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch experience analysis: ${response.status}`);
    }
    
    return response.json();
  } catch (error) {
    throw error;
  }
}

/**
 * 获取学历要求分析
 */
export async function getEducationAnalysis(params?: {
  days?: number;
  role_family?: string;
  seniority?: string;
  location?: string;
}): Promise<EducationAnalysisResponse> {
  const queryParams = new URLSearchParams();
  if (params?.days) queryParams.append('days', params.days.toString());
  if (params?.role_family) queryParams.append('role_family', params.role_family);
  if (params?.seniority) queryParams.append('seniority', params.seniority);
  if (params?.location) queryParams.append('location', params.location);
  
  const url = `${API_BASE_URL}/analytics/education${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  
  try {
    const response = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch education analysis: ${response.status}`);
    }
    
    return response.json();
  } catch (error) {
    throw error;
  }
}

/**
 * 获取行业分析
 */
export async function getIndustryAnalysis(params?: {
  days?: number;
  role_family?: string;
  seniority?: string;
  location?: string;
}): Promise<IndustryAnalysisResponse> {
  const queryParams = new URLSearchParams();
  if (params?.days) queryParams.append('days', params.days.toString());
  if (params?.role_family) queryParams.append('role_family', params.role_family);
  if (params?.seniority) queryParams.append('seniority', params.seniority);
  if (params?.location) queryParams.append('location', params.location);
  
  const url = `${API_BASE_URL}/analytics/industry${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  
  try {
    const response = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch industry analysis: ${response.status}`);
    }
    
    return response.json();
  } catch (error) {
    throw error;
  }
}

/**
 * 获取数据来源分析
 */
export async function getSourceAnalysis(params?: {
  days?: number;
  role_family?: string;
  seniority?: string;
  location?: string;
}): Promise<SourceAnalysisResponse> {
  const queryParams = new URLSearchParams();
  if (params?.days) queryParams.append('days', params.days.toString());
  if (params?.role_family) queryParams.append('role_family', params.role_family);
  if (params?.seniority) queryParams.append('seniority', params.seniority);
  if (params?.location) queryParams.append('location', params.location);
  
  const url = `${API_BASE_URL}/analytics/source${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  
  try {
    const response = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch source analysis: ${response.status}`);
    }
    
    return response.json();
  } catch (error) {
    throw error;
  }
}

/**
 * 获取技能组合分析
 */
export async function getSkillCombinationAnalysis(params?: {
  days?: number;
  role_family?: string;
  seniority?: string;
  location?: string;
}): Promise<SkillCombinationAnalysisResponse> {
  const queryParams = new URLSearchParams();
  if (params?.days) queryParams.append('days', params.days.toString());
  if (params?.role_family) queryParams.append('role_family', params.role_family);
  if (params?.seniority) queryParams.append('seniority', params.seniority);
  if (params?.location) queryParams.append('location', params.location);
  
  const url = `${API_BASE_URL}/analytics/skill-combination${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  
  try {
    const response = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch skill combination analysis: ${response.status}`);
    }
    
    return response.json();
  } catch (error) {
    throw error;
  }
}

/**
 * 手动触发抓取任务
 */
export async function triggerScrape(params?: {
  max_per_keyword?: number;
  headless?: boolean;
  browser?: string;
}): Promise<{
  message: string;
  status: string;
  max_per_keyword: number;
  headless: boolean;
  browser: string;
  note: string;
}> {
  const url = `${API_BASE_URL}/scraper/trigger`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params || {}),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to trigger scrape: ${response.status} ${response.statusText} - ${errorText}`);
    }
    
    return response.json();
  } catch (error) {
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('无法连接到后端API，请确保后端服务正在运行 (http://127.0.0.1:8000)');
    }
    throw error;
  }
}