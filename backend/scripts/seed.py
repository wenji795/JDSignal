"""种子数据脚本"""
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))

from sqlmodel import Session, select
from app.database import engine, create_db_and_tables
from app.models import Job, JobStatus, Seniority
from app.extractors.keyword_extractor import extract_and_save

# 3个示例职位描述
SAMPLE_JOBS = [
    {
        "source": "linkedin",
        "url": "https://linkedin.com/jobs/12345",
        "title": "Senior Python Backend Developer",
        "company": "TechCorp Inc",
        "location": "San Francisco, CA",
        "posted_date": datetime(2024, 1, 15),
        "jd_text": """
        We are looking for a Senior Python Backend Developer with 5+ years of experience 
        in Python, Django, and FastAPI. Experience with PostgreSQL, Redis, and Docker 
        is required. AWS certified professionals preferred. 
        Bachelor's degree in Computer Science or related field required.
        
        Required Skills:
        - Python, Django, FastAPI
        - PostgreSQL, Redis
        - Docker, Kubernetes
        - REST API design
        
        Preferred Skills:
        - AWS (AWS Certified Solutions Architect)
        - GraphQL
        - Microservices architecture
        - CI/CD pipelines
        """,
        "status": JobStatus.NEW,
        "role_family": "backend",
        "seniority": Seniority.SENIOR
    },
    {
        "source": "indeed",
        "url": "https://indeed.com/viewjob?jk=67890",
        "title": "Full Stack JavaScript Engineer",
        "company": "WebStart Inc",
        "location": "Remote",
        "posted_date": datetime(2024, 1, 20),
        "jd_text": """
        Join our team as a Full Stack JavaScript Engineer. Requires 3+ years of 
        experience with React, Node.js, and TypeScript. Experience with MongoDB, 
        Express, and REST APIs required. Master's degree preferred. Kubernetes and 
        Docker experience is a plus.
        
        Must Have:
        - React, Node.js, TypeScript
        - MongoDB, Express
        - REST API development
        - Git, Agile methodologies
        
        Nice to Have:
        - Kubernetes
        - Docker
        - GraphQL
        - Test-driven development
        """,
        "status": JobStatus.NEW,
        "role_family": "fullstack",
        "seniority": Seniority.MID
    },
    {
        "source": "manual",
        "url": None,
        "title": "DevOps Engineer",
        "company": "CloudScale",
        "location": "New York, NY",
        "posted_date": datetime(2024, 2, 1),
        "jd_text": """
        DevOps Engineer needed with 4+ years of experience in AWS, Azure, 
        Kubernetes, and Terraform. AWS Certified Solutions Architect preferred. 
        Experience with CI/CD pipelines, Jenkins, and Git required. 
        Bachelor's degree required.
        
        Required Qualifications:
        - 4+ years of DevOps experience
        - AWS, Azure cloud platforms
        - Kubernetes, Docker
        - Terraform, Infrastructure as Code
        - Jenkins, CI/CD
        - Git version control
        
        Preferred:
        - AWS Certified Solutions Architect
        - Azure certifications
        - Python scripting
        - Monitoring tools (Prometheus, Grafana)
        """,
        "status": JobStatus.NEW,
        "role_family": "devops",
        "seniority": Seniority.MID
    }
]


def seed_data():
    """填充种子数据"""
    # 创建数据库表
    create_db_and_tables()
    
    # 创建会话并插入数据
    with Session(engine) as session:
        # 检查是否已有数据
        count = len(session.exec(select(Job)).all())
        if count > 0:
            print(f"数据库已有 {count} 条记录，跳过种子数据填充")
            return
        
        # 插入种子数据并运行提取
        for job_data in SAMPLE_JOBS:
            job = Job(**job_data)
            session.add(job)
            session.commit()
            session.refresh(job)
            
            # 运行提取
            try:
                extract_and_save(job.id, job.jd_text, session)
                print(f"✓ 创建职位并提取关键词: {job.title} at {job.company}")
            except Exception as e:
                print(f"✗ 提取关键词失败: {job.title} - {e}")
        
        print(f"\n成功插入 {len(SAMPLE_JOBS)} 条职位记录")


if __name__ == "__main__":
    seed_data()