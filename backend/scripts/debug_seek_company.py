"""
调试脚本：检查 Seek 页面结构，找出公司名称的正确选择器
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))

from playwright.async_api import async_playwright


async def debug_seek_page(job_url: str):
    """调试 Seek 页面，找出公司名称的位置"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 使用有头模式，方便查看
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        print(f"正在访问: {job_url}")
        await page.goto(job_url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)  # 等待页面加载
        
        # 保存页面截图
        await page.screenshot(path="seek_page_debug.png", full_page=True)
        print("✓ 页面截图已保存到: seek_page_debug.png")
        
        # 获取页面标题
        page_title = await page.title()
        print(f"\n页面标题: {page_title}")
        
        # 尝试所有可能的选择器
        selectors_to_test = [
            'a[data-automation="job-detail-company-name"]',
            '[data-automation="jobHeaderCompanyName"]',
            '[data-automation="job-detail-company"]',
            'a[href*="/companies/"]',
            'a[href*="/company/"]',
            '.job-detail-company-name',
            'span[data-automation="job-detail-company-name"]',
            '[class*="company-name"]',
            '[class*="companyName"]',
            'a[class*="company"]',
        ]
        
        print("\n=== 测试选择器 ===")
        found_elements = []
        for selector in selectors_to_test:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"\n✓ 找到 {len(elements)} 个元素: {selector}")
                    for i, elem in enumerate(elements[:3]):  # 只显示前3个
                        try:
                            text = await elem.inner_text()
                            href = await elem.get_attribute('href')
                            print(f"  元素 {i+1}:")
                            print(f"    文本: {text[:100] if text else 'None'}")
                            print(f"    href: {href}")
                            found_elements.append({
                                'selector': selector,
                                'text': text,
                                'href': href
                            })
                        except:
                            pass
            except Exception as e:
                print(f"✗ {selector}: {str(e)[:50]}")
        
        # 查找所有包含 "company" 或 "employer" 的链接
        print("\n=== 查找包含 'company' 或 'employer' 的链接 ===")
        all_links = await page.query_selector_all('a')
        company_related_links = []
        for link in all_links:
            try:
                href = await link.get_attribute('href')
                text = await elem.inner_text()
                if href and ('company' in href.lower() or 'employer' in href.lower()):
                    company_related_links.append({
                        'href': href,
                        'text': text[:100] if text else None
                    })
            except:
                pass
        
        if company_related_links:
            print(f"找到 {len(company_related_links)} 个相关链接:")
            for i, link in enumerate(company_related_links[:10]):  # 只显示前10个
                print(f"  {i+1}. {link['href']} - {link['text']}")
        
        # 查找包含 "More about" 的文本
        print("\n=== 查找包含 'More about' 的元素 ===")
        try:
            more_about_elements = await page.query_selector_all('*')
            for elem in more_about_elements[:50]:  # 限制检查数量
                try:
                    text = await elem.inner_text()
                    if text and 'more about' in text.lower():
                        tag_name = await elem.evaluate('el => el.tagName')
                        class_name = await elem.get_attribute('class')
                        print(f"  找到: <{tag_name}> class='{class_name}'")
                        print(f"    文本: {text[:150]}")
                        # 尝试获取父元素或兄弟元素
                        try:
                            parent = await elem.evaluate_handle('el => el.parentElement')
                            if parent:
                                parent_text = await parent.as_element().inner_text()
                                print(f"    父元素文本: {parent_text[:150]}")
                        except:
                            pass
                        break
                except:
                    continue
        except Exception as e:
            print(f"  错误: {e}")
        
        # 获取页面的主要 HTML 结构（简化版）
        print("\n=== 页面主要结构 ===")
        try:
            # 获取标题区域
            header_selectors = [
                '[data-automation="jobHeader"]',
                '.job-header',
                'header',
                'div[class*="header"]'
            ]
            for selector in header_selectors:
                try:
                    header = await page.query_selector(selector)
                    if header:
                        html = await header.inner_html()
                        print(f"\n找到头部元素 ({selector}):")
                        print(html[:500])  # 只显示前500字符
                        break
                except:
                    continue
        except Exception as e:
            print(f"  错误: {e}")
        
        # 等待用户查看（在浏览器中）
        print("\n浏览器窗口将保持打开30秒，请检查页面...")
        print("如果找到公司名称，请告诉我它在页面的哪个位置（例如：在标题下方、在'More about'链接中等）")
        await page.wait_for_timeout(30000)
        
        await browser.close()


if __name__ == "__main__":
    # 可以从命令行参数获取URL，或使用默认的测试URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # 使用一个示例 Seek URL（需要用户提供实际的URL）
        print("请提供一个 Seek 职位页面的 URL")
        print("用法: python debug_seek_company.py <URL>")
        print("\n或者直接输入 URL:")
        url = input("URL: ").strip()
    
    if not url:
        print("错误: 需要提供 URL")
        sys.exit(1)
    
    asyncio.run(debug_seek_page(url))
