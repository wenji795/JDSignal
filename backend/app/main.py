"""FastAPI应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_db_and_tables
from app.routers import jobs, analytics, capture

app = FastAPI(
    title="Job JD Tracker & ATS Keyword Extractor",
    description="本地优先的职位JD追踪和ATS关键词提取系统",
    version="1.0.0"
)

# CORS配置：允许本地Chrome扩展和本地开发
# 注意：No automated crawling, only user-initiated capture
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

# 注册路由
app.include_router(jobs.router)
app.include_router(analytics.router)
app.include_router(capture.router)


@app.get("/")
def root():
    """根路径"""
    return {
        "message": "Job JD Tracker & ATS Keyword Extractor API",
        "docs": "/docs",
        "version": "1.0.0"
    }