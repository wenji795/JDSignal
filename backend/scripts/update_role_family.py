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


def update_all_jobs(force_update: bool = True):
    """
    更新所有职位的role_family和seniority
    
    Args:
        force_update: 如果为True，强制更新所有职位（即使已有值）；如果为False，只更新空值
    """
    # 确保数据库表存在
    create_db_and_tables()
    
    with Session(engine) as session:
        # 获取所有职位
        jobs = session.exec(select(Job)).all()
        
        updated_role_family_count = 0
        updated_seniority_count = 0
        
        for job in jobs:
            # 推断role_family和seniority
            new_role_family, new_seniority = infer_role_and_seniority(job.title, job.jd_text)
            
            # 更新role_family
            if new_role_family:
                if force_update or not job.role_family or job.role_family != new_role_family:
                    old_role_family = job.role_family
                    job.role_family = new_role_family
                    updated_role_family_count += 1
                    print(f"✓ 更新 {job.title[:50]}... role_family: {old_role_family} -> {new_role_family}")
            
            # 更新seniority
            if new_seniority:
                if force_update or not job.seniority or job.seniority != new_seniority:
                    old_seniority = job.seniority
                    job.seniority = new_seniority
                    updated_seniority_count += 1
                    print(f"✓ 更新 {job.title[:50]}... seniority: {old_seniority} -> {new_seniority}")
            
            session.add(job)
        
        session.commit()
        print(f"\n完成！共更新 {updated_role_family_count} 个role_family字段，{updated_seniority_count} 个seniority字段")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="更新已有职位的role_family和seniority")
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制更新所有职位（即使已有值），默认只更新空值"
    )
    
    args = parser.parse_args()
    
    print("开始更新已有职位的role_family和seniority...")
    if args.force:
        print("模式：强制更新所有职位")
    else:
        print("模式：只更新空值")
    
    update_all_jobs(force_update=args.force)
