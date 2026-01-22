"""批量更新posted_date - 快速版本，使用多线程"""
import sys
import asyncio
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
import time

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine
from app.database import engine
from app.models import Job
from scripts.scrape_jobs import parse_posted_date, extract_posted_date_from_text


def get_job_urls_batch(session: Session, limit: int = 100, offset: int = 0):
    """获取一批需要更新的职位URL"""
    statement = select(Job).where(
        Job.posted_date.is_(None),
        Job.url.isnot(None)
    ).limit(limit).offset(offset)
    
    jobs = session.exec(statement).all()
    return [(job.id, job.url) for job in jobs if job.url and 'seek.co.nz' in job.url]


async def scrape_posted_date_from_url(url: str, page) -> Optional[str]:
    """从URL抓取posted_date"""
    try:
        await page.goto(url, wait_until="networkidle", timeout=20000)
        await page.wait_for_timeout(1500)
        
        # 使用JavaScript查找
        posted_date_text = await page.evaluate(r'''() => {
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );
            
            let node;
            while (node = walker.nextNode()) {
                const text = node.textContent.trim();
                if (/posted\s+\d+\s*[dwmyh]\s*ago/i.test(text)) {
                    let parent = node.parentElement;
                    while (parent && parent !== document.body) {
                        const parentText = parent.textContent.trim();
                        const match = parentText.match(/posted\s+(\d+\s*[dwmyh])\s*ago/i);
                        if (match) {
                            return parentText;
                        }
                        parent = parent.parentElement;
                    }
                    return text;
                }
            }
            return null;
        }''')
        
        if posted_date_text:
            posted_date = parse_posted_date(posted_date_text)
            if posted_date:
                return posted_date.isoformat()
        
        # 备用方法：从页面文本提取
        page_text = await page.inner_text('body')
        posted_date = extract_posted_date_from_text(page_text)
        if posted_date:
            return posted_date.isoformat()
            
    except Exception as e:
        print(f"  ✗ 抓取失败 {url}: {e}")
    
    return None


async def batch_update_posted_dates(limit: Optional[int] = None, batch_size: int = 50):
    """批量更新posted_date"""
    from playwright.async_api import async_playwright
    
    with Session(engine) as session:
        total_needed = len(session.exec(select(Job).where(
            Job.posted_date.is_(None),
            Job.url.isnot(None)
        )).all())
        
        if limit:
            total_needed = min(total_needed, limit)
        
        print(f"需要更新 {total_needed} 个职位")
        print("=" * 60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            
            success_count = 0
            fail_count = 0
            offset = 0
            
            while offset < total_needed:
                # 获取一批URL
                job_urls = get_job_urls_batch(session, batch_size, offset)
                
                if not job_urls:
                    break
                
                print(f"\n处理批次 {offset//batch_size + 1} ({len(job_urls)} 个职位)...")
                
                # 为每个URL创建页面并抓取
                tasks = []
                for job_id, url in job_urls:
                    page = await context.new_page()
                    task = scrape_posted_date_from_url(url, page)
                    tasks.append((job_id, url, task, page))
                
                # 并发执行
                for job_id, url, task, page in tasks:
                    try:
                        posted_date_str = await asyncio.wait_for(task, timeout=25.0)
                        await page.close()
                        
                        if posted_date_str:
                            # 更新数据库
                            with Session(engine) as update_session:
                                job = update_session.get(Job, job_id)
                                if job:
                                    from datetime import datetime
                                    posted_date = datetime.fromisoformat(posted_date_str.replace('Z', '+00:00'))
                                    job.posted_date = posted_date
                                    update_session.add(job)
                                    update_session.commit()
                                    success_count += 1
                                    print(f"  ✓ [{success_count}] {job.title[:50]}... -> {posted_date.strftime('%Y-%m-%d')}")
                                else:
                                    fail_count += 1
                        else:
                            fail_count += 1
                            print(f"  ✗ 未提取到日期: {url[:60]}...")
                    except asyncio.TimeoutError:
                        await page.close()
                        fail_count += 1
                        print(f"  ✗ 超时: {url[:60]}...")
                    except Exception as e:
                        try:
                            await page.close()
                        except:
                            pass
                        fail_count += 1
                        print(f"  ✗ 错误: {e}")
                
                offset += batch_size
                
                # 批次间暂停
                if offset < total_needed:
                    print(f"\n已处理 {min(offset, total_needed)}/{total_needed}，暂停2秒...")
                    await asyncio.sleep(2)
            
            await browser.close()
        
        print("\n" + "=" * 60)
        print(f"更新完成！")
        print(f"成功: {success_count} 个")
        print(f"失败: {fail_count} 个")
        print(f"总计: {success_count + fail_count} 个")
        print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='批量更新职位的posted_date')
    parser.add_argument('--limit', type=int, help='限制更新的数量')
    parser.add_argument('--batch-size', type=int, default=10, help='每批处理的数量（默认10）')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("批量更新 posted_date")
    print("=" * 60)
    print(f"批次大小: {args.batch_size}")
    if args.limit:
        print(f"限制数量: {args.limit}")
    print()
    
    asyncio.run(batch_update_posted_dates(limit=args.limit, batch_size=args.batch_size))
