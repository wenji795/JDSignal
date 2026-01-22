"""重新抓取已有职位的posted_date - 访问Seek页面提取"""
import sys
import asyncio
from pathlib import Path
from typing import Optional

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select
from app.database import engine
from app.models import Job
from playwright.async_api import async_playwright
from scripts.scrape_jobs import parse_posted_date, extract_posted_date_from_text
from app.services.ai_builder_client import get_ai_builder_client


async def re_scrape_posted_date(job: Job, page) -> Optional[str]:
    """重新抓取单个职位的posted_date"""
    if not job.url or 'seek.co.nz' not in job.url:
        return None
    
    try:
        print(f"正在访问: {job.url}")
        await page.goto(job.url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        
        # 使用与scrape_jobs.py相同的提取逻辑
        posted_date = None
        
        # 方法1: 查找Seek特定的data-automation属性
        try:
            date_selectors = [
                'span[data-automation="job-detail-date"]',
                '[data-automation="jobHeaderDate"]',
                '[data-automation*="date"]',
                '[data-automation*="Date"]',
                '[data-automation*="posted"]',
                '[data-automation*="Posted"]',
                'time[datetime]',
                '.posted-date',
                '.date-posted',
                '[class*="posted"]',
                '[class*="date"]',
                '[class*="Posted"]',
                '[class*="Date"]'
            ]
            
            for selector in date_selectors:
                try:
                    date_elem = await page.query_selector(selector)
                    if date_elem:
                        # 尝试从datetime属性获取
                        datetime_attr = await date_elem.get_attribute('datetime')
                        if datetime_attr:
                            try:
                                from dateutil import parser as date_parser
                                posted_date = date_parser.parse(datetime_attr)
                                print(f"  ✓ 方法1a-从datetime属性提取: {posted_date.strftime('%Y-%m-%d')}")
                                return posted_date.isoformat()
                            except:
                                pass
                        
                        # 尝试从文本内容解析
                        date_text = (await date_elem.inner_text()).strip()
                        if date_text:
                            posted_date = parse_posted_date(date_text)
                            if posted_date:
                                print(f"  ✓ 方法1b-从元素文本提取: {posted_date.strftime('%Y-%m-%d')} (原文: {date_text})")
                                return posted_date.isoformat()
                        
                        # 尝试从title属性获取
                        title_attr = await date_elem.get_attribute('title')
                        if title_attr:
                            posted_date = parse_posted_date(title_attr)
                            if posted_date:
                                print(f"  ✓ 方法1c-从title属性提取: {posted_date.strftime('%Y-%m-%d')} (原文: {title_attr})")
                                return posted_date.isoformat()
                except:
                    continue
        except Exception as e:
            print(f"    方法1失败: {e}")
        
        # 方法2: 使用JavaScript查找包含"Posted"的元素（更全面的搜索）
        if not posted_date:
            try:
                posted_date_text = await page.evaluate(r'''() => {
                    // 方法2a: 使用TreeWalker查找文本节点
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    
                    let node;
                    while (node = walker.nextNode()) {
                        const text = node.textContent.trim();
                        // 匹配 "Posted Xd ago" 或 "Posted X days ago" 等格式
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
                    
                    // 方法2b: 查找所有包含"Posted"的元素（更宽松的匹配）
                    const allElements = document.querySelectorAll('*');
                    for (let el of allElements) {
                        const text = el.textContent || el.innerText || '';
                        // 匹配各种格式：Posted Xd ago, Posted X days ago, Posted Xd, etc.
                        if (/posted\s+\d+\s*[dwmyh]/i.test(text) || /posted\s+\d+\s*(?:day|days|week|weeks|month|months)/i.test(text)) {
                            // 尝试提取完整的"Posted Xd ago"文本
                            const match = text.match(/posted\s+\d+\s*[dwmyh]\s*ago/i) || 
                                         text.match(/posted\s+\d+\s*(?:day|days|week|weeks|month|months)\s*ago/i) ||
                                         text.match(/posted\s+\d+\s*[dwmyh]/i);
                            if (match) {
                                return match[0];
                            }
                            // 如果元素文本较短，直接返回
                            if (text.length < 100 && /posted\s+\d+/i.test(text)) {
                                return text;
                            }
                        }
                    }
                    
                    // 方法2c: 查找包含"ago"的元素（可能"Posted"和"ago"在不同元素中）
                    const agoElements = document.querySelectorAll('*');
                    for (let el of agoElements) {
                        const text = el.textContent || el.innerText || '';
                        if (/\d+\s*[dwmyh]\s*ago/i.test(text) || /\d+\s*(?:day|days|week|weeks|month|months)\s*ago/i.test(text)) {
                            // 检查父元素是否包含"Posted"
                            let parent = el.parentElement;
                            let checked = 0;
                            while (parent && parent !== document.body && checked < 5) {
                                const parentText = parent.textContent || parent.innerText || '';
                                if (/posted/i.test(parentText)) {
                                    const fullText = parentText.trim();
                                    const match = fullText.match(/posted\s+\d+\s*[dwmyh]\s*ago/i) ||
                                                 fullText.match(/posted\s+\d+\s*(?:day|days|week|weeks|month|months)\s*ago/i);
                                    if (match) {
                                        return match[0];
                                    }
                                }
                                parent = parent.parentElement;
                                checked++;
                            }
                        }
                    }
                    
                    return null;
                }''')
                
                if posted_date_text:
                    from datetime import datetime
                    posted_date = parse_posted_date(posted_date_text)
                    if posted_date:
                        print(f"  ✓ 方法2-从JavaScript提取: {posted_date.strftime('%Y-%m-%d')} (原文: {posted_date_text})")
                        return posted_date.isoformat()
            except Exception as e:
                print(f"    方法2失败: {e}")
        
        # 方法3: 从整个页面文本中提取
        if not posted_date:
            try:
                page_text = await page.inner_text('body')
                posted_date = extract_posted_date_from_text(page_text)
                if posted_date:
                    print(f"  ✓ 方法3-从页面文本提取: {posted_date.strftime('%Y-%m-%d')}")
                    return posted_date.isoformat()
            except Exception as e:
                print(f"    方法3失败: {e}")
        
        # 方法4: 尝试从页面HTML中查找（最后尝试）
        if not posted_date:
            try:
                html_content = await page.content()
                # 查找包含"Posted"的HTML片段
                import re
                posted_patterns = [
                    r'posted\s+(\d+\s*[dwmyh])\s*ago',
                    r'posted\s+(\d+\s*(?:day|days|week|weeks|month|months|hour|hours))\s*ago',
                ]
                
                for pattern in posted_patterns:
                    matches = re.finditer(pattern, html_content, re.IGNORECASE)
                    for match in matches:
                        try:
                            posted_text = match.group(0)
                            posted_date = parse_posted_date(posted_text)
                            if posted_date:
                                print(f"  ✓ 方法4-从HTML提取: {posted_date.strftime('%Y-%m-%d')} (原文: {posted_text})")
                                return posted_date.isoformat()
                        except:
                            continue
            except Exception as e:
                print(f"    方法4失败: {e}")
        
        # 方法5: 使用AI Builder API提取（最后尝试）
        if not posted_date:
            try:
                client = get_ai_builder_client()
                if client:
                    # 尝试获取页面关键区域的文本（标题区域、元数据区域等）
                    # 先尝试获取页面头部和关键区域的文本
                    try:
                        # 获取页面标题区域
                        header_text = await page.evaluate('''() => {
                            const header = document.querySelector('header') || 
                                         document.querySelector('[data-automation="jobHeader"]') ||
                                         document.querySelector('.job-header') ||
                                         document.body;
                            return header ? header.innerText || header.textContent : '';
                        }''')
                        
                        # 如果header_text太长，只取前3000字符
                        if len(header_text) > 3000:
                            header_text = header_text[:3000]
                        
                        # 如果header_text为空或太短，使用body的前5000字符
                        if len(header_text) < 100:
                            page_text = await page.inner_text('body')
                            header_text = page_text[:5000]
                    except:
                        # 如果获取失败，使用body文本
                        page_text = await page.inner_text('body')
                        header_text = page_text[:5000]
                    
                    # 构建AI提示
                    prompt = f"""请从以下网页内容中提取职位发布日期(posted_date)。

这是一个Seek.co.nz职位页面。请仔细查找包含"Posted"、"posted"、"Date posted"等关键词的文本，以及任何表示发布日期的信息。

网页内容：
{header_text}

请查找：
1. 包含"Posted Xd ago"、"Posted X days ago"等格式的文本
2. 包含"Date posted"、"Posted on"等关键词的文本
3. 任何表示相对时间的文本（如"2 weeks ago"、"1 month ago"等）
4. 任何ISO格式的日期（YYYY-MM-DD）

如果找到发布日期，请以以下格式之一返回：
- 相对时间格式：如"13d ago"、"2 weeks ago"（优先使用此格式，因为Seek通常使用相对时间）
- ISO格式日期：YYYY-MM-DD（如果找到具体日期）
- 如果找不到，返回"NOT_FOUND"

只返回日期信息，不要返回其他内容或解释。"""
                    
                    response = await client.chat_completion(
                        messages=[
                            {"role": "system", "content": "你是一个专业的网页数据提取助手，擅长从网页内容中提取日期信息。你特别擅长识别Seek.co.nz网站上的职位发布日期格式。"},
                            {"role": "user", "content": prompt}
                        ],
                        model="supermind-agent-v1",
                        temperature=0.1,
                        max_tokens=150
                    )
                    
                    # 提取AI返回的内容
                    ai_response = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    
                    # 清理AI响应（移除可能的引号、标点等）
                    ai_response = ai_response.strip('"\'.,;:!?')
                    
                    if ai_response and ai_response.upper() != "NOT_FOUND":
                        # 尝试解析AI返回的日期
                        posted_date = parse_posted_date(ai_response)
                        if posted_date:
                            print(f"  ✓ 方法5-AI提取: {posted_date.strftime('%Y-%m-%d')} (AI返回: {ai_response})")
                            return posted_date.isoformat()
                        else:
                            # 如果直接解析失败，尝试从文本中提取
                            posted_date = extract_posted_date_from_text(ai_response)
                            if posted_date:
                                print(f"  ✓ 方法5-AI提取(二次解析): {posted_date.strftime('%Y-%m-%d')} (AI返回: {ai_response})")
                                return posted_date.isoformat()
                            else:
                                print(f"    方法5-AI返回了无法解析的内容: {ai_response}")
                else:
                    print(f"    方法5跳过: AI Builder客户端未配置（请设置AI_BUILDER_TOKEN环境变量）")
            except Exception as e:
                print(f"    方法5失败: {e}")
                import traceback
                traceback.print_exc()
        
        if not posted_date:
            print(f"  ⚠ 未能提取posted_date（已尝试所有方法，包括AI）")
            # 打印页面标题用于调试
            try:
                page_title = await page.title()
                print(f"    页面标题: {page_title[:100]}")
            except:
                pass
            return None
            
    except Exception as e:
        print(f"  ✗ 访问页面失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def re_scrape_all_posted_dates(limit: Optional[int] = None, source: Optional[str] = None):
    """重新抓取所有缺少posted_date的职位"""
    with Session(engine) as session:
        # 查询缺少posted_date且有URL的职位
        statement = select(Job).where(
            Job.posted_date.is_(None),
            Job.url.isnot(None)
        )
        
        if source:
            statement = statement.where(Job.source == source)
        
        if limit:
            statement = statement.limit(limit)
        
        jobs = session.exec(statement).all()
        total_jobs = len(jobs)
        
        if total_jobs == 0:
            print("没有需要更新posted_date的职位")
            return
        
        print(f"找到 {total_jobs} 个需要更新posted_date的职位（有URL）")
        print("=" * 60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            success_count = 0
            fail_count = 0
            
            for i, job in enumerate(jobs, 1):
                print(f"\n[{i}/{total_jobs}] {job.title[:60]}...")
                posted_date_str = await re_scrape_posted_date(job, page)
                
                if posted_date_str:
                    try:
                        from datetime import datetime
                        posted_date = datetime.fromisoformat(posted_date_str.replace('Z', '+00:00'))
                        job.posted_date = posted_date
                        session.add(job)
                        session.commit()
                        success_count += 1
                    except Exception as e:
                        print(f"  ✗ 保存失败: {e}")
                        session.rollback()
                        fail_count += 1
                else:
                    fail_count += 1
                
                # 每10个职位暂停一下
                if i % 10 == 0:
                    print(f"\n已处理 {i}/{total_jobs} 个职位，暂停3秒...")
                    await asyncio.sleep(3)
            
            await browser.close()
        
        print("\n" + "=" * 60)
        print(f"更新完成！")
        print(f"成功: {success_count} 个")
        print(f"失败: {fail_count} 个")
        print(f"总计: {total_jobs} 个")
        print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='重新抓取职位的posted_date')
    parser.add_argument('--limit', type=int, help='限制更新的数量')
    parser.add_argument('--source', type=str, help='只更新指定来源的职位（如：seek）')
    
    args = parser.parse_args()
    
    asyncio.run(re_scrape_all_posted_dates(limit=args.limit, source=args.source))
