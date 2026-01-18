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
}

/**
 * 获取所有职位
 */
export async function getJobs(params?: {
  status?: string;
  role_family?: string;
  seniority?: string;
  keyword?: string;
  location?: string;
}): Promise<Job[]> {
  const queryParams = new URLSearchParams();
  if (params?.status) queryParams.append('status', params.status);
  if (params?.role_family) queryParams.append('role_family', params.role_family);
  if (params?.seniority) queryParams.append('seniority', params.seniority);
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