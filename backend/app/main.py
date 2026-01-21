"""FastAPI应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_db_and_tables
from app.routers import jobs, analytics, capture, manual_job, scraper

# 加载 .env 文件中的环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果没有安装 python-dotenv，跳过（可以使用系统环境变量）
    pass

# 尝试导入定时任务服务（可选）
try:
    from app.services.scheduler_service import start_scheduler, stop_scheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    print("⚠ 警告: apscheduler未安装，定时任务功能已禁用")
    print("  要启用自动抓取功能，请运行: pip install apscheduler==3.10.4")

app = FastAPI(
    title="Job JD Tracker & ATS Keyword Extractor",
    description="本地优先的职位JD追踪和ATS关键词提取系统",
    version="1.0.0"
)

# CORS配置：允许本地Chrome扩展和本地开发
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"chrome-extension://.*",  # 允许所有Chrome扩展
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库表
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    # 启动定时任务调度器（每小时自动抓取）- 如果可用
    if SCHEDULER_AVAILABLE:
        try:
            start_scheduler()
        except Exception as e:
            print(f"⚠ 警告: 定时任务启动失败: {e}")

@app.on_event("shutdown")
def on_shutdown():
    # 停止定时任务调度器 - 如果可用
    if SCHEDULER_AVAILABLE:
        try:
            stop_scheduler()
        except Exception:
            pass

# 注册路由
app.include_router(jobs.router)
app.include_router(analytics.router)
app.include_router(capture.router)
app.include_router(manual_job.router)
app.include_router(scraper.router)


@app.get("/")
def root():
    """根路径"""
    return {
        "message": "Job JD Tracker & ATS Keyword Extractor API",
        "docs": "/docs",
        "version": "1.0.0"
    }