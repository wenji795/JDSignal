"""
抓取新西兰Seek上的真实职位数据（近一个月）
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

# 导入抓取函数
import importlib.util
spec = importlib.util.spec_from_file_location("scrape_jobs", backend_dir / "scripts" / "scrape_jobs.py")
scrape_jobs_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scrape_jobs_module)
scrape_seek_search = scrape_jobs_module.scrape_seek_search

# 新西兰常见的IT职位关键词
NZ_IT_KEYWORDS = [
    "software engineer",
    "software developer",
    "full stack developer",
    "backend developer",
    "frontend developer",
    "devops engineer",
    "data engineer",
    "data scientist",
    "test engineer",
    "qa engineer",
    "product manager",
    "scrum master",
    "cloud engineer",
    "security engineer",
    "mobile developer",
    "python developer",
    "javascript developer",
    "java developer",
    "react developer",
    "node.js developer"
]

async def scrape_nz_jobs(max_per_keyword: int = 10, headless: bool = False, browser: str = "firefox"):
    """
    抓取新西兰Seek上的IT职位
    
    Args:
        max_per_keyword: 每个关键词最多抓取多少个职位（默认10）
        headless: 是否使用无头模式
        browser: 使用的浏览器 (chromium, firefox, webkit)
    """
    print("="*60)
    print("开始抓取新西兰Seek上的IT职位数据")
    print(f"关键词数量: {len(NZ_IT_KEYWORDS)}")
    print(f"每个关键词最多抓取: {max_per_keyword} 个职位")
    print(f"预计最多抓取: {len(NZ_IT_KEYWORDS) * max_per_keyword} 个职位")
    print("="*60)
    
    total_success = 0
    
    for i, keyword in enumerate(NZ_IT_KEYWORDS, 1):
        print(f"\n{'='*60}")
        print(f"处理关键词 {i}/{len(NZ_IT_KEYWORDS)}: {keyword}")
        print(f"{'='*60}")
        
        try:
            # 调用抓取函数
            await scrape_seek_search(
                keywords=keyword,
                max_results=max_per_keyword,
                headless=headless,
                browser_name=browser,
                country='nz'  # 新西兰
            )
            print(f"✓ 完成关键词: {keyword}")
        except Exception as e:
            print(f"✗ 处理关键词失败: {keyword} - {e}")
            import traceback
            traceback.print_exc()
        
        # 每个关键词之间等待一段时间，避免请求过快
        if i < len(NZ_IT_KEYWORDS):
            print(f"\n等待5秒后继续下一个关键词...")
            await asyncio.sleep(5)
    
    print(f"\n{'='*60}")
    print("所有关键词处理完成！")
    print(f"{'='*60}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='抓取新西兰Seek上的IT职位数据')
    parser.add_argument('--max-per-keyword', type=int, default=10, help='每个关键词最多抓取多少个职位（默认10）')
    parser.add_argument('--headless', action='store_true', help='使用无头模式（不显示浏览器）')
    parser.add_argument('--browser', type=str, choices=['chromium', 'firefox', 'webkit'], default='firefox', help='使用的浏览器引擎（默认firefox）')
    
    args = parser.parse_args()
    
    print("注意：此脚本会抓取新西兰Seek上的真实职位数据")
    print("请确保后端服务正在运行: cd backend && uvicorn app.main:app --reload")
    print()
    
    asyncio.run(scrape_nz_jobs(
        max_per_keyword=args.max_per_keyword,
        headless=args.headless,
        browser=args.browser
    ))


if __name__ == "__main__":
    main()
