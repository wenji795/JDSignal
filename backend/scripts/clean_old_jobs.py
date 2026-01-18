"""清理数据库中6个月前的职位数据"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine
from app.models import Job, Extraction

# 使用与主应用相同的数据库路径
db_path = backend_dir / "jobs.db"
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def clean_old_jobs(months: int = 6, dry_run: bool = True):
    """
    清理指定月数之前的职位数据
    
    Args:
        months: 保留最近几个月的数据（默认6个月）
        dry_run: 如果为True，只显示将要删除的数据，不实际删除
    """
    cutoff_date = datetime.utcnow() - timedelta(days=months * 30)
    
    print(f"{'='*60}")
    print(f"清理 {months} 个月前的职位数据")
    print(f"{'='*60}")
    print(f"当前时间: {datetime.utcnow().isoformat()}")
    print(f"截止日期: {cutoff_date.isoformat()}")
    print(f"模式: {'预览模式（不会实际删除）' if dry_run else '删除模式'}")
    print()
    
    with Session(engine) as session:
        # 查找需要删除的职位（基于captured_at）
        old_jobs_query = select(Job).where(Job.captured_at < cutoff_date)
        old_jobs = session.exec(old_jobs_query).all()
        
        if not old_jobs:
            print("✓ 没有需要清理的旧数据")
            return
        
        print(f"找到 {len(old_jobs)} 个需要清理的职位")
        print()
        
        # 统计信息
        total_extractions = 0
        for job in old_jobs:
            extraction = session.exec(
                select(Extraction).where(Extraction.job_id == job.id)
            ).first()
            if extraction:
                total_extractions += 1
        
        print(f"统计信息:")
        print(f"  - 职位数量: {len(old_jobs)}")
        print(f"  - 提取结果数量: {total_extractions}")
        print()
        
        if dry_run:
            print("预览模式：以下职位将被删除（前10个）:")
            for i, job in enumerate(old_jobs[:10], 1):
                print(f"  {i}. {job.title[:60]}... (抓取时间: {job.captured_at.isoformat()})")
            if len(old_jobs) > 10:
                print(f"  ... 还有 {len(old_jobs) - 10} 个职位")
            print()
            print("提示: 使用 --delete 参数来实际执行删除操作")
        else:
            # 实际删除
            deleted_jobs = 0
            deleted_extractions = 0
            
            for job in old_jobs:
                # 删除关联的Extraction（如果存在）
                extraction = session.exec(
                    select(Extraction).where(Extraction.job_id == job.id)
                ).first()
                if extraction:
                    session.delete(extraction)
                    deleted_extractions += 1
                
                # 删除Job
                session.delete(job)
                deleted_jobs += 1
            
            # 提交事务
            session.commit()
            
            print(f"✓ 清理完成!")
            print(f"  - 已删除职位: {deleted_jobs} 个")
            print(f"  - 已删除提取结果: {deleted_extractions} 个")
            
            # 显示数据库大小变化
            if db_path.exists():
                size_mb = db_path.stat().st_size / (1024 * 1024)
                print(f"  - 当前数据库大小: {size_mb:.2f} MB")
    
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='清理数据库中6个月前的职位数据')
    parser.add_argument('--months', type=int, default=6, help='保留最近几个月的数据（默认6个月）')
    parser.add_argument('--delete', action='store_true', help='实际执行删除操作（默认只是预览）')
    
    args = parser.parse_args()
    
    clean_old_jobs(months=args.months, dry_run=not args.delete)
