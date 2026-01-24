"""手动触发抓取任务的API端点"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
import asyncio

router = APIRouter(prefix="/scraper", tags=["scraper"])


class ScrapeRequest(BaseModel):
    """抓取请求"""
    max_per_keyword: int = Field(50, description="每个关键词最多抓取多少个职位", ge=1, le=100)
    headless: bool = Field(True, description="是否使用无头模式（后台运行）")
    browser: str = Field("firefox", description="使用的浏览器", pattern="^(chromium|firefox|webkit)$")


async def run_scrape_task(max_per_keyword: int, headless: bool, browser: str):
    """后台运行抓取任务"""
    try:
        from app.services.scraper_service import scrape_nz_jobs_incremental
        await scrape_nz_jobs_incremental(
            max_per_keyword=max_per_keyword,
            headless=headless,
            browser=browser
        )
    except ImportError as e:
        error_msg = str(e)
        if 'playwright' in error_msg.lower():
            print("✗ 手动抓取任务执行失败: playwright模块未安装")
            print("  请运行以下命令安装：")
            print("    pip install playwright")
            print("    playwright install firefox  # 或 playwright install chromium")
        else:
            print(f"✗ 手动抓取任务执行失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"✗ 手动抓取任务执行失败: {e}")
        import traceback
        traceback.print_exc()


@router.post(
    "/trigger",
    summary="手动触发抓取任务",
    description="立即执行一次增量抓取任务，抓取新西兰Seek上的最新职位"
)
async def trigger_scrape(
    request: Optional[ScrapeRequest] = None,
    background_tasks: BackgroundTasks = None
):
    """
    手动触发抓取任务
    
    此端点会立即在后台执行一次增量抓取任务，抓取新西兰Seek上的最新职位。
    任务在后台运行，不会阻塞API响应。
    """
    if request is None:
        request = ScrapeRequest()
    
    # 在后台执行抓取任务
    background_tasks.add_task(
        run_scrape_task,
        request.max_per_keyword,
        request.headless,
        request.browser
    )
    
    return {
        "message": "抓取任务已启动",
        "status": "running",
        "max_per_keyword": request.max_per_keyword,
        "headless": request.headless,
        "browser": request.browser,
        "note": "任务在后台运行，请查看后端日志了解进度"
    }


@router.get(
    "/status",
    summary="获取抓取任务状态",
    description="获取最近一次抓取任务的状态（简化版）"
)
async def get_scrape_status():
    """获取抓取任务状态"""
    # 这里可以添加更详细的状态跟踪逻辑
    return {
        "message": "抓取任务状态",
        "note": "当前版本不跟踪任务状态，请查看后端日志"
    }
