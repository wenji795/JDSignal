"""使用Playwright抓取Seek和LinkedIn职位数据"""
import sys
import asyncio
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json
from urllib.parse import urlparse, parse_qs, quote_plus

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))

from playwright.async_api import async_playwright, Page, Browser
import httpx

API_BASE_URL = "http://127.0.0.1:8000"


def normalize_linkedin_url(url: str) -> str:
    """
    规范化LinkedIn URL
    如果是搜索页面，提取job ID并转换为职位页面URL
    """
    # 检查是否是搜索页面
    if '/jobs/search/' in url:
        # 从查询参数中提取currentJobId
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if 'currentJobId' in params:
            job_id = params['currentJobId'][0]
            return f"https://www.linkedin.com/jobs/view/{job_id}"
        else:
            # 尝试从URL路径中提取job ID
            match = re.search(r'/jobs/search/.*currentJobId=(\d+)', url)
            if match:
                job_id = match.group(1)
                return f"https://www.linkedin.com/jobs/view/{job_id}"
    
    # 如果不是搜索页面，直接返回
    return url


async def scrape_linkedin_job(page: Page, job_url: str) -> Optional[Dict[str, Any]]:
    """
    抓取LinkedIn职位页面
    
    注意：此脚本需要用户手动操作（登录等），仅用于辅助数据提取
    """
    try:
        print(f"正在访问: {job_url}")
        await page.goto(job_url, wait_until="networkidle", timeout=30000)
        
        # 等待页面加载
        await page.wait_for_timeout(2000)
        
        # 提取职位信息
        job_data = {}
        
        # 尝试提取标题
        title_selectors = [
            'h1.jobs-details-top-card__job-title',
            'h1[class*="job-title"]',
            'h1.text-heading-xlarge'
        ]
        for selector in title_selectors:
            try:
                title_elem = await page.query_selector(selector)
                if title_elem:
                    job_data['title'] = (await title_elem.inner_text()).strip()
                    break
            except:
                continue
        
        # 提取公司名称
        company_selectors = [
            'a[data-tracking-control-name="public_jobs_topcard-org-name"]',
            'a[class*="jobs-details-top-card__company-url"]',
            '.jobs-details-top-card__company-name'
        ]
        for selector in company_selectors:
            try:
                company_elem = await page.query_selector(selector)
                if company_elem:
                    job_data['company'] = (await company_elem.inner_text()).strip()
                    break
            except:
                continue
        
        # 提取地点
        location_selectors = [
            '.jobs-details-top-card__bullet',
            'span[class*="job-criteria__text"]',
            '.jobs-details-top-card__exact-location'
        ]
        for selector in location_selectors:
            try:
                location_elem = await page.query_selector(selector)
                if location_elem:
                    location_text = (await location_elem.inner_text()).strip()
                    if location_text and location_text != job_data.get('company', ''):
                        job_data['location'] = location_text
                        break
            except:
                continue
        
        # 提取职位描述
        description_selectors = [
            '.jobs-box__html-content',
            '.jobs-description-content__text',
            '#job-details',
            '[class*="jobs-description"]'
        ]
        for selector in description_selectors:
            try:
                desc_elem = await page.query_selector(selector)
                if desc_elem:
                    job_data['jd_text'] = (await desc_elem.inner_text()).strip()
                    if len(job_data['jd_text']) > 100:  # 确保有足够内容
                        break
            except:
                continue
        
        # 提取页面标题作为备用
        if 'title' not in job_data:
            page_title = await page.title()
            if ' at ' in page_title:
                parts = page_title.split(' at ')
                job_data['title'] = parts[0].strip()
                if 'company' not in job_data and len(parts) > 1:
                    job_data['company'] = parts[1].split(' | ')[0].strip()
        
        if not job_data.get('jd_text'):
            # 尝试提取整个页面内容
            body_elem = await page.query_selector('body')
            if body_elem:
                job_data['jd_text'] = (await body_elem.inner_text())[:5000]  # 限制长度
        
        job_data['url'] = job_url
        job_data['page_title'] = await page.title()
        
        return job_data if job_data.get('jd_text') else None
        
    except Exception as e:
        print(f"抓取LinkedIn职位失败: {e}")
        return None


async def scrape_seek_job(page: Page, job_url: str) -> Optional[Dict[str, Any]]:
    """
    抓取Seek职位页面
    """
    try:
        print(f"正在访问: {job_url}")
        await page.goto(job_url, wait_until="networkidle", timeout=30000)
        
        # 等待页面加载
        await page.wait_for_timeout(2000)
        
        job_data = {}
        
        # 提取标题
        title_selectors = [
            'h1[data-automation="job-detail-title"]',
            'h1.jobTitle',
            'h1'
        ]
        for selector in title_selectors:
            try:
                title_elem = await page.query_selector(selector)
                if title_elem:
                    job_data['title'] = (await title_elem.inner_text()).strip()
                    break
            except:
                continue
        
        # 提取公司名称
        company_selectors = [
            'a[data-automation="job-detail-company-name"]',
            '[data-automation="jobHeaderCompanyName"]',
            'a[href*="/companies/"]'
        ]
        for selector in company_selectors:
            try:
                company_elem = await page.query_selector(selector)
                if company_elem:
                    job_data['company'] = (await company_elem.inner_text()).strip()
                    break
            except:
                continue
        
        # 提取地点
        location_selectors = [
            'span[data-automation="job-detail-location"]',
            '[data-automation="jobHeaderLocation"]',
            '.location'
        ]
        for selector in location_selectors:
            try:
                location_elem = await page.query_selector(selector)
                if location_elem:
                    job_data['location'] = (await location_elem.inner_text()).strip()
                    break
            except:
                continue
        
        # 提取职位描述
        description_selectors = [
            '[data-automation="jobDescription"]',
            '.templatetext',
            '#jobDescription'
        ]
        for selector in description_selectors:
            try:
                desc_elem = await page.query_selector(selector)
                if desc_elem:
                    job_data['jd_text'] = (await desc_elem.inner_text()).strip()
                    if len(job_data['jd_text']) > 100:
                        break
            except:
                continue
        
        # 提取页面标题作为备用
        if 'title' not in job_data:
            page_title = await page.title()
            job_data['title'] = page_title.split(' | ')[0].strip()
        
        if not job_data.get('jd_text'):
            # 尝试提取整个页面内容
            body_elem = await page.query_selector('body')
            if body_elem:
                job_data['jd_text'] = (await body_elem.inner_text())[:5000]
        
        job_data['url'] = job_url
        job_data['page_title'] = await page.title()
        
        return job_data if job_data.get('jd_text') else None
        
    except Exception as e:
        print(f"抓取Seek职位失败: {e}")
        return None


async def check_api_connection() -> bool:
    """检查后端API是否可用"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/", timeout=5.0)
            return response.status_code == 200
    except:
        return False


async def save_job_to_api(job_data: Dict[str, Any], source: str) -> bool:
    """保存职位到API"""
    try:
        # 确定来源
        if 'linkedin.com' in job_data.get('url', ''):
            source = 'linkedin'
        elif 'seek.com' in job_data.get('url', '') or 'seek.com.au' in job_data.get('url', ''):
            source = 'seek'
        
        # 准备数据
        payload = {
            "source": source,
            "url": job_data.get('url', ''),
            "page_title": job_data.get('page_title', job_data.get('title', '')),
            "company_guess": job_data.get('company', 'Unknown'),
            "location_guess": job_data.get('location'),
            "extracted_text": job_data.get('jd_text', ''),
        }
        
        # 调用capture端点
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/capture",
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 201:
                result = response.json()
                print(f"✓ 成功保存: {job_data.get('title', 'Unknown')} at {job_data.get('company', 'Unknown')}")
                print(f"  职位ID: {result.get('job_id')}")
                print(f"  提取了 {len(result.get('top_keywords', []))} 个关键词")
                return True
            else:
                print(f"✗ 保存失败: {response.status_code} - {response.text}")
                return False
                
    except httpx.ConnectError:
        print(f"✗ 无法连接到后端API ({API_BASE_URL})，请确保后端服务正在运行")
        return False
    except Exception as e:
        print(f"✗ 保存到API失败: {e}")
        return False


async def search_seek_jobs(page: Page, keywords: str, max_results: int = 20, country: str = 'nz') -> list[str]:
    """
    在Seek上搜索职位，返回职位URL列表
    
    Args:
        page: Playwright页面对象
        keywords: 搜索关键词（如 "software test"）
        max_results: 最大返回结果数（默认20）
        country: 国家代码，'nz' 表示新西兰，'au' 表示澳大利亚（默认'nz'）
    
    Returns:
        职位URL列表
    """
    try:
        # 根据国家选择域名
        domain = 'seek.co.nz' if country == 'nz' else 'seek.com.au'
        # 构建搜索URL
        search_url = f"https://www.{domain}/jobs?keywords={quote_plus(keywords)}"
        print(f"正在搜索Seek ({country.upper()}): {keywords}")
        print(f"搜索URL: {search_url}")
        
        await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)  # 等待搜索结果加载（增加等待时间）
        
        job_urls = []
        
        # 查找职位链接 - Seek的职位链接通常在a标签中，包含/job/
        link_selectors = [
            'a[data-automation="jobTitle"]',
            'a[href*="/job/"]',
            'article a[href*="/job/"]',
            '[data-automation="jobTitle"]'
        ]
        
        for selector in link_selectors:
            try:
                # 尝试查找元素（不强制等待，避免超时导致浏览器关闭）
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                except:
                    pass  # 如果超时，继续尝试query_selector_all
                    
                links = await page.query_selector_all(selector)
                print(f"使用选择器 {selector} 找到 {len(links)} 个链接")
                
                for link in links:
                    try:
                        href = await link.get_attribute('href')
                        if href and '/job/' in href:
                            # 确保是完整URL
                            if href.startswith('http'):
                                full_url = href
                            else:
                                # 根据当前域名构建完整URL
                                domain = 'seek.co.nz' if country == 'nz' else 'seek.com.au'
                                full_url = f"https://www.{domain}{href}"
                            
                            # 清理URL（移除查询参数和锚点）
                            full_url = full_url.split('?')[0].split('#')[0]
                            
                            if full_url not in job_urls:
                                job_urls.append(full_url)
                                if len(job_urls) >= max_results:
                                    break
                    except Exception as e:
                        continue
                
                if job_urls:
                    break
            except Exception as e:
                print(f"尝试选择器 {selector} 失败: {e}")
                continue
        
        # 如果上面没找到，尝试从页面源码中提取
        if not job_urls:
            print("尝试从页面源码中提取链接...")
            try:
                content = await page.content()
                # 查找所有 /job/ 开头的链接
                matches = re.findall(r'href="(/job/\d+[^"]*)"', content)
                domain = 'seek.co.nz' if country == 'nz' else 'seek.com.au'
                for match in matches:
                    full_url = f"https://www.{domain}{match.split('?')[0].split('#')[0]}"
                    if full_url not in job_urls:
                        job_urls.append(full_url)
                        if len(job_urls) >= max_results:
                            break
            except Exception as e:
                print(f"从源码提取链接失败: {e}")
        
        print(f"找到 {len(job_urls)} 个职位链接")
        return job_urls[:max_results]
        
    except Exception as e:
        print(f"搜索Seek职位失败: {e}")
        import traceback
        traceback.print_exc()
        return []


async def scrape_seek_search(keywords: str, max_results: int = 20, headless: bool = False, browser_name: str = "chromium", country: str = 'nz'):
    """
    搜索并抓取Seek上的职位
    
    Args:
        keywords: 搜索关键词（如 "software test"）
        max_results: 最多抓取多少个职位（默认20）
        headless: 是否使用无头模式
        browser_name: 使用的浏览器名称 (chromium, firefox, webkit)
        country: 国家代码，'nz' 表示新西兰，'au' 表示澳大利亚（默认'nz'）
    """
    # 检查后端API连接
    print("检查后端API连接...")
    if not await check_api_connection():
        print(f"✗ 错误: 无法连接到后端API ({API_BASE_URL})")
        print("请确保后端服务正在运行:")
        print("  cd backend")
        print("  uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
        return
    
    print("✓ 后端API连接正常")
    print("正在启动浏览器...")
    
    async with async_playwright() as p:
        try:
            # 根据选择的浏览器类型启动
            print(f"启动{browser_name}浏览器...")
            if browser_name == 'firefox':
                browser = await p.firefox.launch(headless=headless)
            elif browser_name == 'webkit':
                browser = await p.webkit.launch(headless=headless)
            else:  # chromium
                # 添加更多启动参数以避免崩溃
                browser = await p.chromium.launch(
                    headless=headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process',
                    ]
                )
            print("✓ 浏览器启动成功")
            
            print("创建浏览器上下文...")
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            print("✓ 上下文创建成功")
            
            print("创建新页面...")
            # 添加错误处理，如果创建页面失败，尝试重新创建
            max_retries = 3
            page = None
            for attempt in range(max_retries):
                try:
                    page = await context.new_page()
                    print("✓ 页面创建成功")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"页面创建失败，重试 {attempt + 1}/{max_retries}...")
                        await asyncio.sleep(1)
                    else:
                        raise
            
            if not page:
                raise Exception("无法创建页面")
            
            # 1. 搜索职位，获取URL列表
            print(f"\n开始搜索职位: {keywords} (国家: {country.upper()})")
            job_urls = await search_seek_jobs(page, keywords, max_results, country)
            
            if not job_urls:
                print("未找到任何职位，请检查搜索关键词或网站结构是否变化")
                await browser.close()
                return
            
            print(f"\n{'='*60}")
            print(f"找到 {len(job_urls)} 个职位，开始抓取...")
            print(f"{'='*60}\n")
            
            success_count = 0
            
            # 2. 逐个抓取职位详情
            for i, url in enumerate(job_urls, 1):
                print(f"\n{'='*60}")
                print(f"处理职位 {i}/{len(job_urls)}: {url}")
                print(f"{'='*60}")
                
                try:
                    job_data = await scrape_seek_job(page, url)
                    
                    if job_data and job_data.get('jd_text'):
                        # 保存到API
                        if await save_job_to_api(job_data, 'seek'):
                            success_count += 1
                            print(f"✓ 成功保存职位: {job_data.get('title', 'N/A')}")
                        else:
                            print(f"✗ 保存到API失败")
                    else:
                        print(f"✗ 未能提取职位数据")
                        
                except Exception as e:
                    print(f"✗ 处理职位失败: {e}")
                    import traceback
                    traceback.print_exc()
                
                # 等待一段时间再处理下一个（避免请求过快）
                if i < len(job_urls):
                    await asyncio.sleep(2)
            
            print(f"\n{'='*60}")
            print(f"完成！成功保存 {success_count}/{len(job_urls)} 个职位")
            print(f"{'='*60}")
            
            await browser.close()
            
        except Exception as e:
            print(f"✗ 抓取过程出错: {e}")
            import traceback
            traceback.print_exc()
            try:
                if 'browser' in locals():
                    await browser.close()
            except:
                pass


async def scrape_jobs_from_urls(urls: list[str], headless: bool = False):
    """
    从URL列表抓取职位
    
    Args:
        urls: 职位URL列表
        headless: 是否使用无头模式（False会显示浏览器窗口）
    """
    async with async_playwright() as p:
        # 启动浏览器（显示窗口，方便查看）
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        success_count = 0
        
        for url in urls:
            print(f"\n{'='*60}")
            print(f"处理URL {urls.index(url) + 1}/{len(urls)}: {url}")
            print(f"{'='*60}")
            
            try:
                # 规范化LinkedIn URL（如果是搜索页面，转换为职位页面）
                if 'linkedin.com' in url:
                    normalized_url = normalize_linkedin_url(url)
                    if normalized_url != url:
                        print(f"检测到搜索页面URL，已转换为职位页面: {normalized_url}")
                    job_data = await scrape_linkedin_job(page, normalized_url)
                elif 'seek.com' in url or 'seek.com.au' in url:
                    job_data = await scrape_seek_job(page, url)
                else:
                    print(f"未知的URL类型，跳过: {url}")
                    continue
                
                if job_data and job_data.get('jd_text'):
                    # 保存到API
                    if await save_job_to_api(job_data, 'other'):
                        success_count += 1
                else:
                    print(f"✗ 未能提取职位数据，可能需要手动登录或页面结构已变化")
                    
            except Exception as e:
                print(f"✗ 处理URL失败: {e}")
            
            # 等待一段时间再处理下一个
            if urls.index(url) < len(urls) - 1:
                await asyncio.sleep(2)
        
        await browser.close()
        print(f"\n{'='*60}")
        print(f"完成！成功保存 {success_count}/{len(urls)} 个职位")
        print(f"{'='*60}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='使用Playwright抓取Seek和LinkedIn职位')
    parser.add_argument('urls', nargs='*', help='职位URL列表（可选）')
    parser.add_argument('--headless', action='store_true', help='使用无头模式（不显示浏览器）')
    parser.add_argument('--file', type=str, help='从文件读取URL列表（每行一个URL）')
    # 新增搜索选项
    parser.add_argument('--search-seek', type=str, help='在Seek上搜索关键词并抓取（如：--search-seek "software test"）')
    parser.add_argument('--max-results', type=int, default=20, help='搜索结果最大数量（默认20）')
    parser.add_argument('--browser', type=str, choices=['chromium', 'firefox', 'webkit'], default='chromium', help='使用的浏览器引擎（默认chromium）')
    parser.add_argument('--country', type=str, choices=['nz', 'au'], default='nz', help='国家代码：nz=新西兰，au=澳大利亚（默认nz）')
    
    args = parser.parse_args()
    
    # 如果使用搜索模式
    if args.search_seek:
        print(f"使用Seek搜索模式，关键词: {args.search_seek}")
        print(f"最多抓取 {args.max_results} 个职位")
        print(f"使用浏览器: {args.browser}")
        print(f"国家: {args.country.upper()}")
        asyncio.run(scrape_seek_search(args.search_seek, args.max_results, args.headless, args.browser, args.country))
        return
    
    # 原有的URL模式
    urls = list(args.urls) if args.urls else []
    
    # 如果指定了文件，从文件读取URL
    if args.file:
        with open(args.file, 'r') as f:
            urls.extend([line.strip() for line in f if line.strip() and not line.strip().startswith('#')])
    
    if not urls:
        print("错误: 请提供至少一个URL、使用--file参数，或使用--search-seek进行搜索")
        return
    
    print(f"准备抓取 {len(urls)} 个职位...")
    print(f"注意: 如果网站需要登录，请在浏览器窗口中手动登录")
    
    asyncio.run(scrape_jobs_from_urls(urls, headless=args.headless))


if __name__ == "__main__":
    main()