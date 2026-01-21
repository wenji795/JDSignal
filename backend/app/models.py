"""数据库模型定义"""
from sqlmodel import SQLModel, Field, Relationship, Column, JSON, Text
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum


class JobStatus(str, Enum):
    """职位状态枚举"""
    NEW = "new"
    REVIEWED = "reviewed"
    APPLIED = "applied"
    REJECTED = "rejected"
    ACCEPTED = "accepted"


class Seniority(str, Enum):
    """资历级别枚举"""
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    PRINCIPAL = "principal"
    LEAD = "lead"
    MANAGER = "manager"
    ARCHITECT = "architect"
    GRADUATE = "graduate"
    UNKNOWN = "unknown"


class Job(SQLModel, table=True):
    """职位信息模型"""
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source: str = Field(index=True)  # 数据来源（如：linkedin, indeed, manual等）
    url: Optional[str] = None
    title: str = Field(index=True)
    company: str = Field(index=True)
    location: Optional[str] = None
    posted_date: Optional[datetime] = None
    captured_at: datetime = Field(default_factory=datetime.utcnow)
    jd_text: str = Field(sa_column=Column(Text))  # 职位描述文本
    status: JobStatus = Field(default=JobStatus.NEW, index=True)
    role_family: Optional[str] = Field(default=None, index=True)  # 如：backend, frontend, fullstack, devops等
    seniority: Optional[Seniority] = Field(default=None, index=True)
    
    # 关联的提取结果
    extraction: Optional["Extraction"] = Relationship(back_populates="job", sa_relationship_kwargs={"uselist": False})


class Extraction(SQLModel, table=True):
    """提取结果模型"""
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    job_id: UUID = Field(foreign_key="job.id", unique=True, index=True)
    keywords_json: dict = Field(default_factory=dict, sa_column=Column(JSON))  # 所有关键词的JSON
    must_have_json: dict = Field(default_factory=dict, sa_column=Column(JSON))  # 必须拥有的技能/要求
    nice_to_have_json: dict = Field(default_factory=dict, sa_column=Column(JSON))  # 加分项
    years_required: Optional[int] = None  # 所需经验年限
    degree_required: Optional[str] = None  # 所需学位
    certifications_json: dict = Field(default_factory=dict, sa_column=Column(JSON))  # 证书列表
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 关联的职位
    job: Job = Relationship(back_populates="extraction")