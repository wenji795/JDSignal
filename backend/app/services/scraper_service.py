"""自动抓取服务 - 支持增量抓取和去重"""
import asyncio
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from sqlmodel import Session, select
import httpx

# 添加项目根目录到Python路径
# __file__ 是 backend/app/services/scraper_service.py
# 需要到达 backend/ 目录
backend_dir = Path(__file__).parent.parent.parent  # services -> app -> backend
project_root = backend_dir.parent  # backend -> JDSignal
sys.path.insert(0, str(project_root))

from app.database import get_session
from app.models import Job

API_BASE_URL = "http://127.0.0.1:8000"

# 导入抓取函数（延迟导入，避免在模块加载时就失败）
scrape_jobs_module = None
scrape_seek_search = None
save_job_to_api = None
search_seek_jobs = None
scrape_seek_job = None

def _load_scrape_module():
    """延迟加载抓取模块"""
    global scrape_jobs_module, scrape_seek_search, save_job_to_api, search_seek_jobs, scrape_seek_job
    
    if scrape_jobs_module is not None:
        return  # 已经加载过了
    
    try:
        import importlib.util
        # scrape_jobs.py 在 backend/scripts/ 目录下
        scrape_jobs_path = backend_dir / "scripts" / "scrape_jobs.py"
        if not scrape_jobs_path.exists():
            raise FileNotFoundError(f"找不到抓取脚本: {scrape_jobs_path}")
        
        spec = importlib.util.spec_from_file_location("scrape_jobs", scrape_jobs_path)
        scrape_jobs_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scrape_jobs_module)
        scrape_seek_search = scrape_jobs_module.scrape_seek_search
        save_job_to_api = scrape_jobs_module.save_job_to_api
        search_seek_jobs = scrape_jobs_module.search_seek_jobs
        scrape_seek_job = scrape_jobs_module.scrape_seek_job
    except ImportError as e:
        if 'playwright' in str(e).lower():
            raise ImportError(
                "playwright模块未安装。请运行以下命令安装：\n"
                "  pip install playwright\n"
                "  playwright install firefox  # 或 playwright install chromium"
            ) from e
        raise

# 新西兰常见的IT职位关键词（扩展版）
NZ_IT_KEYWORDS = [
    # 通用开发职位
    "software engineer",
    "software developer",
    "developer",
    "programmer",
    "coder",
    "full stack developer",
    "fullstack developer",
    "backend developer",
    "frontend developer",
    "front end developer",
    
    # 特定技术栈
    "python developer",
    "javascript developer",
    "java developer",
    "react developer",
    "node.js developer",
    "nodejs developer",
    ".net developer",
    "c# developer",
    "csharp developer",
    "php developer",
    "ruby developer",
    "go developer",
    "golang developer",
    "rust developer",
    "swift developer",
    "kotlin developer",
    
    # 架构和高级职位
    "software architect",
    "solution architect",
    "technical architect",
    "senior developer",
    "lead developer",
    "principal developer",
    
    # DevOps和云
    "devops engineer",
    "devops",
    "sre engineer",
    "site reliability engineer",
    "cloud engineer",
    "aws engineer",
    "azure engineer",
    "kubernetes engineer",
    "docker engineer",
    
    # 测试和质量保证
    "test engineer",
    "qa engineer",
    "quality assurance",
    "automation tester",
    "test automation",
    "software test",
    "test analyst",
    "qa analyst",
    
    # 数据相关
    "data engineer",
    "data scientist",
    "data analyst",
    "data architect",
    "machine learning engineer",
    "ml engineer",
    "ai engineer",
    "analytics engineer",
    
    # 安全和网络
    "security engineer",
    "cybersecurity engineer",
    "network engineer",
    "infrastructure engineer",
    
    # 移动开发
    "mobile developer",
    "ios developer",
    "android developer",
    "react native developer",
    "flutter developer",
    
    # 管理和产品
    "product manager",
    "technical product manager",
    "scrum master",
    "agile coach",
    "engineering manager",
    "tech lead",
    
    # 其他IT职位
    "systems administrator",
    "sysadmin",
    "database administrator",
    "dba",
    "business analyst",
    "technical writer",
    "ui developer",
    "ux developer",
    "web developer",
]


def check_job_exists(url: str, session: Session) -> bool:
    """检查职位URL是否已存在（同步函数）"""
    if not url:
        return False
    existing = session.exec(select(Job).where(Job.url == url)).first()
    return existing is not None


def is_nz_location(location: Optional[str]) -> bool:
    """
    检查location是否在新西兰
    
    Args:
        location: 地点字符串
        
    Returns:
        True如果是新西兰，False否则
    """
    if not location:
        return False
    
    location_lower = location.lower()
    
    # 新西兰城市和地区关键词
    nz_keywords = [
        'new zealand', 'nz', 'auckland', 'wellington', 'christchurch', 
        'hamilton', 'dunedin', 'tauranga', 'lower hutt', 'palmerston north',
        'napier', 'rotorua', 'new plymouth', 'whangarei', 'invercargill',
        'nelson', 'hastings', 'gisborne', 'blenheim', 'timaru',
        'queenstown', 'wanganui', 'masterton', 'levin', 'otago',
        'canterbury', 'waikato', 'bay of plenty', 'manawatu', 'taranaki',
        'northland', 'southland', 'westland', 'marlborough', 'tasman'
    ]
    
    # 检查是否包含新西兰关键词
    for keyword in nz_keywords:
        if keyword in location_lower:
            return True
    
    # 排除澳大利亚的地点
    au_keywords = [
        'australia', 'au', 'sydney', 'melbourne', 'brisbane', 'perth',
        'adelaide', 'gold coast', 'newcastle', 'canberra', 'sunshine coast',
        'wollongong', 'hobart', 'geelong', 'townsville', 'cairns',
        'darwin', 'toowoomba', 'ballarat', 'bendigo', 'albury',
        'launceston', 'mackay', 'rockhampton', 'bunbury', 'bundaberg',
        'coffs harbour', 'wagga wagga', 'hervey bay', 'port macquarie',
        'shepparton', 'gladstone', 'mildura', 'tamworth', 'traralgon',
        'orange', 'bowral', 'geraldton', 'nowra', 'bathurst',
        'warrnambool', 'albany', 'kalgoorlie', 'broome', 'mount gambier',
        'queensland', 'qld', 'new south wales', 'nsw', 'victoria', 'vic',
        'western australia', 'wa', 'south australia', 'sa', 'tasmania', 'tas',
        'northern territory', 'nt', 'australian capital territory', 'act'
    ]
    
    # 如果包含澳大利亚关键词，返回False
    for keyword in au_keywords:
        if keyword in location_lower:
            return False
    
    # 排除美国的地点
    us_keywords = [
        'united states', 'usa', 'us', 'america', 'american',
        'california', 'ca', 'texas', 'tx', 'new york', 'ny', 'florida', 'fl',
        'san francisco', 'los angeles', 'san diego', 'chicago', 'houston', 'phoenix',
        'philadelphia', 'san antonio', 'dallas', 'austin', 'seattle', 'portland',
        'boston', 'detroit', 'nashville', 'las vegas', 'atlanta', 'miami',
        'remote us', 'remote usa', 'us remote', 'usa remote', 'united states remote'
    ]
    
    # 如果包含美国关键词，返回False
    for keyword in us_keywords:
        if keyword in location_lower:
            return False
    
    # 如果没有明确标识，默认返回False（保守策略）
    return False


async def save_job_to_api_incremental(job_data: Dict[str, Any], source: str, session: Session) -> bool:
    """保存职位到API（增量模式，检查URL去重）"""
    url = job_data.get('url', '')
    
    # 检查URL是否已存在
    if url and check_job_exists(url, session):
        print(f"⏭ 跳过已存在的职位: {url}")
        return False
    
    # 调用原有的保存函数
    return await save_job_to_api(job_data, source)


async def scrape_nz_jobs_incremental(
    max_per_keyword: int = 20, 
    headless: bool = True, 
    browser: str = "firefox"
):
    """
    增量抓取新西兰Seek上的IT职位
    
    Args:
        max_per_keyword: 每个关键词最多抓取多少个职位（默认20，增加覆盖率）
        headless: 是否使用无头模式（默认True，后台运行）
        browser: 使用的浏览器 (chromium, firefox, webkit)
    """
    # 延迟加载抓取模块
    _load_scrape_module()
    
    print("="*60)
    print("开始增量抓取新西兰Seek上的IT职位数据")
    print(f"关键词数量: {len(NZ_IT_KEYWORDS)}")
    print(f"每个关键词最多抓取: {max_per_keyword} 个职位")
    print("="*60)
    
    # 获取数据库session用于检查重复
    session_gen = get_session()
    session = next(session_gen)
    
    try:
        total_success = 0
        total_skipped = 0
        
        for i, keyword in enumerate(NZ_IT_KEYWORDS, 1):
            print(f"\n{'='*60}")
            print(f"处理关键词 {i}/{len(NZ_IT_KEYWORDS)}: {keyword}")
            print(f"{'='*60}")
            
            try:
                # 先搜索获取URL列表
                from playwright.async_api import async_playwright
                async with async_playwright() as p:
                    browser_instance = await p.firefox.launch(headless=headless) if browser == 'firefox' else await p.chromium.launch(headless=headless)
                    context = await browser_instance.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                    )
                    page = await context.new_page()
                    
                    # 搜索职位
                    job_urls = await search_seek_jobs(page, keyword, max_per_keyword, 'nz')
                    
                    if job_urls:
                        print(f"找到 {len(job_urls)} 个职位URL")
                        
                        # 检查每个URL是否已存在
                        new_urls = []
                        for url in job_urls:
                            if not check_job_exists(url, session):
                                new_urls.append(url)
                            else:
                                total_skipped += 1
                                print(f"⏭ 跳过已存在的职位: {url}")
                        
                        print(f"新职位: {len(new_urls)}, 已跳过: {len(job_urls) - len(new_urls)}")
                        
                        # 只抓取新职位
                        if new_urls:
                            for url in new_urls:
                                try:
                                    # 检查URL是否是澳大利亚的（seek.com.au）
                                    if 'seek.com.au' in url:
                                        print(f"⏭ 跳过澳大利亚职位: {url}")
                                        total_skipped += 1
                                        continue
                                    
                                    job_data = await scrape_seek_job(page, url)
                                    if job_data and job_data.get('jd_text'):
                                        # 验证location是否在新西兰
                                        location = job_data.get('location', '')
                                        if not is_nz_location(location):
                                            print(f"⏭ 跳过非新西兰职位: {location} - {url}")
                                            total_skipped += 1
                                            continue
                                        
                                        if await save_job_to_api(job_data, 'seek'):
                                            total_success += 1
                                        await asyncio.sleep(2)  # 避免请求过快
                                except Exception as e:
                                    print(f"✗ 抓取失败: {url} - {e}")
                    
                    await browser_instance.close()
                    
            except Exception as e:
                print(f"✗ 处理关键词失败: {keyword} - {e}")
                import traceback
                traceback.print_exc()
            
            # 每个关键词之间等待一段时间
            if i < len(NZ_IT_KEYWORDS):
                await asyncio.sleep(5)
        
        print(f"\n{'='*60}")
        print(f"增量抓取完成！")
        print(f"成功抓取: {total_success} 个新职位")
        print(f"跳过重复: {total_skipped} 个职位")
        print(f"{'='*60}")
        
    finally:
        session.close()


if __name__ == "__main__":
    # 测试用
    asyncio.run(scrape_nz_jobs_incremental(max_per_keyword=2, headless=True))
