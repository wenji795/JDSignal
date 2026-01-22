"""测试 product manager 推断逻辑"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine
from app.models import Job
from app.extractors.role_inferrer import infer_role_family

db_path = backend_dir / "jobs.db"
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

with Session(engine) as session:
    # 查找几个真正的 product manager 职位
    pm_titles = ['Product Manager', 'Product Owner', 'Senior Product Manager']
    for title_pattern in pm_titles:
        jobs = session.exec(select(Job).where(Job.title.like(f'%{title_pattern}%'))).all()
        if jobs:
            job = jobs[0]
            inferred = infer_role_family(job.title, job.jd_text)
            print(f"标题: {job.title[:80]}")
            print(f"当前分类: {job.role_family}")
            print(f"推断分类: {inferred}")
            print("---")
