"""删除数据库中的所有数据"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import Session, select
from app.database import engine, create_db_and_tables
from app.models import Job, Extraction


def delete_all_data():
    """删除数据库中的所有数据"""
    print("开始删除数据库中的所有数据...")
    
    with Session(engine) as session:
        # 先删除所有Extraction记录（因为有外键约束）
        extractions = session.exec(select(Extraction)).all()
        extraction_count = len(extractions)
        for extraction in extractions:
            session.delete(extraction)
        print(f"✓ 删除了 {extraction_count} 条提取记录")
        
        # 再删除所有Job记录
        jobs = session.exec(select(Job)).all()
        job_count = len(jobs)
        for job in jobs:
            session.delete(job)
        print(f"✓ 删除了 {job_count} 条职位记录")
        
        # 提交更改
        session.commit()
        print(f"\n✓ 成功删除所有数据！")
        print(f"  - 职位记录: {job_count}")
        print(f"  - 提取记录: {extraction_count}")


if __name__ == "__main__":
    try:
        delete_all_data()
    except Exception as e:
        print(f"❌ 删除数据时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
