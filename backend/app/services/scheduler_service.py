"""定时任务调度服务"""
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from datetime import datetime
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    AsyncIOScheduler = None
    CronTrigger = None
    datetime = None

import asyncio

scheduler = None


async def run_scraper():
    """包装异步抓取函数"""
    try:
        # 延迟导入，避免在模块加载时就导入
        from app.services.scraper_service import scrape_nz_jobs_incremental
        await scrape_nz_jobs_incremental(
            max_per_keyword=5,
            headless=True,
            browser='firefox'
        )
    except Exception as e:
        print(f"✗ 自动抓取任务执行失败: {e}")
        import traceback
        traceback.print_exc()


async def clean_old_data():
    """清理6个月前的数据"""
    try:
        from datetime import datetime, timedelta
        from sqlmodel import Session, select
        from app.database import engine
        from app.models import Job, Extraction
        
        cutoff_date = datetime.utcnow() - timedelta(days=180)  # 6个月
        
        with Session(engine) as session:
            # 查找需要删除的职位
            old_jobs_query = select(Job).where(Job.captured_at < cutoff_date)
            old_jobs = session.exec(old_jobs_query).all()
            
            if not old_jobs:
                print("✓ 数据清理：没有需要清理的旧数据")
                return
            
            deleted_count = 0
            for job in old_jobs:
                # 删除关联的Extraction
                extraction = session.exec(
                    select(Extraction).where(Extraction.job_id == job.id)
                ).first()
                if extraction:
                    session.delete(extraction)
                
                # 删除Job
                session.delete(job)
                deleted_count += 1
            
            session.commit()
            print(f"✓ 数据清理：已删除 {deleted_count} 个6个月前的职位")
            
    except Exception as e:
        print(f"✗ 数据清理任务执行失败: {e}")
        import traceback
        traceback.print_exc()


def start_scheduler():
    """启动定时任务调度器"""
    global scheduler
    
    if not APSCHEDULER_AVAILABLE:
        print("⚠ 警告: apscheduler未安装，定时任务功能已禁用")
        return
    
    if scheduler is None:
        scheduler = AsyncIOScheduler()
    
    # 每小时执行一次（每小时的第0分钟）
    scheduler.add_job(
        run_scraper,
        trigger=CronTrigger(minute=0),  # 每小时的第0分钟执行
        id='hourly_scrape',
        name='每小时抓取新西兰职位',
        max_instances=1,  # 同一时间只允许一个实例运行
        replace_existing=True
    )
    
    # 每天凌晨2点执行数据清理（清理6个月前的数据）
    scheduler.add_job(
        clean_old_data,
        trigger=CronTrigger(hour=2, minute=0),  # 每天凌晨2点执行
        id='daily_cleanup',
        name='每天清理6个月前的数据',
        max_instances=1,
        replace_existing=True
    )
    
    scheduler.start()
    print("✓ 定时任务调度器已启动")
    print("  - 每小时自动抓取新西兰职位（每小时的第0分钟）")
    print("  - 每天自动清理6个月前的数据（每天凌晨2点）")
    
    # 启动时立即执行一次抓取任务（使用scheduler添加一次性任务）
    print("  - 正在启动时立即执行一次抓取任务...")
    scheduler.add_job(
        run_scraper,
        trigger='date',
        run_date=datetime.now(),  # 立即执行
        id='startup_scrape',
        name='启动时立即抓取',
        max_instances=1,
        replace_existing=True
    )


def stop_scheduler():
    """停止定时任务调度器"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        print("定时任务调度器已停止")
