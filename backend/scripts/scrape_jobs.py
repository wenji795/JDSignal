"""使用Playwright抓取Seek职位数据"""
import sys
import asyncio
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json
from urllib.parse import quote_plus

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))

from playwright.async_api import async_playwright, Page, Browser
import httpx

API_BASE_URL = "http://127.0.0.1:8000"




async def scrape_seek_job(page: Page, job_url: str) -> Optional[Dict[str, Any]]:
    """
    抓取Seek职位页面
    """
    try:
        print(f"正在访问: {job_url}")
        await page.goto(job_url, wait_until="networkidle", timeout=30000)
        
        # 等待页面加载 - 增加等待时间确保动态内容加载完成
        await page.wait_for_timeout(3000)
        
        # 等待关键元素加载
        try:
            await page.wait_for_selector('h1', timeout=5000)
        except:
            pass
        
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
        
        # 提取公司名称 - 使用多种方法，按优先级排序
        company_found = False
        
        # 方法1: 使用data-automation="advertiser-name"（Seek新版本）
        # 注意：这个span可能是空的，需要从父元素或兄弟元素获取
        try:
            advertiser_elem = await page.query_selector('[data-automation="advertiser-name"]')
            if advertiser_elem:
                # 先尝试直接获取文本
                company_text = (await advertiser_elem.inner_text()).strip()
                
                # 如果span是空的，使用JavaScript查找公司名称
                if not company_text or len(company_text) == 0:
                    company_text = await advertiser_elem.evaluate('''el => {
                        // 方法1: 查找父元素中的文本（可能是button、div、a等）
                        let parent = el.parentElement;
                        if (parent) {
                            // 获取父元素的所有文本内容
                            let parentText = parent.textContent || parent.innerText || '';
                            // 移除"View all jobs"等后缀
                            parentText = parentText.replace(/View all jobs/gi, '').trim();
                            // 移除换行和多余空格
                            parentText = parentText.replace(/\\s+/g, ' ').trim();
                            
                            // 如果父元素有文本，返回第一个有意义的部分
                            if (parentText && parentText.length > 0) {
                                // 取第一个单词或短语（通常是公司名）
                                let parts = parentText.split(/[\\s\\n]+/);
                                if (parts.length > 0 && parts[0].length > 1) {
                                    // 如果第一个部分太短，尝试组合前几个部分
                                    if (parts[0].length < 3 && parts.length > 1) {
                                        return parts.slice(0, Math.min(3, parts.length)).join(' ').trim();
                                    }
                                    return parts[0];
                                }
                                return parentText;
                            }
                            
                            // 方法2: 查找兄弟元素
                            let sibling = parent.firstElementChild || parent.firstChild;
                            while (sibling) {
                                if (sibling !== el && sibling.textContent) {
                                    let siblingText = sibling.textContent.trim();
                                    if (siblingText && !siblingText.toLowerCase().includes('view all jobs')) {
                                        return siblingText.split(/[\\s\\n]+/)[0];
                                    }
                                }
                                sibling = sibling.nextSibling;
                            }
                            
                            // 方法3: 查找父元素的第一个文本节点
                            let walker = document.createTreeWalker(
                                parent,
                                NodeFilter.SHOW_TEXT,
                                null,
                                false
                            );
                            let textNodes = [];
                            let node;
                            while (node = walker.nextNode()) {
                                let text = node.textContent.trim();
                                if (text && !text.toLowerCase().includes('view all jobs')) {
                                    textNodes.push(text);
                                }
                            }
                            if (textNodes.length > 0) {
                                return textNodes[0].split(/[\\s\\n]+/)[0];
                            }
                        }
                        
                        // 方法4: 查找包含公司名称的相邻元素
                        let container = el.closest('[class*="company"], [class*="advertiser"], [class*="employer"]');
                        if (container) {
                            let containerText = container.textContent || container.innerText || '';
                            containerText = containerText.replace(/View all jobs/gi, '').trim();
                            if (containerText) {
                                return containerText.split(/[\\s\\n]+/)[0];
                            }
                        }
                        
                        return '';
                    }''')
                
                # 清理和验证公司名称
                if company_text:
                    company_text = company_text.strip()
                    # 移除常见的后缀和无关文本
                    company_text = re.sub(r'\s*(View all jobs|view all jobs|View All Jobs).*$', '', company_text, flags=re.IGNORECASE)
                    company_text = company_text.strip()
                    # 移除可能的HTML实体和特殊字符
                    company_text = re.sub(r'\s+', ' ', company_text)
                    
                    # 验证：公司名应该是合理的长度和格式
                    if (company_text and 
                        len(company_text) > 1 and 
                        len(company_text) < 100 and
                        company_text.lower() not in ['unknown', 'seek', 'view all jobs', ''] and
                        not company_text.lower().startswith('view')):
                        job_data['company'] = company_text
                        company_found = True
                        print(f"  ✓ 方法1-找到公司名称: {company_text} (从advertiser-name)")
        except Exception as e:
            print(f"    方法1失败: {e}")
            pass
        
        # 方法2: 使用其他data-automation属性
        if not company_found:
            automation_selectors = [
                'a[data-automation="job-detail-company-name"]',
                '[data-automation="jobHeaderCompanyName"]',
                '[data-automation="job-detail-company"]',
                'span[data-automation="job-detail-company-name"]',
            ]
            for selector in automation_selectors:
                try:
                    company_elem = await page.query_selector(selector)
                    if company_elem:
                        company_text = (await company_elem.inner_text()).strip()
                        if company_text and len(company_text) > 0 and company_text.lower() not in ['unknown', 'seek']:
                            job_data['company'] = company_text
                            company_found = True
                            print(f"  ✓ 方法2-找到公司名称: {company_text} (选择器: {selector})")
                            break
                except Exception as e:
                    continue
        
        # 方法2: 查找包含/companies/的链接
        if not company_found:
            try:
                company_links = await page.query_selector_all('a[href*="/companies/"]')
                for link in company_links:
                    try:
                        href = await link.get_attribute('href')
                        if href and '/companies/' in href:
                            # 从URL提取公司名
                            company_slug = href.split('/companies/')[-1].split('/')[0].split('?')[0]
                            if company_slug and company_slug != 'companies':
                                # 从slug转换为可读的公司名
                                company_text = company_slug.replace('-', ' ').title()
                                # 也尝试获取链接文本
                                link_text = (await link.inner_text()).strip()
                                if link_text and len(link_text) > 0 and 'more about' not in link_text.lower():
                                    company_text = link_text
                                
                                if company_text and company_text.lower() not in ['unknown', 'seek', 'more about']:
                                    job_data['company'] = company_text
                                    company_found = True
                                    print(f"  ✓ 方法2-找到公司名称: {company_text} (从链接: {href})")
                                    break
                    except:
                        continue
            except Exception as e:
                pass
        
        # 方法3: 使用XPath查找包含"More about"或公司相关文本的元素
        if not company_found:
            try:
                # 查找包含"More about"的链接
                more_about_links = await page.query_selector_all('a')
                for link in more_about_links:
                    try:
                        link_text = (await link.inner_text()).strip()
                        href = await link.get_attribute('href')
                        
                        if href and '/companies/' in href:
                            # 从URL提取
                            company_slug = href.split('/companies/')[-1].split('/')[0].split('?')[0]
                            if company_slug and company_slug != 'companies':
                                company_text = company_slug.replace('-', ' ').title()
                                if company_text and company_text.lower() not in ['unknown', 'seek']:
                                    job_data['company'] = company_text
                                    company_found = True
                                    print(f"  ✓ 方法3-找到公司名称: {company_text} (从More about链接)")
                                    break
                    except:
                        continue
            except Exception as e:
                pass
        
        # 方法4: 查找class包含company的元素
        if not company_found:
            class_selectors = [
                '.job-detail-company-name',
                '[class*="company-name"]',
                '[class*="companyName"]',
                'a[class*="company"]',
            ]
            for selector in class_selectors:
                try:
                    company_elem = await page.query_selector(selector)
                    if company_elem:
                        company_text = (await company_elem.inner_text()).strip()
                        if company_text and len(company_text) > 0 and company_text.lower() not in ['unknown', 'seek', 'more about', 'about the company']:
                            job_data['company'] = company_text
                            company_found = True
                            print(f"  ✓ 方法4-找到公司名称: {company_text} (选择器: {selector})")
                            break
                except Exception as e:
                    continue
        
        # 方法5: 从页面标题中提取（Seek常见格式）
        if not company_found:
            try:
                page_title = await page.title()
                print(f"    尝试从页面标题提取: {page_title}")
                
                # Seek格式1: "Job Title at Company Name | Seek"
                if ' at ' in page_title:
                    parts = page_title.split(' at ')
                    if len(parts) > 1:
                        company_from_title = parts[1].split(' | ')[0].split(' - ')[0].strip()
                        # 清理可能的额外信息
                        company_from_title = re.sub(r'\s*-\s*.*$', '', company_from_title)  # 移除 "- Location" 部分
                        if company_from_title and company_from_title.lower() not in ['seek', 'unknown', '']:
                            job_data['company'] = company_from_title
                            company_found = True
                            print(f"  ✓ 方法5-从标题提取公司名称: {company_from_title}")
                
                # Seek格式2: "Job Title - Company Name | Seek" 或 "Job Title - Company Name - Location | Seek"
                elif ' - ' in page_title and ' | ' in page_title:
                    # 找到最后一个 " - " 和 " | " 之间的内容
                    before_seek = page_title.split(' | ')[0]
                    parts = before_seek.split(' - ')
                    if len(parts) >= 2:
                        # 取倒数第二个部分作为公司名（最后一个通常是地点）
                        company_from_title = parts[-2].strip() if len(parts) > 2 else parts[-1].strip()
                        if company_from_title and company_from_title.lower() not in ['seek', 'unknown', '']:
                            job_data['company'] = company_from_title
                            company_found = True
                            print(f"  ✓ 方法5-从标题提取公司名称: {company_from_title}")
            except Exception as e:
                print(f"    从标题提取失败: {e}")
                pass
        
        # 最后尝试：从JD文本的开头提取（有些职位会在开头提到公司名）
        if not company_found and job_data.get('jd_text'):
            try:
                jd_text = job_data['jd_text'][:500]  # 只检查前500字符
                # 查找常见的公司名称模式
                # 模式1: "About [Company Name]"
                match = re.search(r'About\s+([A-Z][a-zA-Z\s&]+)', jd_text)
                if match:
                    potential_company = match.group(1).strip()
                    if len(potential_company) < 50:  # 合理的公司名长度
                        job_data['company'] = potential_company
                        company_found = True
                        print(f"  ✓ 从JD文本提取公司名称: {potential_company}")
            except:
                pass
        
        if not company_found:
            print(f"  ⚠ 未能提取公司名称，尝试从页面标题提取...")
            # 打印页面标题用于调试
            try:
                page_title = await page.title()
                print(f"    页面标题: {page_title}")
            except:
                pass
        
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


def is_nz_location(location: Optional[str]) -> bool:
    """检查location是否在新西兰"""
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
    
    return False


async def save_job_to_api(job_data: Dict[str, Any], source: str) -> bool:
    """保存职位到API"""
    try:
        # 检查URL是否是澳大利亚的（seek.com.au）
        url = job_data.get('url', '')
        if 'seek.com.au' in url:
            print(f"⏭ 跳过澳大利亚职位（URL）: {url}")
            return False
        
        # 检查location是否在新西兰
        location = job_data.get('location', '')
        if not is_nz_location(location):
            print(f"⏭ 跳过非新西兰职位（Location: {location}）: {url}")
            return False
        
        # 确定来源（只支持Seek）
        if 'seek.co.nz' in url:
            source = 'seek'
        else:
            source = 'seek'  # 默认为seek
        
        # 准备数据
        # 如果 company 为空或 "Unknown"，则使用 None（不设置该字段）
        company_guess = job_data.get('company', '').strip()
        if not company_guess or company_guess.lower() == 'unknown':
            company_guess = None
        
        payload = {
            "source": source,
            "url": job_data.get('url', ''),
            "page_title": job_data.get('page_title', job_data.get('title', '')),
            "company_guess": company_guess,
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
                company_display = company_guess or "未知公司"
                print(f"✓ 成功保存: {job_data.get('title', 'Unknown')} at {company_display}")
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
    在Seek上搜索职位，返回职位URL列表（支持翻页）
    
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
        
        job_urls = []
        page_num = 1
        max_pages = 10  # 最多翻10页，避免无限循环
        
        while len(job_urls) < max_results and page_num <= max_pages:
            # 构建当前页的URL
            if page_num == 1:
                current_url = search_url
            else:
                current_url = f"{search_url}&page={page_num}"
            
            print(f"正在抓取第 {page_num} 页...")
            await page.goto(current_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)  # 等待搜索结果加载
            
            page_urls = []
            
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
                            
                            # 只添加新西兰的URL（seek.co.nz），跳过澳大利亚（seek.com.au）
                            if 'seek.co.nz' in full_url and full_url not in job_urls and full_url not in page_urls:
                                page_urls.append(full_url)
                            elif 'seek.com.au' in full_url:
                                # 跳过澳大利亚的职位
                                continue
                        except Exception as e:
                            continue
                    
                    if page_urls:
                        break
                except Exception as e:
                    print(f"尝试选择器 {selector} 失败: {e}")
                    continue
            
            # 如果上面没找到，尝试从页面源码中提取
            if not page_urls:
                print("尝试从页面源码中提取链接...")
                try:
                    content = await page.content()
                    # 查找所有 /job/ 开头的链接
                    matches = re.findall(r'href="(/job/\d+[^"]*)"', content)
                    domain = 'seek.co.nz' if country == 'nz' else 'seek.com.au'
                    for match in matches:
                        full_url = f"https://www.{domain}{match.split('?')[0].split('#')[0]}"
                        # 只添加新西兰的URL，跳过澳大利亚
                        if 'seek.co.nz' in full_url and full_url not in job_urls and full_url not in page_urls:
                            page_urls.append(full_url)
                        elif 'seek.com.au' in full_url:
                            # 跳过澳大利亚的职位
                            continue
                except Exception as e:
                    print(f"从源码提取链接失败: {e}")
            
            if not page_urls:
                print(f"第 {page_num} 页没有找到新职位，停止翻页")
                break
            
            # 添加到总列表
            job_urls.extend(page_urls)
            print(f"第 {page_num} 页找到 {len(page_urls)} 个职位，累计 {len(job_urls)} 个")
            
            # 检查是否还需要继续翻页
            if len(job_urls) >= max_results:
                break
            
            # 检查是否有下一页按钮
            try:
                next_button = await page.query_selector('a[data-automation="pagination-next-button"]')
                if not next_button:
                    # 尝试其他可能的下页按钮选择器
                    next_button = await page.query_selector('a[aria-label*="Next"]')
                if not next_button:
                    # 检查是否已经是最后一页
                    disabled_next = await page.query_selector('a[data-automation="pagination-next-button"][aria-disabled="true"]')
                    if disabled_next:
                        print("已到达最后一页")
                        break
                if not next_button:
                    print("未找到下一页按钮，停止翻页")
                    break
            except:
                pass
            
            page_num += 1
            await asyncio.sleep(2)  # 翻页之间等待，避免请求过快
        
        print(f"总共找到 {len(job_urls)} 个职位链接")
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
                # 只支持Seek URL
                if 'seek.com' in url or 'seek.co.nz' in url:
                    job_data = await scrape_seek_job(page, url)
                else:
                    print(f"✗ 不支持的URL类型（仅支持Seek），跳过: {url}")
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
    
    parser = argparse.ArgumentParser(description='使用Playwright抓取Seek职位')
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