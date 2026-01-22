"""更新现有职位的posted_date - 使用AI从JD文本中提取"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select
from app.database import engine
from app.models import Job
from app.extractors.ai_enhanced_extractor import extract_with_ai


async def update_posted_date_for_job(job: Job, session: Session) -> bool:
    """为单个职位更新posted_date"""
    try:
        # 如果已经有posted_date，跳过
        if job.posted_date:
            return False
        
        # 使用AI提取posted_date
        print(f"正在处理: {job.title} ({job.company})")
        ai_result = await extract_with_ai(
            job.jd_text,
            job_title=job.title,
            company=job.company
        )
        
        if ai_result.get("success") and ai_result.get("posted_date"):
            try:
                posted_date_str = ai_result.get("posted_date")
                if isinstance(posted_date_str, str):
                    # 解析日期字符串
                    posted_date = datetime.fromisoformat(posted_date_str.replace('Z', '+00:00'))
                    job.posted_date = posted_date
                    session.add(job)
                    session.commit()
                    print(f"  ✓ 更新posted_date: {posted_date.strftime('%Y-%m-%d')}")
                    return True
            except Exception as e:
                print(f"  ✗ 解析posted_date失败: {e}")
                return False
        else:
            print(f"  ⚠ AI未提取到posted_date")
            return False
            
    except Exception as e:
        print(f"  ✗ 处理失败: {e}")
        session.rollback()
        return False


async def update_all_posted_dates(limit: Optional[int] = None, source: Optional[str] = None):
    """更新所有缺少posted_date的职位"""
    with Session(engine) as session:
        # 查询缺少posted_date的职位
        statement = select(Job).where(Job.posted_date.is_(None))
        
        # 如果指定了source，添加过滤条件
        if source:
            statement = statement.where(Job.source == source)
        
        # 如果指定了limit，限制数量
        if limit:
            statement = statement.limit(limit)
        
        jobs = session.exec(statement).all()
        total_jobs = len(jobs)
        
        if total_jobs == 0:
            print("没有需要更新posted_date的职位")
            return
        
        print(f"找到 {total_jobs} 个需要更新posted_date的职位")
        print("=" * 60)
        
        success_count = 0
        fail_count = 0
        
        for i, job in enumerate(jobs, 1):
            print(f"\n[{i}/{total_jobs}]")
            if await update_posted_date_for_job(job, session):
                success_count += 1
            else:
                fail_count += 1
            
            # 每10个职位暂停一下，避免API限流
            if i % 10 == 0:
                print(f"\n已处理 {i}/{total_jobs} 个职位，暂停2秒...")
                await asyncio.sleep(2)
        
        print("\n" + "=" * 60)
        print(f"更新完成！")
        print(f"成功: {success_count} 个")
        print(f"失败: {fail_count} 个")
        print(f"总计: {total_jobs} 个")


def check_posted_dates_status():
    """检查posted_date的状态"""
    with Session(engine) as session:
        # 统计总数
        total_jobs = len(session.exec(select(Job)).all())
        
        # 统计有posted_date的数量
        jobs_with_date = len(session.exec(select(Job).where(Job.posted_date.isnot(None))).all())
        
        # 统计没有posted_date的数量
        jobs_without_date = len(session.exec(select(Job).where(Job.posted_date.is_(None))).all())
        
        # 按source分组统计
        all_jobs = session.exec(select(Job)).all()
        by_source = {}
        for job in all_jobs:
            source = job.source
            if source not in by_source:
                by_source[source] = {"total": 0, "with_date": 0, "without_date": 0}
            by_source[source]["total"] += 1
            if job.posted_date:
                by_source[source]["with_date"] += 1
            else:
                by_source[source]["without_date"] += 1
        
        print("=" * 60)
        print("Posted Date 状态统计")
        print("=" * 60)
        print(f"总职位数: {total_jobs}")
        print(f"有 posted_date: {jobs_with_date} ({jobs_with_date/total_jobs*100:.1f}%)")
        print(f"无 posted_date: {jobs_without_date} ({jobs_without_date/total_jobs*100:.1f}%)")
        print("\n按来源统计:")
        for source, stats in by_source.items():
            print(f"  {source}:")
            print(f"    总数: {stats['total']}")
            print(f"    有日期: {stats['with_date']} ({stats['with_date']/stats['total']*100:.1f}%)")
            print(f"    无日期: {stats['without_date']} ({stats['without_date']/stats['total']*100:.1f}%)")
        print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='更新职位的posted_date')
    parser.add_argument('--check', action='store_true', help='只检查状态，不更新')
    parser.add_argument('--limit', type=int, help='限制更新的数量')
    parser.add_argument('--source', type=str, help='只更新指定来源的职位（如：seek）')
    
    args = parser.parse_args()
    
    if args.check:
        check_posted_dates_status()
    else:
        asyncio.run(update_all_posted_dates(limit=args.limit, source=args.source))
