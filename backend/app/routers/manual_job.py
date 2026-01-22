"""手动输入职位JD的API端点"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.database import get_session
from app.models import Job, Extraction, JobStatus
from app.schemas import JobResponse, ExtractionResponse
from app.extractors.keyword_extractor import extract_and_save_sync
from app.extractors.ai_role_inferrer import infer_role_and_seniority_with_ai

router = APIRouter(prefix="/manual-job", tags=["manual-job"])


class ManualJobCreate(BaseModel):
    """手动输入职位JD请求"""
    title: str = Field(..., description="职位标题")
    company: Optional[str] = Field(None, description="公司名称")
    location: Optional[str] = Field(None, description="工作地点")
    jd_text: str = Field(..., description="职位描述文本（纯文本）")
    url: Optional[str] = Field(None, description="职位URL（可选）")


@router.post(
    "",
    response_model=JobResponse,
    status_code=201,
    summary="手动输入职位JD",
    description="通过纯文本形式手动输入职位JD，系统会自动提取关键词并推断角色族和资历级别"
)
def create_manual_job(
    job_data: ManualJobCreate,
    session: Session = Depends(get_session)
):
    """手动创建职位并自动运行提取"""
    # 检查URL是否已存在（如果提供了URL）
    if job_data.url:
        existing = session.exec(select(Job).where(Job.url == job_data.url)).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"职位URL已存在: {job_data.url}"
            )
    
    # 自动推断role_family和seniority（AI优先）
    import asyncio
    role_family, seniority = asyncio.run(infer_role_and_seniority_with_ai(
        job_data.title,
        job_data.jd_text,
        use_ai=True
    ))
    
    # 创建Job记录
    job = Job(
        source="manual",
        url=job_data.url,
        title=job_data.title,
        company=job_data.company or "Unknown",
        location=job_data.location,
        jd_text=job_data.jd_text,
        role_family=role_family,
        seniority=seniority,
        status=JobStatus.NEW
    )
    
    session.add(job)
    session.commit()
    session.refresh(job)
    
    # 自动运行提取（支持AI增强）
    try:
        extract_and_save_sync(
            job.id, 
            job.jd_text, 
            session,
            job_title=job.title,
            company=job.company,
            use_ai=True
        )
        session.refresh(job)
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
