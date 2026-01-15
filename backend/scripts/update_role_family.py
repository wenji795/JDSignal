"""
更新已有职位的role_family和seniority字段
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine
from app.models import Job
from app.extractors.role_inferrer import infer_role_and_seniority
from app.database import create_db_and_tables

# 使用与主应用相同的数据库路径（相对于backend目录）
backend_dir = Path(__file__).parent.parent
db_path = backend_dir / "jobs.db"
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def update_all_jobs():
    """更新所有职位的role_family和seniority"""
    # 确保数据库表存在
    create_db_and_tables()
    
    with Session(engine) as session:
        # 获取所有没有role_family或seniority的职位
        jobs = session.exec(select(Job)).all()
        
        updated_count = 0
        
        for job in jobs:
            # 推断role_family和seniority
            role_family, seniority = infer_role_and_seniority(job.title, job.jd_text)
            
            # 如果推断出结果且与现有值不同，则更新
            if role_family and job.role_family != role_family:
                job.role_family = role_family
                updated_count += 1
                print(f"✓ 更新 {job.title[:50]}... role_family: {job.role_family} -> {role_family}")
            
            if seniority and job.seniority != seniority:
                job.seniority = seniority
                updated_count += 1
                print(f"✓ 更新 {job.title[:50]}... seniority: {job.seniority} -> {seniority}")
            
            session.add(job)
        
        session.commit()
        print(f"\n完成！共更新 {updated_count} 个字段")


if __name__ == "__main__":
    print("开始更新已有职位的role_family和seniority...")
    update_all_jobs()
