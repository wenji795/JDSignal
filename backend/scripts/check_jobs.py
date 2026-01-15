"""检查数据库中的职位数量"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine
from app.models import Job

db_path = backend_dir / "jobs.db"
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

with Session(engine) as session:
    jobs = session.exec(select(Job)).all()
    print(f"数据库中共有 {len(jobs)} 个职位")
    
    if jobs:
        print("\n前10个职位:")
        for i, job in enumerate(jobs[:10], 1):
            print(f"  {i}. {job.title} - {job.company} ({job.location or 'N/A'})")
        
        # 统计按location分组
        from collections import Counter
        locations = Counter(job.location for job in jobs if job.location)
        print(f"\n按地点统计:")
        for loc, count in locations.most_common(10):
            print(f"  {loc}: {count}")
    else:
        print("数据库中没有职位数据，需要重新抓取")
