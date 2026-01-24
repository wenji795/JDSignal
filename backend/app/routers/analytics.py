"""分析和趋势API端点"""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func, and_, or_
from typing import Dict, Any, Optional
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import re

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

def normalize_keyword(term: str) -> str:
    """
    规范化关键词，将变体统一为标准形式
    例如：CI, CD, CI/CD, CI CD -> CI/CD
         .NET, NET -> .NET
    """
    if not term:
        return term
    
    term_stripped = term.strip()
    term_upper = term_stripped.upper()
    
    # .NET相关：NET, .net -> .NET（统一为标准形式）
    if term_upper == 'NET' or term_upper == '.NET':
        return '.NET'
    
    # CI/CD相关：CI, CD, CI/CD, CI CD -> CI/CD
    # 注意：这个在调用处处理，因为需要合并计数
    
    return term_stripped


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
    
    # 过滤掉年份（4位数字，范围1900-2100）
    if term.isdigit() and len(term) == 4:
        try:
            year = int(term)
            if 1900 <= year <= 2100:
                return True
        except ValueError:
            pass
    
    # 过滤掉月份名称（全称和缩写）- 使用小写比较
    month_names = {
        'january', 'february', 'march', 'april', 'may', 'june',
        'july', 'august', 'september', 'october', 'november', 'december',
        'jan', 'feb', 'mar', 'apr', 'may', 'jun',
        'jul', 'aug', 'sep', 'sept', 'oct', 'nov', 'dec'
    }
    if term_lower in month_names:
        return True
    
    # 过滤掉日期格式（如 01/01/2024, 2024-01-01, 01-01-2024）
    date_patterns = [
        r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$',  # 01/01/2024, 01-01-2024
        r'^\d{4}[/-]\d{1,2}[/-]\d{1,2}$',     # 2024-01-01, 2024/01/01
        r'^\d{1,2}\.\d{1,2}\.\d{2,4}$',      # 01.01.2024
    ]
    for pattern in date_patterns:
        if re.match(pattern, term):
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
    - top_keywords_by_role_family: 每个角色族的前20个关键词
    - monthly_comparison: 上月vs本月关键词对比
        - comparison: 总体Top 7变化最大的关键词
        - by_role_family: 按角色族分组的Top 5关键词变化
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
    
    # 4. 获取提取结果和对应的Job（只统计有Extraction的Job，确保数据一致性）
    if job_ids:
        extraction_query = select(Extraction).where(Extraction.job_id.in_(job_ids))
        extractions = session.exec(extraction_query).all()
        
        # 创建job_id到job的映射
        job_map = {job.id: job for job in jobs}
        # 只保留有Extraction的Job
        extractions_with_jobs = [(ext, job_map.get(ext.job_id)) for ext in extractions if ext.job_id in job_map]
        
        # 获取有Extraction的Job ID集合
        jobs_with_extraction_ids = {ext.job_id for ext in extractions}
        # 过滤出有Extraction的Job
        jobs_with_extraction = [job for job in jobs if job.id in jobs_with_extraction_ids]
    else:
        extractions_with_jobs = []
        jobs_with_extraction = []
    
    # 1. 总职位数（只统计有Extraction的Job，确保数据一致性）
    total_jobs = len(jobs_with_extraction)
    
    # 统计所有Job数量（用于显示提取覆盖率）
    total_jobs_all = len(jobs)
    
    # 2. 按角色族统计（只统计有Extraction的Job）
    count_by_role_family = Counter()
    for job in jobs_with_extraction:
        if job.role_family:
            count_by_role_family[job.role_family] += 1
    
    # 3. 按资历级别统计（只统计有Extraction的Job）
    count_by_seniority = Counter()
    for job in jobs_with_extraction:
        if job.seniority:
            count_by_seniority[job.seniority.value] += 1
    
    # 5. 统计所有关键词（top 30）
    keyword_counter = Counter()
    keyword_by_role_family = {}  # role_family -> Counter
    
    for extraction, job in extractions_with_jobs:
        if not job:
            continue
        keywords_data = extraction.keywords_json.get("keywords", [])
        for kw in keywords_data:
            # 处理两种格式：字符串列表或字典列表
            if isinstance(kw, dict):
                term = kw.get("term", "")
            elif isinstance(kw, str):
                term = kw
            else:
                continue  # 跳过无效格式
            
            # 过滤掉通用关键词
            if term and not should_filter_keyword(term):
                # 规范化关键词
                normalized_term = normalize_keyword(term)
                
                # 处理CI/CD变体：CI/CD, CI CD -> CI/CD（统一格式）
                term_upper = normalized_term.upper().strip()
                if term_upper == 'CI/CD' or term_upper == 'CI CD':
                    normalized_term = 'CI/CD'
                # 注意：单独的CI或CD保留原样，不强制合并
                
                keyword_counter[normalized_term] += 1
                
                # 按角色族统计
                if job.role_family:
                    if job.role_family not in keyword_by_role_family:
                        keyword_by_role_family[job.role_family] = Counter()
                    keyword_by_role_family[job.role_family][normalized_term] += 1
    
    # 后处理：如果CI和CD同时存在，合并为CI/CD
    if 'CI' in keyword_counter and 'CD' in keyword_counter:
        ci_count = keyword_counter['CI']
        cd_count = keyword_counter['CD']
        # 合并计数（取较大值，或相加，这里选择相加）
        combined_count = ci_count + cd_count
        # 如果CI/CD已经存在，也加上它的计数
        if 'CI/CD' in keyword_counter:
            combined_count += keyword_counter['CI/CD']
        keyword_counter['CI/CD'] = combined_count
        # 删除单独的CI和CD
        del keyword_counter['CI']
        del keyword_counter['CD']
    
    # 同样处理按角色族的统计
    for role_fam, counter in keyword_by_role_family.items():
        if 'CI' in counter and 'CD' in counter:
            ci_count = counter['CI']
            cd_count = counter['CD']
            combined_count = ci_count + cd_count
            if 'CI/CD' in counter:
                combined_count += counter['CI/CD']
            counter['CI/CD'] = combined_count
            del counter['CI']
            del counter['CD']
    
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
    
    # 8. 上月vs本月关键词比较
    # 注意：月度比较需要独立查询，不受days参数限制，确保能获取到上个月的数据
    monthly_comparison = {}
    now = datetime.utcnow()
    # 计算本月开始和结束时间
    current_month_start = datetime(now.year, now.month, 1)
    current_month_end = now
    # 计算上月开始和结束时间
    # 先计算上个月的第一天
    if now.month == 1:
        last_month_start = datetime(now.year - 1, 12, 1)
    else:
        last_month_start = datetime(now.year, now.month - 1, 1)
    # 上个月的最后一天是本月第一天减1天
    last_month_end = current_month_start - timedelta(days=1)
    
    # 独立查询本月和上月的职位（不受days参数限制）
    monthly_job_query = select(Job).where(
        (Job.captured_at >= last_month_start) & (Job.captured_at <= current_month_end)
    )
    
    # 应用相同的过滤条件（role_family, seniority, location）
    if role_family:
        monthly_job_query = monthly_job_query.where(Job.role_family == role_family)
    if seniority:
        seniority_mapping = {
            'graduate': Seniority.JUNIOR,
            'junior': Seniority.JUNIOR,
            'intermediate': Seniority.MID,
            'mid': Seniority.MID,
            'senior': Seniority.SENIOR
        }
        mapped_seniority = seniority_mapping.get(seniority.lower())
        if mapped_seniority:
            monthly_job_query = monthly_job_query.where(Job.seniority == mapped_seniority)
        else:
            try:
                monthly_job_query = monthly_job_query.where(Job.seniority == Seniority(seniority.lower()))
            except ValueError:
                pass
    if location:
        monthly_job_query = monthly_job_query.where(Job.location.contains(location))
    
    monthly_jobs = session.exec(monthly_job_query).all()
    monthly_job_ids = [job.id for job in monthly_jobs]
    
    # 分别获取本月和上月的职位
    current_month_jobs_all = [j for j in monthly_jobs if current_month_start <= j.captured_at <= current_month_end]
    last_month_jobs_all = [j for j in monthly_jobs if last_month_start <= j.captured_at <= last_month_end]
    
    if current_month_jobs_all or last_month_jobs_all:
        # 获取月度比较相关的提取结果
        if monthly_job_ids:
            monthly_extraction_query = select(Extraction).where(Extraction.job_id.in_(monthly_job_ids))
            monthly_extractions = session.exec(monthly_extraction_query).all()
            monthly_job_map = {job.id: job for job in monthly_jobs}
            monthly_extractions_with_jobs = [(ext, monthly_job_map.get(ext.job_id)) for ext in monthly_extractions if ext.job_id in monthly_job_map]
            
            # 获取有Extraction的Job ID集合
            monthly_jobs_with_extraction_ids = {ext.job_id for ext in monthly_extractions}
            # 只保留有Extraction的Job
            current_month_jobs = [j for j in current_month_jobs_all if j.id in monthly_jobs_with_extraction_ids]
            last_month_jobs = [j for j in last_month_jobs_all if j.id in monthly_jobs_with_extraction_ids]
        else:
            monthly_extractions_with_jobs = []
            current_month_jobs = []
            last_month_jobs = []
        
        # 总体关键词统计（所有角色族）
        current_month_counter = Counter()
        last_month_counter = Counter()
        
        # 按角色族分组的关键词统计
        current_month_by_role_family = {}  # role_family -> Counter
        last_month_by_role_family = {}     # role_family -> Counter
        
        # 获取本月和上月的Job ID集合（只包含有Extraction的）
        current_month_job_ids = {job.id for job in current_month_jobs}
        last_month_job_ids = {job.id for job in last_month_jobs}
        
        for extraction, job in monthly_extractions_with_jobs:
            if not job:
                continue
            keywords_data = extraction.keywords_json.get("keywords", [])
            for kw in keywords_data:
                # 处理两种格式：字符串列表或字典列表
                if isinstance(kw, dict):
                    term = kw.get("term", "")
                elif isinstance(kw, str):
                    term = kw
                else:
                    continue  # 跳过无效格式
                
                # 过滤掉通用关键词
                if term and not should_filter_keyword(term):
                    # 规范化关键词
                    normalized_term = normalize_keyword(term)
                    
                    # 处理CI/CD变体：CI/CD, CI CD -> CI/CD（统一格式）
                    term_upper = normalized_term.upper().strip()
                    if term_upper == 'CI/CD' or term_upper == 'CI CD':
                        normalized_term = 'CI/CD'
                    # 注意：单独的CI或CD保留原样，不强制合并
                    
                    # 总体统计
                    if job.id in current_month_job_ids:
                        current_month_counter[normalized_term] += 1
                    elif job.id in last_month_job_ids:
                        last_month_counter[normalized_term] += 1
                    
                    # 按角色族统计
                    if job.role_family:
                        if job.id in current_month_job_ids:
                            if job.role_family not in current_month_by_role_family:
                                current_month_by_role_family[job.role_family] = Counter()
                            current_month_by_role_family[job.role_family][normalized_term] += 1
                        elif job.id in last_month_job_ids:
                            if job.role_family not in last_month_by_role_family:
                                last_month_by_role_family[job.role_family] = Counter()
                            last_month_by_role_family[job.role_family][normalized_term] += 1
        
        # 后处理：如果CI和CD同时存在，合并为CI/CD
        if 'CI' in current_month_counter and 'CD' in current_month_counter:
            ci_count = current_month_counter['CI']
            cd_count = current_month_counter['CD']
            combined_count = ci_count + cd_count
            if 'CI/CD' in current_month_counter:
                combined_count += current_month_counter['CI/CD']
            current_month_counter['CI/CD'] = combined_count
            del current_month_counter['CI']
            del current_month_counter['CD']
        
        if 'CI' in last_month_counter and 'CD' in last_month_counter:
            ci_count = last_month_counter['CI']
            cd_count = last_month_counter['CD']
            combined_count = ci_count + cd_count
            if 'CI/CD' in last_month_counter:
                combined_count += last_month_counter['CI/CD']
            last_month_counter['CI/CD'] = combined_count
            del last_month_counter['CI']
            del last_month_counter['CD']
        
        # 同样处理按角色族的统计
        for role_fam in set(current_month_by_role_family.keys()) | set(last_month_by_role_family.keys()):
            current_rf = current_month_by_role_family.get(role_fam, Counter())
            last_rf = last_month_by_role_family.get(role_fam, Counter())
            
            if 'CI' in current_rf and 'CD' in current_rf:
                ci_count = current_rf['CI']
                cd_count = current_rf['CD']
                combined_count = ci_count + cd_count
                if 'CI/CD' in current_rf:
                    combined_count += current_rf['CI/CD']
                current_rf['CI/CD'] = combined_count
                del current_rf['CI']
                del current_rf['CD']
            
            if 'CI' in last_rf and 'CD' in last_rf:
                ci_count = last_rf['CI']
                cd_count = last_rf['CD']
                combined_count = ci_count + cd_count
                if 'CI/CD' in last_rf:
                    combined_count += last_rf['CI/CD']
                last_rf['CI/CD'] = combined_count
                del last_rf['CI']
                del last_rf['CD']
        
        # 计算总体变化（Top 7）
        all_monthly_terms = set(current_month_counter.keys()) | set(last_month_counter.keys())
        monthly_comparison_data = []
        
        for term in all_monthly_terms:
            current_count = current_month_counter.get(term, 0)
            last_count = last_month_counter.get(term, 0)
            
            delta = current_count - last_count
            if last_count > 0:
                percent_change = (delta / last_count) * 100
            elif current_count > 0:
                percent_change = 100.0  # 新增关键词，增长100%
            else:
                percent_change = 0.0
            
            monthly_comparison_data.append({
                "term": term,
                "current_month_count": current_count,
                "last_month_count": last_count,
                "delta": delta,
                "percent_change": round(percent_change, 2),
                "status": "new" if last_count == 0 and current_count > 0 else 
                         "increased" if delta > 0 else 
                         "decreased" if delta < 0 else "unchanged"
            })
        
        # 按变化量排序（优先显示增长最多的），取Top 7
        monthly_comparison_data.sort(key=lambda x: (x["delta"], x["current_month_count"]), reverse=True)
        
        # 按角色族计算变化（每个角色族Top 5）
        monthly_comparison_by_role_family = {}
        all_role_families = set(current_month_by_role_family.keys()) | set(last_month_by_role_family.keys())
        
        for role_fam in all_role_families:
            current_rf_counter = current_month_by_role_family.get(role_fam, Counter())
            last_rf_counter = last_month_by_role_family.get(role_fam, Counter())
            
            rf_terms = set(current_rf_counter.keys()) | set(last_rf_counter.keys())
            rf_comparison_data = []
            
            for term in rf_terms:
                current_count = current_rf_counter.get(term, 0)
                last_count = last_rf_counter.get(term, 0)
                
                delta = current_count - last_count
                if last_count > 0:
                    percent_change = (delta / last_count) * 100
                elif current_count > 0:
                    percent_change = 100.0
                else:
                    percent_change = 0.0
                
                rf_comparison_data.append({
                    "term": term,
                    "current_month_count": current_count,
                    "last_month_count": last_count,
                    "delta": delta,
                    "percent_change": round(percent_change, 2),
                    "status": "new" if last_count == 0 and current_count > 0 else 
                             "increased" if delta > 0 else 
                             "decreased" if delta < 0 else "unchanged"
                })
            
            # 按变化量排序，取Top 5
            rf_comparison_data.sort(key=lambda x: (x["delta"], x["current_month_count"]), reverse=True)
            monthly_comparison_by_role_family[role_fam] = rf_comparison_data[:5]
        
        monthly_comparison = {
            "current_month": {
                "start": current_month_start.isoformat(),
                "end": current_month_end.isoformat(),
                "job_count": len(current_month_jobs)
            },
            "last_month": {
                "start": last_month_start.isoformat(),
                "end": last_month_end.isoformat(),
                "job_count": len(last_month_jobs)
            },
            "comparison": monthly_comparison_data[:7],  # Top 7变化最大的关键词（总体）
            "by_role_family": monthly_comparison_by_role_family  # 按角色族分组的Top 5
        }
    
    # 9. 关键词增长分析（已废弃，改用monthly_comparison）
    # 保留此字段以保持API兼容性，但使用空字典
    keyword_growth = {}
    
    # 计算提取覆盖率
    extraction_coverage = {
        "total_jobs_all": total_jobs_all,  # 所有Job数量（包括未提取的）
        "total_jobs_with_extraction": total_jobs,  # 有Extraction的Job数量
        "coverage_rate": round((total_jobs / total_jobs_all * 100) if total_jobs_all > 0 else 0, 2)  # 覆盖率百分比
    }
    
    result = {
        "total_jobs": total_jobs,  # 只统计有Extraction的Job
        "count_by_role_family": dict(count_by_role_family),
        "count_by_seniority": dict(count_by_seniority),
        "top_keywords": top_keywords,
        "top_keywords_by_role_family": top_keywords_by_role_family,
        "keyword_growth": keyword_growth,
        "monthly_comparison": monthly_comparison,
        "extraction_coverage": extraction_coverage  # 添加提取覆盖率信息
    }
    
    # 如果指定了role_family筛选，添加该角色族的top20关键词
    if selected_role_family_top_keywords is not None:
        result["selected_role_family_top_keywords"] = selected_role_family_top_keywords
    
    return result


@router.get("/time-trends", response_model=Dict[str, Any])
def get_time_trends(
    days: int = Query(90, description="时间窗口（天数）"),
    granularity: str = Query("day", description="时间粒度：day/week/month"),
    role_family: Optional[str] = Query(None, description="按角色族过滤"),
    seniority: Optional[str] = Query(None, description="按资历级别过滤"),
    location: Optional[str] = Query(None, description="按地点过滤"),
    session: Session = Depends(get_session)
):
    """
    获取时间趋势分析（基于posted_date）
    
    返回：
    - job_count_trend: 职位数量随时间变化
    - role_family_trends: 不同角色族的职位数量趋势
    - keyword_trends: Top 10关键词热度趋势
    - activity_summary: 招聘活跃度统计（按周/月）
    """
    
    # 验证granularity参数
    if granularity not in ["day", "week", "month"]:
        granularity = "day"
    
    # 计算时间窗口
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 构建基础查询 - 只查询有Extraction的Job，并且posted_date不为空
    job_query = select(Job).where(
        Job.posted_date.isnot(None),
        Job.posted_date >= start_date,
        Job.posted_date <= end_date
    )
    
    # 应用过滤条件
    if role_family:
        job_query = job_query.where(Job.role_family == role_family)
    if seniority:
        seniority_mapping = {
            'graduate': Seniority.JUNIOR,
            'junior': Seniority.JUNIOR,
            'intermediate': Seniority.MID,
            'mid': Seniority.MID,
            'senior': Seniority.SENIOR
        }
        mapped_seniority = seniority_mapping.get(seniority.lower())
        if mapped_seniority:
            job_query = job_query.where(Job.seniority == mapped_seniority)
        else:
            try:
                job_query = job_query.where(Job.seniority == Seniority(seniority.lower()))
            except ValueError:
                pass
    if location:
        job_query = job_query.where(Job.location.contains(location))
    
    jobs = session.exec(job_query).all()
    job_ids = [job.id for job in jobs]
    
    # 只获取有Extraction的Job
    if job_ids:
        extraction_query = select(Extraction).where(Extraction.job_id.in_(job_ids))
        extractions = session.exec(extraction_query).all()
        extraction_job_ids = {ext.job_id for ext in extractions}
        jobs_with_extraction = [job for job in jobs if job.id in extraction_job_ids]
    else:
        jobs_with_extraction = []
    
    # 创建job_id到job的映射
    job_map = {job.id: job for job in jobs_with_extraction}
    
    # 1. 职位数量随时间变化
    time_buckets = defaultdict(int)
    
    for job in jobs_with_extraction:
        if not job.posted_date:
            continue
        
        posted_date = job.posted_date
        
        # 根据granularity分组
        if granularity == "day":
            bucket_key = posted_date.strftime("%Y-%m-%d")
        elif granularity == "week":
            # 获取该周的周一日期
            days_since_monday = posted_date.weekday()
            monday = posted_date - timedelta(days=days_since_monday)
            bucket_key = monday.strftime("%Y-%m-%d")
        else:  # month
            bucket_key = posted_date.strftime("%Y-%m")
        
        time_buckets[bucket_key] += 1
    
    # 转换为列表并排序
    job_count_trend = [
        {"date": date, "count": count}
        for date, count in sorted(time_buckets.items())
    ]
    
    # 2. 不同角色族的职位数量趋势
    role_family_trends = defaultdict(lambda: defaultdict(int))
    
    for job in jobs_with_extraction:
        if not job.posted_date or not job.role_family:
            continue
        
        posted_date = job.posted_date
        
        # 根据granularity分组
        if granularity == "day":
            bucket_key = posted_date.strftime("%Y-%m-%d")
        elif granularity == "week":
            days_since_monday = posted_date.weekday()
            monday = posted_date - timedelta(days=days_since_monday)
            bucket_key = monday.strftime("%Y-%m-%d")
        else:  # month
            bucket_key = posted_date.strftime("%Y-%m")
        
        role_family_trends[job.role_family][bucket_key] += 1
    
    # 转换为字典格式
    role_family_trends_dict = {}
    for role_fam, buckets in role_family_trends.items():
        role_family_trends_dict[role_fam] = [
            {"date": date, "count": count}
            for date, count in sorted(buckets.items())
        ]
    
    # 3. Top 10关键词热度趋势
    # 先获取Top 10关键词
    keyword_counter = Counter()
    keyword_jobs_map = defaultdict(list)  # keyword -> list of jobs
    
    for extraction in extractions:
        if extraction.job_id not in job_map:
            continue
        job = job_map[extraction.job_id]
        if not job.posted_date:
            continue
        
        keywords_data = extraction.keywords_json.get("keywords", [])
        for kw in keywords_data:
            if isinstance(kw, dict):
                term = kw.get("term", "")
            elif isinstance(kw, str):
                term = kw
            else:
                continue
            
            if term and not should_filter_keyword(term):
                normalized_term = normalize_keyword(term)
                term_upper = normalized_term.upper().strip()
                if term_upper == 'CI/CD' or term_upper == 'CI CD':
                    normalized_term = 'CI/CD'
                
                keyword_counter[normalized_term] += 1
                keyword_jobs_map[normalized_term].append(job)
    
    # 处理CI/CD合并
    if 'CI' in keyword_counter and 'CD' in keyword_counter:
        ci_count = keyword_counter['CI']
        cd_count = keyword_counter['CD']
        combined_count = ci_count + cd_count
        if 'CI/CD' in keyword_counter:
            combined_count += keyword_counter['CI/CD']
        keyword_counter['CI/CD'] = combined_count
        # 合并job列表
        if 'CI/CD' not in keyword_jobs_map:
            keyword_jobs_map['CI/CD'] = []
        keyword_jobs_map['CI/CD'].extend(keyword_jobs_map.get('CI', []))
        keyword_jobs_map['CI/CD'].extend(keyword_jobs_map.get('CD', []))
        del keyword_counter['CI']
        del keyword_counter['CD']
        if 'CI' in keyword_jobs_map:
            del keyword_jobs_map['CI']
        if 'CD' in keyword_jobs_map:
            del keyword_jobs_map['CD']
    
    # 获取Top 10关键词
    top_10_keywords = [term for term, _ in keyword_counter.most_common(10)]
    
    # 计算每个关键词的时间趋势
    keyword_trends = {}
    for keyword in top_10_keywords:
        keyword_buckets = defaultdict(int)
        for job in keyword_jobs_map.get(keyword, []):
            if not job.posted_date:
                continue
            
            posted_date = job.posted_date
            
            if granularity == "day":
                bucket_key = posted_date.strftime("%Y-%m-%d")
            elif granularity == "week":
                days_since_monday = posted_date.weekday()
                monday = posted_date - timedelta(days=days_since_monday)
                bucket_key = monday.strftime("%Y-%m-%d")
            else:  # month
                bucket_key = posted_date.strftime("%Y-%m")
            
            keyword_buckets[bucket_key] += 1
        
        keyword_trends[keyword] = [
            {"date": date, "count": count}
            for date, count in sorted(keyword_buckets.items())
        ]
    
    # 4. 招聘活跃度统计（按周/月）
    activity_summary = {}
    
    # 按周统计
    weekly_activity = defaultdict(int)
    for job in jobs_with_extraction:
        if not job.posted_date:
            continue
        posted_date = job.posted_date
        days_since_monday = posted_date.weekday()
        monday = posted_date - timedelta(days=days_since_monday)
        week_key = monday.strftime("%Y-%m-%d")
        weekly_activity[week_key] += 1
    
    activity_summary["weekly"] = [
        {"week": week, "count": count}
        for week, count in sorted(weekly_activity.items())
    ]
    
    # 按月统计
    monthly_activity = defaultdict(int)
    for job in jobs_with_extraction:
        if not job.posted_date:
            continue
        month_key = job.posted_date.strftime("%Y-%m")
        monthly_activity[month_key] += 1
    
    activity_summary["monthly"] = [
        {"month": month, "count": count}
        for month, count in sorted(monthly_activity.items())
    ]
    
    return {
        "granularity": granularity,
        "time_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "job_count_trend": job_count_trend,
        "role_family_trends": role_family_trends_dict,
        "keyword_trends": keyword_trends,
        "activity_summary": activity_summary,
        "total_jobs": len(jobs_with_extraction)
    }


@router.get("/location", response_model=Dict[str, Any])
def get_location_analysis(
    days: int = Query(30, description="时间窗口（天数）"),
    role_family: Optional[str] = Query(None, description="按角色族过滤"),
    seniority: Optional[str] = Query(None, description="按资历级别过滤"),
    location: Optional[str] = Query(None, description="按地点过滤"),
    session: Session = Depends(get_session)
):
    """
    获取地理位置分析
    
    返回：
    - location_distribution: 按城市/地区统计职位分布
    - location_by_role_family: 不同城市的角色族分布
    - location_trends: 城市职位需求趋势
    """
    # 计算时间窗口
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 构建基础查询
    job_query = select(Job).where(Job.captured_at >= start_date, Job.captured_at <= end_date)
    
    # 应用过滤条件
    if role_family:
        job_query = job_query.where(Job.role_family == role_family)
    if seniority:
        seniority_mapping = {
            'graduate': Seniority.JUNIOR,
            'junior': Seniority.JUNIOR,
            'intermediate': Seniority.MID,
            'mid': Seniority.MID,
            'senior': Seniority.SENIOR
        }
        mapped_seniority = seniority_mapping.get(seniority.lower())
        if mapped_seniority:
            job_query = job_query.where(Job.seniority == mapped_seniority)
        else:
            try:
                job_query = job_query.where(Job.seniority == Seniority(seniority.lower()))
            except ValueError:
                pass
    if location:
        job_query = job_query.where(Job.location.contains(location))
    
    jobs = session.exec(job_query).all()
    job_ids = [job.id for job in jobs]
    
    # 只获取有Extraction的Job
    if job_ids:
        extraction_query = select(Extraction).where(Extraction.job_id.in_(job_ids))
        extractions = session.exec(extraction_query).all()
        extraction_job_ids = {ext.job_id for ext in extractions}
        jobs_with_extraction = [job for job in jobs if job.id in extraction_job_ids]
    else:
        jobs_with_extraction = []
    
    # 1. 按城市/地区统计职位分布
    location_counter = Counter()
    for job in jobs_with_extraction:
        if job.location:
            # 提取主要城市名称（处理 "Auckland, New Zealand" -> "Auckland"）
            location_parts = job.location.split(',')
            city = location_parts[0].strip() if location_parts else job.location.strip()
            location_counter[city] += 1
    
    location_distribution = [
        {"location": loc, "count": count}
        for loc, count in location_counter.most_common(20)
    ]
    
    # 2. 不同城市的角色族分布
    location_by_role_family: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for job in jobs_with_extraction:
        if job.location and job.role_family:
            location_parts = job.location.split(',')
            city = location_parts[0].strip() if location_parts else job.location.strip()
            location_by_role_family[city][job.role_family] += 1
    
    # 转换为前端需要的格式
    location_by_role_family_dict = {}
    for city, role_families in location_by_role_family.items():
        location_by_role_family_dict[city] = dict(role_families)
    
    # 3. 城市职位需求趋势（按周统计）
    location_trends: Dict[str, List[Dict[str, Any]]] = defaultdict(lambda: defaultdict(int))
    for job in jobs_with_extraction:
        if job.location and job.posted_date:
            location_parts = job.location.split(',')
            city = location_parts[0].strip() if location_parts else job.location.strip()
            # 获取该周的周一日期
            days_since_monday = job.posted_date.weekday()
            monday = job.posted_date - timedelta(days=days_since_monday)
            week_key = monday.strftime("%Y-%m-%d")
            location_trends[city][week_key] += 1
    
    # 转换为列表格式
    location_trends_dict = {}
    for city, weeks in location_trends.items():
        location_trends_dict[city] = [
            {"week": week, "count": count}
            for week, count in sorted(weeks.items())
        ]
    
    return {
        "location_distribution": location_distribution,
        "location_by_role_family": location_by_role_family_dict,
        "location_trends": location_trends_dict,
        "total_jobs": len(jobs_with_extraction)
    }


@router.get("/company", response_model=Dict[str, Any])
def get_company_analysis(
    days: int = Query(30, description="时间窗口（天数）"),
    role_family: Optional[str] = Query(None, description="按角色族过滤"),
    seniority: Optional[str] = Query(None, description="按资历级别过滤"),
    location: Optional[str] = Query(None, description="按地点过滤"),
    session: Session = Depends(get_session)
):
    """
    获取公司分析
    
    返回：
    - top_companies: Top 20 招聘公司（按职位数）
    - company_trends: 公司招聘趋势（时间序列）
    - company_role_family_preference: 公司角色族偏好
    """
    # 计算时间窗口
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 构建基础查询
    job_query = select(Job).where(Job.captured_at >= start_date, Job.captured_at <= end_date)
    
    # 应用过滤条件
    if role_family:
        job_query = job_query.where(Job.role_family == role_family)
    if seniority:
        seniority_mapping = {
            'graduate': Seniority.JUNIOR,
            'junior': Seniority.JUNIOR,
            'intermediate': Seniority.MID,
            'mid': Seniority.MID,
            'senior': Seniority.SENIOR
        }
        mapped_seniority = seniority_mapping.get(seniority.lower())
        if mapped_seniority:
            job_query = job_query.where(Job.seniority == mapped_seniority)
        else:
            try:
                job_query = job_query.where(Job.seniority == Seniority(seniority.lower()))
            except ValueError:
                pass
    if location:
        job_query = job_query.where(Job.location.contains(location))
    
    jobs = session.exec(job_query).all()
    job_ids = [job.id for job in jobs]
    
    # 只获取有Extraction的Job
    if job_ids:
        extraction_query = select(Extraction).where(Extraction.job_id.in_(job_ids))
        extractions = session.exec(extraction_query).all()
        extraction_job_ids = {ext.job_id for ext in extractions}
        jobs_with_extraction = [job for job in jobs if job.id in extraction_job_ids]
    else:
        jobs_with_extraction = []
    
    # 1. Top 20 招聘公司
    company_counter = Counter()
    for job in jobs_with_extraction:
        if job.company:
            company_counter[job.company] += 1
    
    top_companies = [
        {"company": company, "count": count}
        for company, count in company_counter.most_common(20)
    ]
    
    # 2. 公司招聘趋势（按周统计）
    company_trends: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for job in jobs_with_extraction:
        if job.company and job.posted_date:
            # 获取该周的周一日期
            days_since_monday = job.posted_date.weekday()
            monday = job.posted_date - timedelta(days=days_since_monday)
            week_key = monday.strftime("%Y-%m-%d")
            company_trends[job.company][week_key] += 1
    
    # 转换为列表格式（只保留Top 10公司）
    top_10_companies = [item["company"] for item in top_companies[:10]]
    company_trends_dict = {}
    for company in top_10_companies:
        if company in company_trends:
            company_trends_dict[company] = [
                {"week": week, "count": count}
                for week, count in sorted(company_trends[company].items())
            ]
    
    # 3. 公司角色族偏好
    company_role_family_preference: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for job in jobs_with_extraction:
        if job.company and job.role_family:
            company_role_family_preference[job.company][job.role_family] += 1
    
    # 转换为前端需要的格式（只保留Top 10公司）
    company_role_family_preference_dict = {}
    for company in top_10_companies:
        if company in company_role_family_preference:
            company_role_family_preference_dict[company] = dict(company_role_family_preference[company])
    
    return {
        "top_companies": top_companies,
        "company_trends": company_trends_dict,
        "company_role_family_preference": company_role_family_preference_dict,
        "total_jobs": len(jobs_with_extraction)
    }


@router.get("/experience", response_model=Dict[str, Any])
def get_experience_analysis(
    days: int = Query(30, description="时间窗口（天数）"),
    role_family: Optional[str] = Query(None, description="按角色族过滤"),
    seniority: Optional[str] = Query(None, description="按资历级别过滤"),
    location: Optional[str] = Query(None, description="按地点过滤"),
    session: Session = Depends(get_session)
):
    """
    获取经验要求分析
    
    返回：
    - experience_distribution: 经验年限分布
    - experience_by_role_family: 不同角色族的经验要求对比
    - experience_trends: 经验要求随时间的变化趋势
    """
    # 计算时间窗口
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 构建基础查询
    job_query = select(Job).where(Job.captured_at >= start_date, Job.captured_at <= end_date)
    
    # 应用过滤条件
    if role_family:
        job_query = job_query.where(Job.role_family == role_family)
    if seniority:
        seniority_mapping = {
            'graduate': Seniority.JUNIOR,
            'junior': Seniority.JUNIOR,
            'intermediate': Seniority.MID,
            'mid': Seniority.MID,
            'senior': Seniority.SENIOR
        }
        mapped_seniority = seniority_mapping.get(seniority.lower())
        if mapped_seniority:
            job_query = job_query.where(Job.seniority == mapped_seniority)
        else:
            try:
                job_query = job_query.where(Job.seniority == Seniority(seniority.lower()))
            except ValueError:
                pass
    if location:
        job_query = job_query.where(Job.location.contains(location))
    
    jobs = session.exec(job_query).all()
    job_ids = [job.id for job in jobs]
    
    # 只获取有Extraction的Job
    if job_ids:
        extraction_query = select(Extraction).where(Extraction.job_id.in_(job_ids))
        extractions = session.exec(extraction_query).all()
        extraction_job_ids = {ext.job_id for ext in extractions}
        jobs_with_extraction = [job for job in jobs if job.id in extraction_job_ids]
        # 创建job_id到extraction的映射
        extraction_map = {ext.job_id: ext for ext in extractions}
    else:
        jobs_with_extraction = []
        extraction_map = {}
    
    # 1. 经验年限分布
    experience_counter = Counter()
    for job in jobs_with_extraction:
        extraction = extraction_map.get(job.id)
        if extraction and extraction.years_required is not None:
            # 将经验年限分组（0-2, 3-5, 6-8, 9-11, 12+）
            years = extraction.years_required
            if years <= 2:
                bucket = "0-2 years"
            elif years <= 5:
                bucket = "3-5 years"
            elif years <= 8:
                bucket = "6-8 years"
            elif years <= 11:
                bucket = "9-11 years"
            else:
                bucket = "12+ years"
            experience_counter[bucket] += 1
    
    experience_distribution = [
        {"range": range_name, "count": count}
        for range_name, count in sorted(experience_counter.items(), key=lambda x: {
            "0-2 years": 0, "3-5 years": 1, "6-8 years": 2, "9-11 years": 3, "12+ years": 4
        }.get(x[0], 5))
    ]
    
    # 2. 不同角色族的经验要求对比
    experience_by_role_family: Dict[str, Counter] = defaultdict(Counter)
    for job in jobs_with_extraction:
        extraction = extraction_map.get(job.id)
        if job.role_family and extraction and extraction.years_required is not None:
            years = extraction.years_required
            if years <= 2:
                bucket = "0-2 years"
            elif years <= 5:
                bucket = "3-5 years"
            elif years <= 8:
                bucket = "6-8 years"
            elif years <= 11:
                bucket = "9-11 years"
            else:
                bucket = "12+ years"
            experience_by_role_family[job.role_family][bucket] += 1
    
    experience_by_role_family_dict = {}
    for role_fam, counter in experience_by_role_family.items():
        experience_by_role_family_dict[role_fam] = dict(counter)
    
    # 3. 经验要求随时间的变化趋势（按周统计，只统计平均经验要求）
    experience_trends: Dict[str, List[int]] = defaultdict(list)
    for job in jobs_with_extraction:
        extraction = extraction_map.get(job.id)
        if extraction and extraction.years_required is not None and job.posted_date:
            days_since_monday = job.posted_date.weekday()
            monday = job.posted_date - timedelta(days=days_since_monday)
            week_key = monday.strftime("%Y-%m-%d")
            experience_trends[week_key].append(extraction.years_required)
    
    # 计算每周的平均经验要求
    experience_trends_list = []
    for week, years_list in sorted(experience_trends.items()):
        avg_years = sum(years_list) / len(years_list) if years_list else 0
        experience_trends_list.append({
            "week": week,
            "average_years": round(avg_years, 1),
            "count": len(years_list)
        })
    
    return {
        "experience_distribution": experience_distribution,
        "experience_by_role_family": experience_by_role_family_dict,
        "experience_trends": experience_trends_list,
        "total_jobs": len(jobs_with_extraction),
        "jobs_with_experience": sum(1 for job in jobs_with_extraction if extraction_map.get(job.id) and extraction_map[job.id].years_required is not None)
    }


@router.get("/education", response_model=Dict[str, Any])
def get_education_analysis(
    days: int = Query(30, description="时间窗口（天数）"),
    role_family: Optional[str] = Query(None, description="按角色族过滤"),
    seniority: Optional[str] = Query(None, description="按资历级别过滤"),
    location: Optional[str] = Query(None, description="按地点过滤"),
    session: Session = Depends(get_session)
):
    """
    获取学历要求分析
    
    返回：
    - degree_distribution: 学历要求分布
    - degree_by_role_family: 不同角色族的学历要求对比
    - certifications_distribution: 证书要求统计
    """
    # 计算时间窗口
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 构建基础查询
    job_query = select(Job).where(Job.captured_at >= start_date, Job.captured_at <= end_date)
    
    # 应用过滤条件
    if role_family:
        job_query = job_query.where(Job.role_family == role_family)
    if seniority:
        seniority_mapping = {
            'graduate': Seniority.JUNIOR,
            'junior': Seniority.JUNIOR,
            'intermediate': Seniority.MID,
            'mid': Seniority.MID,
            'senior': Seniority.SENIOR
        }
        mapped_seniority = seniority_mapping.get(seniority.lower())
        if mapped_seniority:
            job_query = job_query.where(Job.seniority == mapped_seniority)
        else:
            try:
                job_query = job_query.where(Job.seniority == Seniority(seniority.lower()))
            except ValueError:
                pass
    if location:
        job_query = job_query.where(Job.location.contains(location))
    
    jobs = session.exec(job_query).all()
    job_ids = [job.id for job in jobs]
    
    # 只获取有Extraction的Job
    if job_ids:
        extraction_query = select(Extraction).where(Extraction.job_id.in_(job_ids))
        extractions = session.exec(extraction_query).all()
        extraction_job_ids = {ext.job_id for ext in extractions}
        jobs_with_extraction = [job for job in jobs if job.id in extraction_job_ids]
        extraction_map = {ext.job_id: ext for ext in extractions}
    else:
        jobs_with_extraction = []
        extraction_map = {}
    
    # 1. 学历要求分布
    degree_counter = Counter()
    for job in jobs_with_extraction:
        extraction = extraction_map.get(job.id)
        if extraction and extraction.degree_required:
            # 规范化学历名称
            degree_lower = extraction.degree_required.lower()
            if 'bachelor' in degree_lower or 'bs' in degree_lower or 'ba' in degree_lower:
                degree = "Bachelor's"
            elif 'master' in degree_lower or 'ms' in degree_lower or 'mba' in degree_lower:
                degree = "Master's"
            elif 'phd' in degree_lower or 'ph.d' in degree_lower or 'doctorate' in degree_lower:
                degree = "PhD"
            elif 'associate' in degree_lower:
                degree = "Associate"
            else:
                degree = extraction.degree_required
            degree_counter[degree] += 1
    
    degree_distribution = [
        {"degree": degree, "count": count}
        for degree, count in degree_counter.most_common()
    ]
    
    # 2. 不同角色族的学历要求对比
    degree_by_role_family: Dict[str, Counter] = defaultdict(Counter)
    for job in jobs_with_extraction:
        extraction = extraction_map.get(job.id)
        if job.role_family and extraction and extraction.degree_required:
            degree_lower = extraction.degree_required.lower()
            if 'bachelor' in degree_lower or 'bs' in degree_lower or 'ba' in degree_lower:
                degree = "Bachelor's"
            elif 'master' in degree_lower or 'ms' in degree_lower or 'mba' in degree_lower:
                degree = "Master's"
            elif 'phd' in degree_lower or 'ph.d' in degree_lower or 'doctorate' in degree_lower:
                degree = "PhD"
            elif 'associate' in degree_lower:
                degree = "Associate"
            else:
                degree = extraction.degree_required
            degree_by_role_family[job.role_family][degree] += 1
    
    degree_by_role_family_dict = {}
    for role_fam, counter in degree_by_role_family.items():
        degree_by_role_family_dict[role_fam] = dict(counter)
    
    # 3. 证书要求统计
    certification_counter = Counter()
    for job in jobs_with_extraction:
        extraction = extraction_map.get(job.id)
        if extraction and extraction.certifications_json:
            certs = extraction.certifications_json.get("certifications", [])
            for cert in certs:
                if isinstance(cert, str):
                    certification_counter[cert] += 1
    
    certifications_distribution = [
        {"certification": cert, "count": count}
        for cert, count in certification_counter.most_common(20)
    ]
    
    return {
        "degree_distribution": degree_distribution,
        "degree_by_role_family": degree_by_role_family_dict,
        "certifications_distribution": certifications_distribution,
        "total_jobs": len(jobs_with_extraction),
        "jobs_with_degree": sum(1 for job in jobs_with_extraction if extraction_map.get(job.id) and extraction_map[job.id].degree_required),
        "jobs_with_certifications": sum(1 for job in jobs_with_extraction if extraction_map.get(job.id) and extraction_map[job.id].certifications_json.get("certifications"))
    }


@router.get("/industry", response_model=Dict[str, Any])
def get_industry_analysis(
    days: int = Query(30, description="时间窗口（天数）"),
    role_family: Optional[str] = Query(None, description="按角色族过滤"),
    seniority: Optional[str] = Query(None, description="按资历级别过滤"),
    location: Optional[str] = Query(None, description="按地点过滤"),
    session: Session = Depends(get_session)
):
    """
    获取行业分析
    
    返回：
    - industry_distribution: 行业分布
    - industry_by_role_family: 不同行业的角色族分布
    - industry_trends: 行业招聘趋势
    """
    # 计算时间窗口
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 构建基础查询
    job_query = select(Job).where(Job.captured_at >= start_date, Job.captured_at <= end_date)
    
    # 应用过滤条件
    if role_family:
        job_query = job_query.where(Job.role_family == role_family)
    if seniority:
        seniority_mapping = {
            'graduate': Seniority.JUNIOR,
            'junior': Seniority.JUNIOR,
            'intermediate': Seniority.MID,
            'mid': Seniority.MID,
            'senior': Seniority.SENIOR
        }
        mapped_seniority = seniority_mapping.get(seniority.lower())
        if mapped_seniority:
            job_query = job_query.where(Job.seniority == mapped_seniority)
        else:
            try:
                job_query = job_query.where(Job.seniority == Seniority(seniority.lower()))
            except ValueError:
                pass
    if location:
        job_query = job_query.where(Job.location.contains(location))
    
    jobs = session.exec(job_query).all()
    job_ids = [job.id for job in jobs]
    
    # 只获取有Extraction的Job
    if job_ids:
        extraction_query = select(Extraction).where(Extraction.job_id.in_(job_ids))
        extractions = session.exec(extraction_query).all()
        extraction_job_ids = {ext.job_id for ext in extractions}
        jobs_with_extraction = [job for job in jobs if job.id in extraction_job_ids]
    else:
        jobs_with_extraction = []
    
    # 1. 行业分布
    industry_counter = Counter()
    for job in jobs_with_extraction:
        if job.industry:
            industry_counter[job.industry] += 1
    
    industry_distribution = [
        {"industry": industry, "count": count}
        for industry, count in industry_counter.most_common(20)
    ]
    
    # 2. 不同行业的角色族分布
    industry_by_role_family: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for job in jobs_with_extraction:
        if job.industry and job.role_family:
            industry_by_role_family[job.industry][job.role_family] += 1
    
    industry_by_role_family_dict = {}
    for industry, role_families in industry_by_role_family.items():
        industry_by_role_family_dict[industry] = dict(role_families)
    
    # 3. 行业招聘趋势（按周统计）
    industry_trends: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for job in jobs_with_extraction:
        if job.industry and job.posted_date:
            days_since_monday = job.posted_date.weekday()
            monday = job.posted_date - timedelta(days=days_since_monday)
            week_key = monday.strftime("%Y-%m-%d")
            industry_trends[job.industry][week_key] += 1
    
    # 转换为列表格式（只保留Top 10行业）
    top_10_industries = [item["industry"] for item in industry_distribution[:10]]
    industry_trends_dict = {}
    for industry in top_10_industries:
        if industry in industry_trends:
            industry_trends_dict[industry] = [
                {"week": week, "count": count}
                for week, count in sorted(industry_trends[industry].items())
            ]
    
    return {
        "industry_distribution": industry_distribution,
        "industry_by_role_family": industry_by_role_family_dict,
        "industry_trends": industry_trends_dict,
        "total_jobs": len(jobs_with_extraction)
    }


@router.get("/source", response_model=Dict[str, Any])
def get_source_analysis(
    days: int = Query(30, description="时间窗口（天数）"),
    role_family: Optional[str] = Query(None, description="按角色族过滤"),
    seniority: Optional[str] = Query(None, description="按资历级别过滤"),
    location: Optional[str] = Query(None, description="按地点过滤"),
    session: Session = Depends(get_session)
):
    """
    获取数据来源分析
    
    返回：
    - source_distribution: 数据来源分布
    - source_quality: 不同来源的职位质量对比（提取成功率）
    """
    # 计算时间窗口
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 构建基础查询
    job_query = select(Job).where(Job.captured_at >= start_date, Job.captured_at <= end_date)
    
    # 应用过滤条件
    if role_family:
        job_query = job_query.where(Job.role_family == role_family)
    if seniority:
        seniority_mapping = {
            'graduate': Seniority.JUNIOR,
            'junior': Seniority.JUNIOR,
            'intermediate': Seniority.MID,
            'mid': Seniority.MID,
            'senior': Seniority.SENIOR
        }
        mapped_seniority = seniority_mapping.get(seniority.lower())
        if mapped_seniority:
            job_query = job_query.where(Job.seniority == mapped_seniority)
        else:
            try:
                job_query = job_query.where(Job.seniority == Seniority(seniority.lower()))
            except ValueError:
                pass
    if location:
        job_query = job_query.where(Job.location.contains(location))
    
    jobs = session.exec(job_query).all()
    job_ids = [job.id for job in jobs]
    
    # 获取所有Extraction
    if job_ids:
        extraction_query = select(Extraction).where(Extraction.job_id.in_(job_ids))
        extractions = session.exec(extraction_query).all()
        extraction_job_ids = {ext.job_id for ext in extractions}
    else:
        extractions = []
        extraction_job_ids = set()
    
    # 1. 数据来源分布
    source_counter = Counter()
    for job in jobs:
        source_counter[job.source] += 1
    
    source_distribution = [
        {"source": source, "count": count}
        for source, count in source_counter.most_common()
    ]
    
    # 2. 不同来源的提取成功率
    source_quality = {}
    for source, total_count in source_counter.items():
        source_jobs = [job for job in jobs if job.source == source]
        source_job_ids = {job.id for job in source_jobs}
        extracted_count = len(source_job_ids & extraction_job_ids)
        success_rate = (extracted_count / total_count * 100) if total_count > 0 else 0
        
        source_quality[source] = {
            "total_jobs": total_count,
            "extracted_jobs": extracted_count,
            "success_rate": round(success_rate, 2)
        }
    
    return {
        "source_distribution": source_distribution,
        "source_quality": source_quality,
        "total_jobs": len(jobs)
    }


@router.get("/skill-combination", response_model=Dict[str, Any])
def get_skill_combination_analysis(
    days: int = Query(30, description="时间窗口（天数）"),
    role_family: Optional[str] = Query(None, description="按角色族过滤"),
    seniority: Optional[str] = Query(None, description="按资历级别过滤"),
    location: Optional[str] = Query(None, description="按地点过滤"),
    session: Session = Depends(get_session)
):
    """
    获取技能组合分析
    
    返回：
    - skill_cooccurrence: 技能共现分析（Top 20 技能组合）
    - must_have_vs_nice_to_have: Must-have vs Nice-to-have 对比
    - skill_intensity_by_role_family: 按角色族统计技能出现频率（Top 10技能）
    """
    # 计算时间窗口
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 构建基础查询
    job_query = select(Job).where(Job.captured_at >= start_date, Job.captured_at <= end_date)
    
    # 应用过滤条件
    if role_family:
        job_query = job_query.where(Job.role_family == role_family)
    if seniority:
        seniority_mapping = {
            'graduate': Seniority.JUNIOR,
            'junior': Seniority.JUNIOR,
            'intermediate': Seniority.MID,
            'mid': Seniority.MID,
            'senior': Seniority.SENIOR
        }
        mapped_seniority = seniority_mapping.get(seniority.lower())
        if mapped_seniority:
            job_query = job_query.where(Job.seniority == mapped_seniority)
        else:
            try:
                job_query = job_query.where(Job.seniority == Seniority(seniority.lower()))
            except ValueError:
                pass
    if location:
        job_query = job_query.where(Job.location.contains(location))
    
    jobs = session.exec(job_query).all()
    job_ids = [job.id for job in jobs]
    
    # 只获取有Extraction的Job
    if job_ids:
        extraction_query = select(Extraction).where(Extraction.job_id.in_(job_ids))
        extractions = session.exec(extraction_query).all()
        extraction_job_ids = {ext.job_id for ext in extractions}
        jobs_with_extraction = [job for job in jobs if job.id in extraction_job_ids]
        extraction_map = {ext.job_id: ext for ext in extractions}
    else:
        jobs_with_extraction = []
        extraction_map = {}
    
    # 1. 技能共现分析
    skill_cooccurrence_counter = Counter()
    skill_sets = []  # 存储每个职位的技能集合
    
    for job in jobs_with_extraction:
        extraction = extraction_map.get(job.id)
        if not extraction:
            continue
        
        # 获取所有技能（从keywords_json）
        keywords_data = extraction.keywords_json.get("keywords", [])
        skills_in_job = set()
        
        for kw in keywords_data:
            if isinstance(kw, dict):
                term = kw.get("term", "")
            elif isinstance(kw, str):
                term = kw
            else:
                continue
            
            if term and not should_filter_keyword(term):
                normalized_term = normalize_keyword(term)
                term_upper = normalized_term.upper().strip()
                if term_upper == 'CI/CD' or term_upper == 'CI CD':
                    normalized_term = 'CI/CD'
                skills_in_job.add(normalized_term)
        
        if len(skills_in_job) > 1:
            skill_sets.append(skills_in_job)
            # 计算所有技能对
            skills_list = sorted(list(skills_in_job))
            for i in range(len(skills_list)):
                for j in range(i + 1, len(skills_list)):
                    pair = tuple(sorted([skills_list[i], skills_list[j]]))
                    skill_cooccurrence_counter[pair] += 1
    
    # 处理CI/CD合并
    if 'CI' in skill_cooccurrence_counter or 'CD' in skill_cooccurrence_counter:
        # 需要重新计算包含CI/CD的组合
        pass  # 这里简化处理，实际应该合并CI和CD
    
    skill_cooccurrence = [
        {"skill1": pair[0], "skill2": pair[1], "count": count}
        for pair, count in skill_cooccurrence_counter.most_common(20)
    ]
    
    # 2. Must-have vs Nice-to-have 对比
    must_have_counter = Counter()
    nice_to_have_counter = Counter()
    
    for job in jobs_with_extraction:
        extraction = extraction_map.get(job.id)
        if not extraction:
            continue
        
        # Must-have 技能
        must_have_skills = extraction.must_have_json.get("keywords", [])
        for skill in must_have_skills:
            if isinstance(skill, str) and skill and not should_filter_keyword(skill):
                normalized = normalize_keyword(skill)
                must_have_counter[normalized] += 1
        
        # Nice-to-have 技能
        nice_to_have_skills = extraction.nice_to_have_json.get("keywords", [])
        for skill in nice_to_have_skills:
            if isinstance(skill, str) and skill and not should_filter_keyword(skill):
                normalized = normalize_keyword(skill)
                nice_to_have_counter[normalized] += 1
    
    # 合并统计
    all_skills = set(must_have_counter.keys()) | set(nice_to_have_counter.keys())
    must_have_vs_nice_to_have = []
    for skill in sorted(all_skills, key=lambda s: must_have_counter.get(s, 0) + nice_to_have_counter.get(s, 0), reverse=True)[:30]:
        must_have_vs_nice_to_have.append({
            "skill": skill,
            "must_have_count": must_have_counter.get(skill, 0),
            "nice_to_have_count": nice_to_have_counter.get(skill, 0),
            "total_count": must_have_counter.get(skill, 0) + nice_to_have_counter.get(skill, 0)
        })
    
    # 3. 按角色族统计技能出现频率
    skill_intensity_by_role_family: Dict[str, Counter] = defaultdict(Counter)
    
    for job in jobs_with_extraction:
        extraction = extraction_map.get(job.id)
        if not job.role_family or not extraction:
            continue
        
        keywords_data = extraction.keywords_json.get("keywords", [])
        for kw in keywords_data:
            if isinstance(kw, dict):
                term = kw.get("term", "")
            elif isinstance(kw, str):
                term = kw
            else:
                continue
            
            if term and not should_filter_keyword(term):
                normalized_term = normalize_keyword(term)
                term_upper = normalized_term.upper().strip()
                if term_upper == 'CI/CD' or term_upper == 'CI CD':
                    normalized_term = 'CI/CD'
                skill_intensity_by_role_family[job.role_family][normalized_term] += 1
    
    # 转换为前端需要的格式（每个角色族Top 10技能）
    skill_intensity_dict = {}
    for role_fam, counter in skill_intensity_by_role_family.items():
        top_skills = counter.most_common(10)
        skill_intensity_dict[role_fam] = [
            {"skill": skill, "count": count}
            for skill, count in top_skills
        ]
    
    return {
        "skill_cooccurrence": skill_cooccurrence,
        "must_have_vs_nice_to_have": must_have_vs_nice_to_have,
        "skill_intensity_by_role_family": skill_intensity_dict,
        "total_jobs": len(jobs_with_extraction)
    }