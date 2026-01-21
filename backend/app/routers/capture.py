"""捕获端点（用于Chrome扩展）"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Dict, Any
from datetime import datetime
from uuid import UUID

from app.database import get_session
from app.models import Job, Extraction, JobStatus
from app.schemas import CaptureRequest, CaptureResponse
from app.extractors.keyword_extractor import extract_and_save
from app.extractors.role_inferrer import infer_role_and_seniority

router = APIRouter(prefix="/capture", tags=["capture"])


@router.post(
    "",
    response_model=CaptureResponse,
    status_code=201,
    summary="捕获职位信息",
    description="""
    捕获职位信息（用于Chrome扩展）。
    
    注意：此端点仅用于用户主动触发的捕获操作，不进行自动爬取。
    No automated crawling, only user-initiated capture.
    
    行为：
    - 使用extracted_text作为jd_text创建Job
    - 自动运行关键词提取并存储结果
    - 返回创建的job_id和top 20关键词
    """
)
def capture_job(capture_data: CaptureRequest, session: Session = Depends(get_session)):
    """
    捕获职位信息
    
    注意：此端点仅用于用户主动触发的捕获操作，不进行自动爬取。
    No automated crawling, only user-initiated capture.
    
    此端点从Chrome扩展接收用户主动提取的职位信息（通过DOM提取或文本选择），
    创建Job记录并运行关键词提取。
    """
    # 检查URL是否已存在（如果提供了URL）
    if capture_data.url:
        existing = session.exec(select(Job).where(Job.url == capture_data.url)).first()
        if existing:
            # 如果已存在，返回现有职位信息
            extraction = session.exec(select(Extraction).where(Extraction.job_id == existing.id)).first()
            keywords_data = extraction.keywords_json.get("keywords", []) if extraction else []
            top_keywords = keywords_data[:20] if keywords_data else []
            
            return CaptureResponse(
                job_id=existing.id,
                top_keywords=top_keywords,
                message="职位已存在（URL重复）"
            )
    
    # 准备Job数据
    captured_at = capture_data.captured_at if capture_data.captured_at else datetime.utcnow()
    
    # 自动推断role_family和seniority
    role_family, seniority = infer_role_and_seniority(
        capture_data.page_title,
        capture_data.extracted_text
    )
    
    # 使用page_title作为title，company_guess作为company
    # 如果 company_guess 为空或 "Unknown"，则不设置 company 字段（让它为 None）
    company = capture_data.company_guess
    if company and company.strip().lower() not in ['unknown', '']:
        company = company.strip()
    else:
        company = None
    
    job_data = {
        "source": capture_data.source.value,
        "url": capture_data.url,
        "title": capture_data.page_title,
        "company": company,
        "location": capture_data.location_guess,
        "jd_text": capture_data.extracted_text,
        "status": JobStatus.NEW,
        "role_family": role_family,
        "seniority": seniority,
        "captured_at": captured_at
    }
    
    # 创建Job
    job = Job(**job_data)
    session.add(job)
    session.commit()
    session.refresh(job)
    
    # 运行提取并存储结果（支持AI增强）
    extraction_success = False
    try:
        from app.extractors.keyword_extractor import extract_and_save_sync
        extract_and_save_sync(
            job.id, 
            job.jd_text, 
            session,
            job_title=job.title,
            company=job.company,
            use_ai=True
        )
        session.refresh(job)
        extraction_success = True
    except Exception as e:
        # 记录详细错误信息
        import traceback
        error_detail = f"Failed to extract keywords: {str(e)}\n{traceback.format_exc()}"
        print(f"提取关键词失败: {error_detail}")
        # 即使提取失败，也继续处理（职位已创建）
        # 尝试回滚可能的数据库更改
        try:
            session.rollback()
        except:
            pass
        # 刷新job以确保状态正确
        try:
            session.refresh(job)
        except:
            pass
    
    # 获取提取结果
    extraction = session.exec(select(Extraction).where(Extraction.job_id == job.id)).first()
    
    # 如果没有提取结果，返回空的关键词列表（职位已创建，但提取失败）
    if not extraction:
        return CaptureResponse(
            job_id=job.id,
            top_keywords=[],
            message="职位已创建，但关键词提取失败"
        )
    
    # 获取top 20关键词
    keywords_data = extraction.keywords_json.get("keywords", [])
    top_keywords = keywords_data[:20] if keywords_data else []  # 取前20个（已经按分数排序）
    
    return CaptureResponse(
        job_id=job.id,
        top_keywords=top_keywords
    )