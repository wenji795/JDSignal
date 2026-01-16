"""分析和趋势API端点"""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func, and_, or_
from typing import Dict, Any, Optional
from collections import Counter
from datetime import datetime, timedelta

from app.database import get_session
from app.models import Job, Extraction, Seniority

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/trends", response_model=Dict[str, Any])
def get_trends(
    days: int = Query(30, description="时间窗口（天数）"),
    role_family: Optional[str] = Query(None, description="按角色族过滤"),
    seniority: Optional[Seniority] = Query(None, description="按资历级别过滤"),
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
        job_query = job_query.where(Job.seniority == seniority)
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
            if term:
                keyword_counter[term] += 1
                
                # 按角色族统计
                if job.role_family:
                    if job.role_family not in keyword_by_role_family:
                        keyword_by_role_family[job.role_family] = Counter()
                    keyword_by_role_family[job.role_family][term] += 1
    
    top_keywords = [{"term": term, "count": count} for term, count in keyword_counter.most_common(30)]
    
    # 6. 按角色族统计top关键词（每个角色族top 20）
    top_keywords_by_role_family = {}
    for role_fam, counter in keyword_by_role_family.items():
        top_keywords_by_role_family[role_fam] = [
            {"term": term, "count": count} for term, count in counter.most_common(20)
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
        
        # 统计前半段关键词
        first_half_counter = Counter()
        second_half_counter = Counter()
        
        for extraction, job in extractions_with_jobs:
            if not job:
                continue
            keywords_data = extraction.keywords_json.get("keywords", [])
            for kw in keywords_data:
                term = kw.get("term", "")
                if term:
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