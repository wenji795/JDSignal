"""种子数据脚本"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlmodel import Session, select
from app.database import engine, create_db_and_tables
from app.models import Job
from datetime import datetime

# 示例职位描述
SAMPLE_JOBS = [
    {
        "title": "Senior Python Developer",
        "company": "TechCorp",
        "description": """
        We are looking for a Senior Python Developer with 5+ years of experience 
        in Python, Django, and FastAPI. Experience with PostgreSQL, Redis, and 
        Docker is required. AWS certified professionals preferred. 
        Bachelor's degree in Computer Science or related field required.
        """,
        "location": "San Francisco, CA",
        "posted_date": datetime(2024, 1, 15)
    },
    {
        "title": "Full Stack JavaScript Engineer",
        "company": "WebStart Inc",
        "description": """
        Join our team as a Full Stack JavaScript Engineer. Requires 3+ years of 
        experience with React, Node.js, and TypeScript. Experience with MongoDB, 
        Express, and REST APIs. Master's degree preferred. Kubernetes and 
        Docker experience is a plus.
        """,
        "location": "Remote",
        "posted_date": datetime(2024, 1, 20)
    },
    {
        "title": "DevOps Engineer",
        "company": "CloudScale",
        "description": """
        DevOps Engineer needed with 4+ years of experience in AWS, Azure, 
        Kubernetes, and Terraform. AWS Certified Solutions Architect preferred. 
        Experience with CI/CD pipelines, Jenkins, and Git. Bachelor's degree required.
        """,
        "location": "New York, NY",
        "posted_date": datetime(2024, 2, 1)
    },
    {
        "title": "Machine Learning Engineer",
        "company": "AI Innovations",
        "description": """
        Machine Learning Engineer position. Requires 3+ years of experience with 
        Python, TensorFlow, PyTorch, and deep learning. Experience with SQL and 
        PostgreSQL. Master's degree or PhD in related field required.
        """,
        "location": "Boston, MA",
        "posted_date": datetime(2024, 2, 5)
    },
    {
        "title": "Backend Engineer - Java",
        "company": "Enterprise Solutions",
        "description": """
        Backend Engineer with 5+ years of Java experience. Spring Boot, 
        Microservices, and SQL expertise required. Experience with Redis and 
        Kafka preferred. Bachelor's degree in Computer Science required.
        """,
        "location": "Austin, TX",
        "posted_date": datetime(2024, 2, 10)
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
        
        # 插入种子数据
        for job_data in SAMPLE_JOBS:
            job = Job(**job_data)
            session.add(job)
        
        session.commit()
        print(f"成功插入 {len(SAMPLE_JOBS)} 条职位记录")


if __name__ == "__main__":
    seed_data()