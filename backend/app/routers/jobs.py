"""职位相关API端点"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, or_
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.database import get_session
from app.models import Job, Extraction, JobStatus, Seniority
from app.schemas import JobCreate, JobUpdate, JobResponse, ExtractionResponse
from app.extractors.keyword_extractor import extract_and_save

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post(
    "",
    response_model=JobResponse,
    status_code=201,
    summary="创建新职位",
    description="""
    创建新职位并自动运行关键词提取。
    
    支持两种模式：
    - **Direct模式**: 直接提供jd_text字段
    - **URL Capture模式**: 提供url和selected_text字段（可选jd_text）
    
    规则：
    - 如果jd_text缺失但selected_text存在，使用selected_text作为jd_text
    - 至少需要提供jd_text或selected_text之一
    - source字段自动设置为"manual"（direct模式）或"capture"（url capture模式）
    """,
    response_description="创建的职位信息（包含提取结果）"
)
async def create_job(job_data: JobCreate, session: Session = Depends(get_session)):
    """创建新职位并自动运行提取"""
    # model_validator已经处理了jd_text和source的转换
    # 排除selected_text字段（它不应该保存到数据库）
    job_dict = job_data.model_dump(exclude={"selected_text"})
    
    # 如果用户没有提供role_family或seniority，使用AI推断（优先）
    if not job_dict.get("role_family") or not job_dict.get("seniority"):
        from app.extractors.ai_role_inferrer import infer_role_and_seniority_with_ai
        inferred_role_family, inferred_seniority = await infer_role_and_seniority_with_ai(
            job_data.title,
            job_data.jd_text or "",
            use_ai=True
        )
        # 只有在用户没有提供时才使用推断结果
        if not job_dict.get("role_family") and inferred_role_family:
            job_dict["role_family"] = inferred_role_family
        if not job_dict.get("seniority") and inferred_seniority:
            job_dict["seniority"] = inferred_seniority
    
    job = Job(**job_dict)
    session.add(job)
    session.commit()
    session.refresh(job)
    
    # 自动运行提取（支持AI增强）
    try:
        await extract_and_save(
            job.id, 
            job.jd_text, 
            session,
            job_title=job.title,
            company=job.company,
            use_ai=True
        )
        session.refresh(job)
        
        # 如果posted_date未设置，尝试从AI提取结果中获取
        if not job.posted_date:
            from app.extractors.ai_enhanced_extractor import extract_with_ai
            ai_result = await extract_with_ai(
                job.jd_text,
                job_title=job.title,
                company=job.company
            )
            if ai_result.get("success") and ai_result.get("posted_date"):
                try:
                    from datetime import datetime
                    posted_date_str = ai_result.get("posted_date")
                    if isinstance(posted_date_str, str):
                        # 解析日期字符串
                        posted_date = datetime.fromisoformat(posted_date_str.replace('Z', '+00:00'))
                        job.posted_date = posted_date
                        session.add(job)
                        session.commit()
                        session.refresh(job)
                        print(f"✓ 从AI提取到posted_date: {posted_date.strftime('%Y-%m-%d')}")
                except Exception as e:
                    print(f"解析AI提取的posted_date失败: {e}")
    except Exception as e:
        # 即使提取失败，也返回创建的职位
        print(f"提取失败: {e}")
        pass
    
    # 获取提取结果
    extraction = session.exec(select(Extraction).where(Extraction.job_id == job.id)).first()
    
    response_data = {
        "id": job.id,
        "source": job.source,
        "url": job.url,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "posted_date": job.posted_date,
        "captured_at": job.captured_at,
        "jd_text": job.jd_text,
        "status": job.status,
        "role_family": job.role_family,
        "seniority": job.seniority,
        "extraction": ExtractionResponse(
            id=extraction.id,
            job_id=extraction.job_id,
            keywords_json=extraction.keywords_json,
            must_have_json=extraction.must_have_json,
            nice_to_have_json=extraction.nice_to_have_json,
            years_required=extraction.years_required,
            degree_required=extraction.degree_required,
            certifications_json=extraction.certifications_json,
            summary=extraction.summary,
            extraction_method=extraction.extraction_method,
            extracted_at=extraction.extracted_at
        ) if extraction else None
    }
    
    return JobResponse(**response_data)


@router.get("", response_model=List[JobResponse])
def list_jobs(
    status: Optional[JobStatus] = Query(None, description="按状态过滤"),
    role_family: Optional[List[str]] = Query(None, description="按角色族过滤（支持多选）"),
    seniority: Optional[List[str]] = Query(None, description="按资历级别过滤（支持多选，支持graduate/junior/intermediate/mid/senior/manager/lead/architect/unknown）"),
    keyword: Optional[str] = Query(None, description="关键词搜索（在jd_text中）"),
    location: Optional[str] = Query(None, description="按地点过滤（支持部分匹配，如'New Zealand'或'NZ'）"),
    session: Session = Depends(get_session)
):
    """列出所有职位（支持过滤）"""
    statement = select(Job)
    
    # 应用过滤条件
    conditions = []
    if status:
        conditions.append(Job.status == status)
    if role_family:
        # 支持多选：如果传入列表，使用 in_ 操作符
        if isinstance(role_family, list) and len(role_family) > 0:
            conditions.append(Job.role_family.in_(role_family))
        elif isinstance(role_family, str):
            conditions.append(Job.role_family == role_family)
    if seniority:
        # 映射前端的显示名称到实际的枚举值
        seniority_mapping = {
            'graduate': Seniority.GRADUATE,
            'junior': Seniority.JUNIOR,
            'intermediate': Seniority.MID,
            'mid': Seniority.MID,
            'senior': Seniority.SENIOR,
            'manager': Seniority.MANAGER,
            'lead': Seniority.LEAD,
            'architect': Seniority.ARCHITECT,
            'unknown': Seniority.UNKNOWN
        }
        # 支持多选：如果传入列表，映射所有值并使用 in_ 操作符
        if isinstance(seniority, list) and len(seniority) > 0:
            mapped_seniorities = []
            for s in seniority:
                mapped = seniority_mapping.get(s.lower())
                if mapped:
                    mapped_seniorities.append(mapped)
                else:
                    # 尝试直接转换为枚举
                    try:
                        mapped_seniorities.append(Seniority(s.lower()))
                    except ValueError:
                        pass  # 无效的seniority值，忽略
            if mapped_seniorities:
                conditions.append(Job.seniority.in_(mapped_seniorities))
        elif isinstance(seniority, str):
            # 单个值的情况（向后兼容）
            mapped_seniority = seniority_mapping.get(seniority.lower())
            if mapped_seniority:
                conditions.append(Job.seniority == mapped_seniority)
            else:
                # 尝试直接转换为枚举
                try:
                    conditions.append(Job.seniority == Seniority(seniority.lower()))
                except ValueError:
                    pass  # 无效的seniority值，忽略
    if keyword:
        conditions.append(Job.jd_text.contains(keyword))
    if location:
        # 支持部分匹配
        conditions.append(Job.location.contains(location))
    
    if conditions:
        for condition in conditions:
            statement = statement.where(condition)
    
    # 先按captured_at降序获取所有数据（用于去重）
    statement = statement.order_by(Job.captured_at.desc())
    jobs = session.exec(statement).all()
    
    # 去重：优先使用URL去重（更准确），如果没有URL则使用title+company+location
    seen_jobs = {}
    unique_jobs = []
    for job in jobs:
        # 优先使用URL作为唯一标识（如果存在）
        if job.url:
            key = job.url.lower().strip()
        else:
            # 如果没有URL，使用title + company + location组合
            key = f"{job.title.lower().strip()}|{job.company.lower().strip() if job.company else ''}|{job.location.lower().strip() if job.location else ''}"
        
        if key not in seen_jobs:
            seen_jobs[key] = job
            unique_jobs.append(job)
        else:
            # 如果已存在，保留captured_at更新的
            existing_job = seen_jobs[key]
            if job.captured_at and existing_job.captured_at:
                if job.captured_at > existing_job.captured_at:
                    # 替换为更新的
                    index = unique_jobs.index(existing_job)
                    unique_jobs[index] = job
                    seen_jobs[key] = job
    
    # 去重后按posted_date降序排序（如果有），否则使用captured_at，确保最近的在最前面
    unique_jobs.sort(key=lambda j: j.posted_date if j.posted_date else (j.captured_at if j.captured_at else datetime.min), reverse=True)
    
    # 构建响应
    result = []
    for job in unique_jobs:
        extraction = session.exec(select(Extraction).where(Extraction.job_id == job.id)).first()
        response_data = {
            "id": job.id,
            "source": job.source,
            "url": job.url,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "posted_date": job.posted_date,
            "captured_at": job.captured_at,
            "jd_text": job.jd_text,
            "status": job.status,
            "role_family": job.role_family,
            "seniority": job.seniority,
            "industry": job.industry,
            "extraction": ExtractionResponse(
                id=extraction.id,
                job_id=extraction.job_id,
                keywords_json=extraction.keywords_json,
                must_have_json=extraction.must_have_json,
                nice_to_have_json=extraction.nice_to_have_json,
                years_required=extraction.years_required,
                degree_required=extraction.degree_required,
                certifications_json=extraction.certifications_json,
                extracted_at=extraction.extracted_at
            ) if extraction else None
        }
        result.append(JobResponse(**response_data))
    
    return result


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID, session: Session = Depends(get_session)):
    """获取特定职位"""
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    extraction = session.exec(select(Extraction).where(Extraction.job_id == job_id)).first()
    
    response_data = {
        "id": job.id,
        "source": job.source,
        "url": job.url,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "posted_date": job.posted_date,
        "captured_at": job.captured_at,
        "jd_text": job.jd_text,
        "status": job.status,
        "role_family": job.role_family,
        "seniority": job.seniority,
        "industry": job.industry,
        "extraction": ExtractionResponse(
            id=extraction.id,
            job_id=extraction.job_id,
            keywords_json=extraction.keywords_json,
            must_have_json=extraction.must_have_json,
            nice_to_have_json=extraction.nice_to_have_json,
            years_required=extraction.years_required,
            degree_required=extraction.degree_required,
            certifications_json=extraction.certifications_json,
            summary=extraction.summary,
            extraction_method=extraction.extraction_method,
            extracted_at=extraction.extracted_at
        ) if extraction else None
    }
    
    return JobResponse(**response_data)


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(job_id: UUID, job_data: JobUpdate, session: Session = Depends(get_session)):
    """更新职位信息"""
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # 更新字段
    update_data = job_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    # 如果jd_text更新了，重新运行提取
    if "jd_text" in update_data:
        from app.extractors.keyword_extractor import extract_and_save_sync
        try:
            extract_and_save_sync(
                job.id, 
                job.jd_text, 
                session,
                job_title=job.title,
                company=job.company,
                use_ai=True
            )
        except Exception as e:
            print(f"提取失败: {e}")
    
    session.add(job)
    session.commit()
    session.refresh(job)
    
    extraction = session.exec(select(Extraction).where(Extraction.job_id == job_id)).first()
    
    response_data = {
        "id": job.id,
        "source": job.source,
        "url": job.url,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "posted_date": job.posted_date,
        "captured_at": job.captured_at,
        "jd_text": job.jd_text,
        "status": job.status,
        "role_family": job.role_family,
        "seniority": job.seniority,
        "industry": job.industry,
        "extraction": ExtractionResponse(
            id=extraction.id,
            job_id=extraction.job_id,
            keywords_json=extraction.keywords_json,
            must_have_json=extraction.must_have_json,
            nice_to_have_json=extraction.nice_to_have_json,
            years_required=extraction.years_required,
            degree_required=extraction.degree_required,
            certifications_json=extraction.certifications_json,
            summary=extraction.summary,
            extraction_method=extraction.extraction_method,
            extracted_at=extraction.extracted_at
        ) if extraction else None
    }
    
    return JobResponse(**response_data)


@router.get("/{job_id}/extraction", response_model=ExtractionResponse)
def get_extraction(job_id: UUID, session: Session = Depends(get_session)):
    """获取职位的提取结果"""
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    extraction = session.exec(select(Extraction).where(Extraction.job_id == job_id)).first()
    if not extraction:
        raise HTTPException(status_code=404, detail="Extraction not found")
    
    return ExtractionResponse(
        id=extraction.id,
        job_id=extraction.job_id,
        keywords_json=extraction.keywords_json,
        must_have_json=extraction.must_have_json,
        nice_to_have_json=extraction.nice_to_have_json,
        years_required=extraction.years_required,
        degree_required=extraction.degree_required,
        certifications_json=extraction.certifications_json,
        summary=extraction.summary,
        extraction_method=extraction.extraction_method,
        extracted_at=extraction.extracted_at
    )