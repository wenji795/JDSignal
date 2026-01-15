"""Pydantic schemas for API请求和响应"""
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from enum import Enum
from app.models import JobStatus, Seniority


class JobCreate(BaseModel):
    """
    创建职位请求
    
    支持两种模式：
    A) direct模式: 直接提供jd_text
    B) url_capture模式: 提供url和selected_text（可选jd_text）
    
    规则：
    - 如果jd_text缺失但selected_text存在，使用selected_text作为jd_text
    - 至少需要提供jd_text或selected_text之一
    - source字段自动设置为"manual"（有jd_text）或"capture"（有url和selected_text）
    """
    title: str = Field(..., description="职位标题", examples=["Senior Python Developer"])
    company: str = Field(..., description="公司名称", examples=["TechCorp Inc"])
    location: Optional[str] = Field(None, description="工作地点", examples=["San Francisco, CA"])
    posted_date: Optional[datetime] = Field(None, description="发布日期")
    status: JobStatus = Field(JobStatus.NEW, description="职位状态")
    role_family: Optional[str] = Field(None, description="角色族（如：backend, frontend）", examples=["backend"])
    seniority: Optional[Seniority] = Field(None, description="资历级别")
    
    # Direct模式字段
    jd_text: Optional[str] = Field(None, description="职位描述文本（直接模式）", examples=["We are looking for a Senior Python Developer..."])
    
    # URL capture模式字段
    url: Optional[str] = Field(None, description="职位页面URL（捕获模式）", examples=["https://linkedin.com/jobs/12345"])
    selected_text: Optional[str] = Field(None, description="从页面选中的文本（捕获模式）", examples=["Selected text from webpage..."])
    
    # Source字段（可选，如果不提供则自动推断）
    source: Optional[str] = Field(None, description="数据来源（如果提供则使用，否则自动推断）")
    
    @model_validator(mode='after')
    def validate_and_set_jd_text(self):
        """验证并设置jd_text和source"""
        # 如果jd_text缺失但selected_text存在，使用selected_text
        if not self.jd_text and self.selected_text:
            self.jd_text = self.selected_text
        
        # 验证至少有一个文本字段
        if not self.jd_text:
            raise ValueError("At least one of 'jd_text' or 'selected_text' must be provided")
        
        # 自动设置source字段
        if not self.source:
            if self.url:
                self.source = "capture"
            else:
                self.source = "manual"
        
        return self
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Senior Python Developer",
                    "company": "TechCorp Inc",
                    "location": "San Francisco, CA",
                    "jd_text": "We are looking for a Senior Python Developer with 5+ years of experience in Python, Django, and FastAPI.",
                    "role_family": "backend",
                    "seniority": "senior"
                },
                {
                    "title": "Full Stack Engineer",
                    "company": "WebStart Inc",
                    "url": "https://linkedin.com/jobs/67890",
                    "selected_text": "We need a Full Stack Engineer with React and Node.js experience.",
                    "role_family": "fullstack",
                    "seniority": "mid"
                }
            ]
        }
    }


class JobUpdate(BaseModel):
    """更新职位请求"""
    source: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    posted_date: Optional[datetime] = None
    jd_text: Optional[str] = None
    status: Optional[JobStatus] = None
    role_family: Optional[str] = None
    seniority: Optional[Seniority] = None


class ExtractionResponse(BaseModel):
    """提取结果响应"""
    id: UUID
    job_id: UUID
    keywords_json: Dict[str, Any]
    must_have_json: Dict[str, Any]
    nice_to_have_json: Dict[str, Any]
    years_required: Optional[int]
    degree_required: Optional[str]
    certifications_json: Dict[str, Any]
    extracted_at: datetime

    model_config = {"from_attributes": True}


class JobResponse(BaseModel):
    """职位响应"""
    id: UUID
    source: str
    url: Optional[str]
    title: str
    company: str
    location: Optional[str]
    posted_date: Optional[datetime]
    captured_at: datetime
    jd_text: str
    status: JobStatus
    role_family: Optional[str]
    seniority: Optional[Seniority]
    extraction: Optional[ExtractionResponse] = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    """职位列表响应（简化版）"""
    id: UUID
    source: str
    title: str
    company: str
    location: Optional[str]
    status: JobStatus
    role_family: Optional[str]
    seniority: Optional[Seniority]
    captured_at: datetime

    model_config = {"from_attributes": True}


class CaptureSource(str, Enum):
    """捕获来源枚举"""
    SEEK = "seek"
    LINKEDIN = "linkedin"
    OTHER = "other"


class CaptureRequest(BaseModel):
    """
    捕获请求（用于Chrome扩展）
    
    注意：此端点仅用于用户主动触发的捕获操作，不进行自动爬取。
    No automated crawling, only user-initiated capture.
    """
    source: CaptureSource = Field(..., description="数据来源", examples=["linkedin"])
    url: str = Field(..., description="职位页面URL", examples=["https://linkedin.com/jobs/view/123456"])
    page_title: str = Field(..., description="页面标题", examples=["Senior Python Developer at TechCorp"])
    company_guess: Optional[str] = Field(None, description="推测的公司名称", examples=["TechCorp"])
    location_guess: Optional[str] = Field(None, description="推测的工作地点", examples=["San Francisco, CA"])
    extracted_text: str = Field(..., description="用户主动提取的文本（DOM提取或选中文本）", examples=["We are looking for a Senior Python Developer..."])
    captured_at: Optional[datetime] = Field(None, description="捕获时间（如果不提供则使用当前时间）")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "source": "linkedin",
                    "url": "https://linkedin.com/jobs/view/123456",
                    "page_title": "Senior Python Developer at TechCorp",
                    "company_guess": "TechCorp",
                    "location_guess": "San Francisco, CA",
                    "extracted_text": "We are looking for a Senior Python Developer with 5+ years of experience..."
                }
            ]
        }
    }


class CaptureResponse(BaseModel):
    """捕获响应"""
    job_id: UUID
    top_keywords: List[Dict[str, Any]] = Field(..., description="前20个关键词（按分数排序）")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "job_id": "123e4567-e89b-12d3-a456-426614174000",
                    "top_keywords": [
                        {"term": "Python", "category": "language", "score": 5.0},
                        {"term": "Django", "category": "framework", "score": 4.0}
                    ]
                }
            ]
        }
    }