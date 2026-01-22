"""调试posted_date提取 - 检查特定URL的页面结构"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from playwright.async_api import async_playwright


async def debug_posted_date(url: str):
    """调试特定URL的posted_date提取"""
    browser = None
    context = None
    page = None
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # 使用有头模式以便观察
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            
            # 检查浏览器是否已关闭
            if browser.is_connected():
                page = await context.new_page()
            else:
                raise Exception("浏览器连接已断开")
            
            print(f"正在访问: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            
            # 方法1: 检查所有包含"Posted"的元素
            print("\n=== 方法1: 查找包含'Posted'的元素 ===")
            posted_elements = await page.evaluate('''() => {
                const results = [];
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                
                let node;
                while (node = walker.nextNode()) {
                    const text = node.textContent.trim();
                    if (/posted/i.test(text)) {
                        let parent = node.parentElement;
                        let parentText = parent ? parent.textContent.trim() : '';
                        results.push({
                            text: text,
                            parentText: parentText.substring(0, 200),
                            tagName: parent ? parent.tagName : 'unknown'
                        });
                    }
                }
                return results.slice(0, 10);  // 只返回前10个
            }''')
            
            print(f"找到 {len(posted_elements)} 个包含'Posted'的文本节点:")
            for i, elem in enumerate(posted_elements, 1):
                print(f"  {i}. 文本: {elem['text'][:100]}")
                print(f"     父元素: {elem['tagName']}")
                print(f"     父文本: {elem['parentText'][:100]}")
                print()
            
            # 方法2: 检查data-automation属性
            print("\n=== 方法2: 查找data-automation属性 ===")
            automation_elements = await page.evaluate('''() => {
                const results = [];
                const elements = document.querySelectorAll('[data-automation*="date"], [data-automation*="Date"], [data-automation*="posted"], [data-automation*="Posted"]');
                elements.forEach(el => {
                    results.push({
                        selector: el.tagName + (el.className ? '.' + el.className.split(' ')[0] : ''),
                        automation: el.getAttribute('data-automation'),
                        text: el.textContent.trim().substring(0, 100),
                        datetime: el.getAttribute('datetime')
                    });
                });
                return results;
            }''')
            
            print(f"找到 {len(automation_elements)} 个相关元素:")
            for i, elem in enumerate(automation_elements, 1):
                print(f"  {i}. data-automation: {elem['automation']}")
                print(f"     文本: {elem['text']}")
                print(f"     datetime: {elem['datetime']}")
                print()
            
            # 方法3: 检查页面HTML中的日期模式
            print("\n=== 方法3: 检查HTML中的日期模式 ===")
            html_content = await page.content()
            import re
            patterns = [
                r'posted\s+\d+\s*[dwmyh]\s*ago',
                r'posted\s+\d+\s*(?:day|days|week|weeks|month|months)\s*ago',
                r'Posted\s+\d+\s*[dwmyh]\s*ago',
            ]
            
            for pattern in patterns:
                matches = list(re.finditer(pattern, html_content, re.IGNORECASE))
                if matches:
                    print(f"模式 '{pattern}' 找到 {len(matches)} 个匹配:")
                    for match in matches[:5]:  # 只显示前5个
                        context_start = max(0, match.start() - 50)
                        context_end = min(len(html_content), match.end() + 50)
                        context = html_content[context_start:context_end]
                        print(f"  匹配: {match.group(0)}")
                        print(f"  上下文: {context}")
                        print()
            
            # 方法4: 获取页面标题和关键区域
            print("\n=== 方法4: 页面信息 ===")
            page_title = await page.title()
            print(f"页面标题: {page_title}")
            
            # 等待用户查看（使用异步方式）
            print("\n页面已打开，请检查浏览器窗口...")
            print("等待30秒后自动关闭，或手动关闭浏览器窗口...")
            await page.wait_for_timeout(30000)
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 安全地关闭资源
        try:
            if page and not page.is_closed():
                await page.close()
        except:
            pass
        try:
            if context:
                await context.close()
        except:
            pass
        try:
            if browser and browser.is_connected():
                await browser.close()
        except:
            pass


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='调试posted_date提取')
    parser.add_argument('url', help='要调试的URL')
    
    args = parser.parse_args()
    
    asyncio.run(debug_posted_date(args.url))
