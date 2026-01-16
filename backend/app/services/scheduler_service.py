"""定时任务调度服务"""
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    AsyncIOScheduler = None
    CronTrigger = None

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
    
    scheduler.start()
    print("✓ 定时任务调度器已启动")
    print("  - 每小时自动抓取新西兰职位（每小时的第0分钟）")


def stop_scheduler():
    """停止定时任务调度器"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        print("定时任务调度器已停止")
