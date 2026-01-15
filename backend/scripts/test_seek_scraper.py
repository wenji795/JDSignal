"""测试Seek抓取功能（简化版）"""
import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))

from playwright.async_api import async_playwright

async def test_seek_single_job():
    """测试抓取单个Seek职位（更简单的方式）"""
    # 使用一个已知的Seek职位URL进行测试
    test_url = "https://www.seek.com.au/job/test-job"  # 你需要替换为真实的URL
    
    print("开始测试Seek抓取...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 显示浏览器
        page = await browser.new_page()
        
        try:
            print(f"访问测试URL: {test_url}")
            await page.goto(test_url, timeout=30000)
            await page.wait_for_timeout(3000)
            
            # 获取页面标题
            title = await page.title()
            print(f"页面标题: {title}")
            
            # 尝试提取一些基本信息
            try:
                job_title = await page.query_selector('h1')
                if job_title:
                    print(f"职位标题: {await job_title.inner_text()}")
            except:
                print("无法提取职位标题")
            
            print("测试完成！如果能看到浏览器打开，说明Playwright工作正常")
            
        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_seek_single_job())