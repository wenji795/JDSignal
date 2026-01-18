"""分析和趋势API端点"""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func, and_, or_
from typing import Dict, Any, Optional
from collections import Counter
from datetime import datetime, timedelta

from app.database import get_session
from app.models import Job, Extraction, Seniority

# 需要过滤的通用关键词（与keyword_extractor.py保持一致）
COMMON_KEYWORDS_TO_FILTER = {
    'seek', 'seek.co.nz', 'linkedin', 'indeed',
    'nz', 'new zealand', 'cbd', 'auckland', 'wellington', 'christchurch',
    'hamilton', 'dunedin', 'tauranga', 'new', 'zealand',
    'job', 'jobs', 'position', 'positions', 'role', 'roles',
    'opportunity', 'opportunities', 'vacancy', 'vacancies',
    'apply', 'application', 'applicant', 'applicants', 'candidate', 'candidates',
    'company', 'companies', 'employer', 'employers', 'organisation', 'organization',
    'please', 'thank', 'thanks', 'regards', 'sincerely',
    'full time', 'full-time', 'part time', 'part-time', 'permanent', 'contract',
    'temporary', 'temp', 'casual',
    'remote', 'hybrid', 'onsite', 'on-site', 'work from home', 'wfh',
    'salary', 'wage', 'wages', 'compensation', 'benefits', 'benefit',
    'package', 'remuneration',
    'experience', 'years', 'year', 'month', 'months', 'yr', 'yrs',
    'required', 'requirement', 'requirements', 'qualification', 'qualifications',
    'qualify', 'qualified', 'qualifying',
    'skill', 'skills', 'ability', 'abilities', 'capability', 'capabilities',
    'team', 'teams', 'work', 'working', 'workplace', 'workforce',
    'it', 'information technology',  # IT是通用术语，对分析没有价值
    'australia', 'au', 'us', 'usa', 'united states', 'america',
    'location', 'locations', 'area', 'areas', 'region', 'regions', 'city', 'cities',
    'description', 'about', 'overview', 'summary', 'detail', 'details',
    'contact', 'email', 'phone', 'telephone', 'website', 'www', 'http', 'https',
    'click', 'here', 'more', 'information', 'details', 'view', 'see',
    'equal', 'opportunity', 'employer', 'eoe', 'eeo', 'diversity', 'inclusive',
    'akl', 'wlg', 'chc', 'ham', 'dun', 'tau'  # 城市缩写
}

def should_filter_keyword(term: str) -> bool:
    """检查关键词是否应该被过滤"""
    if not term or len(term.strip()) == 0:
        return True
    
    term_lower = term.lower().strip()
    term_upper = term.upper().strip()
    
    # 检查是否完全匹配过滤列表（大小写不敏感）
    if term_lower in COMMON_KEYWORDS_TO_FILTER:
        return True
    
    # 检查大写形式（处理 "SEEK", "NZ", "CBD" 等全大写词）
    if term_upper.lower() in COMMON_KEYWORDS_TO_FILTER:
        return True
    
    # 特殊处理：过滤掉常见的2-3字母缩写（如果不是技术术语）
    if len(term_lower) <= 3:
        tech_short_acronyms = {'api', 'sql', 'xml', 'json', 'css', 'html', 'url', 'uri',
                               'aws', 'gcp', 'ci', 'cd', 'ui', 'ux', 'qa', 'sdk', 'ide',
                               'cli', 'ssh', 'tls', 'ssl', 'jwt', 'rpc', 'iot', 'ml', 'ai',
                               'etl', 'bi', 'crm', 'erp', 'dns', 'cdn', 'vpn', 'acl', 'iso',
                               'tdd', 'bdd', 'ddd', 'k8s', 'pdf', 'csv', 'tsv', 'yaml'}
        if term_lower not in tech_short_acronyms:
            common_short = {'nz', 'au', 'us', 'uk', 'eu', 'cbd', 'hr', 'ceo', 'cto', 'cfo',
                           'wfh', 'eoe', 'eeo', 'www', 'akl', 'wlg', 'chc', 'ham', 'dun', 'tau', 'it'}
            if term_lower in common_short:
                return True
    
    return False

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/trends", response_model=Dict[str, Any])
def get_trends(
    days: int = Query(30, description="时间窗口（天数）"),
    role_family: Optional[str] = Query(None, description="按角色族过滤"),
    seniority: Optional[str] = Query(None, description="按资历级别过滤（支持graduate/junior/intermediate/mid/senior）"),
    location: Optional[str] = Query(None, description="按地点过滤（支持部分匹配，如'New Zealand'或'NZ'）"),
    session: Session = Depends(get_session)
):
    """
    获取关键词趋势分析
    
    返回：
    - total_jobs: 总职位数
    - count_by_role_family: 按角色族统计
    - count_by_seniority: 按资历级别统计
    - top_keywords: 前30个关键词及计数
    - top_keywords_by_role_family: 每个角色族的前10个关键词
    - keyword_growth: 关键词增长趋势（前半段 vs 后半段）
    """
    from sqlmodel import or_
    
    # 计算时间窗口
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 构建基础查询
    job_query = select(Job).where(Job.captured_at >= start_date, Job.captured_at <= end_date)
    
    # 应用过滤条件
    if role_family:
        job_query = job_query.where(Job.role_family == role_family)
    if seniority:
        # 映射前端的显示名称到实际的枚举值
        seniority_mapping = {
            'graduate': Seniority.JUNIOR,
            'junior': Seniority.JUNIOR,
            'intermediate': Seniority.MID,
            'mid': Seniority.MID,
            'senior': Seniority.SENIOR
        }
        # 如果传入的是映射值，使用映射；否则尝试直接转换
        mapped_seniority = seniority_mapping.get(seniority.lower())
        if mapped_seniority:
            job_query = job_query.where(Job.seniority == mapped_seniority)
        else:
            # 尝试直接转换为枚举
            try:
                job_query = job_query.where(Job.seniority == Seniority(seniority.lower()))
            except ValueError:
                pass  # 无效的seniority值，忽略
    if location:
        # 支持部分匹配
        job_query = job_query.where(Job.location.contains(location))
    
    jobs = session.exec(job_query).all()
    job_ids = [job.id for job in jobs]
    
    # 1. 总职位数
    total_jobs = len(jobs)
    
    # 2. 按角色族统计
    count_by_role_family = Counter()
    for job in jobs:
        if job.role_family:
            count_by_role_family[job.role_family] += 1
    
    # 3. 按资历级别统计
    count_by_seniority = Counter()
    for job in jobs:
        if job.seniority:
            count_by_seniority[job.seniority.value] += 1
    
    # 4. 获取提取结果和对应的Job
    if job_ids:
        extraction_query = select(Extraction).where(Extraction.job_id.in_(job_ids))
        extractions = session.exec(extraction_query).all()
        
        # 创建job_id到job的映射
        job_map = {job.id: job for job in jobs}
        extractions_with_jobs = [(ext, job_map.get(ext.job_id)) for ext in extractions if ext.job_id in job_map]
    else:
        extractions_with_jobs = []
    
    # 5. 统计所有关键词（top 30）
    keyword_counter = Counter()
    keyword_by_role_family = {}  # role_family -> Counter
    
    for extraction, job in extractions_with_jobs:
        if not job:
            continue
        keywords_data = extraction.keywords_json.get("keywords", [])
        for kw in keywords_data:
            term = kw.get("term", "")
            # 过滤掉通用关键词
            if term and not should_filter_keyword(term):
                keyword_counter[term] += 1
                
                # 按角色族统计
                if job.role_family:
                    if job.role_family not in keyword_by_role_family:
                        keyword_by_role_family[job.role_family] = Counter()
                    keyword_by_role_family[job.role_family][term] += 1
    
    top_keywords = [{"term": term, "count": count} for term, count in keyword_counter.most_common(30)]
    
    # 6. 按角色族统计top关键词（每个角色族top 20，过滤通用词）
    top_keywords_by_role_family = {}
    for role_fam, counter in keyword_by_role_family.items():
        # 过滤掉通用关键词后再统计
        filtered_counter = Counter({term: count for term, count in counter.items() 
                                    if not should_filter_keyword(term)})
        top_keywords_by_role_family[role_fam] = [
            {"term": term, "count": count} for term, count in filtered_counter.most_common(20)
        ]
    
    # 7. 如果指定了role_family筛选，返回该角色族的top20关键词
    selected_role_family_top_keywords = None
    if role_family and role_family in top_keywords_by_role_family:
        selected_role_family_top_keywords = top_keywords_by_role_family[role_family]
    
    # 8. 关键词增长分析（比较前半段和后半段）
    keyword_growth = {}
    if len(jobs) > 1:
        # 按captured_at排序
        sorted_jobs = sorted(jobs, key=lambda j: j.captured_at)
        mid_point = len(sorted_jobs) // 2
        first_half_jobs = sorted_jobs[:mid_point]
        second_half_jobs = sorted_jobs[mid_point:]
        
        first_half_ids = {job.id for job in first_half_jobs}
        second_half_ids = {job.id for job in second_half_jobs}
        
        # 统计前半段关键词（过滤通用词）
        first_half_counter = Counter()
        second_half_counter = Counter()
        
        for extraction, job in extractions_with_jobs:
            if not job:
                continue
            keywords_data = extraction.keywords_json.get("keywords", [])
            for kw in keywords_data:
                term = kw.get("term", "")
                # 过滤掉通用关键词
                if term and not should_filter_keyword(term):
                    if job.id in first_half_ids:
                        first_half_counter[term] += 1
                    elif job.id in second_half_ids:
                        second_half_counter[term] += 1
        
        # 计算增长
        all_terms = set(first_half_counter.keys()) | set(second_half_counter.keys())
        for term in all_terms:
            first_count = first_half_counter.get(term, 0)
            second_count = second_half_counter.get(term, 0)
            
            delta = second_count - first_count
            if first_count > 0:
                percent_change = (delta / first_count) * 100
            elif second_count > 0:
                percent_change = 100.0  # 从0到有值，增长100%
            else:
                percent_change = 0.0
            
            keyword_growth[term] = {
                "first_half_count": first_count,
                "second_half_count": second_count,
                "delta": delta,
                "percent_change": round(percent_change, 2)
            }
    
    result = {
        "total_jobs": total_jobs,
        "count_by_role_family": dict(count_by_role_family),
        "count_by_seniority": dict(count_by_seniority),
        "top_keywords": top_keywords,
        "top_keywords_by_role_family": top_keywords_by_role_family,
        "keyword_growth": keyword_growth
    }
    
    # 如果指定了role_family筛选，添加该角色族的top20关键词
    if selected_role_family_top_keywords is not None:
        result["selected_role_family_top_keywords"] = selected_role_family_top_keywords
    
    return result