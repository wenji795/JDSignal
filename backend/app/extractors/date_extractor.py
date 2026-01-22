"""日期提取器：从文本中提取发布日期"""
import re
from typing import Optional
from datetime import datetime, timedelta


def parse_posted_date(date_text: str) -> Optional[datetime]:
    """
    解析发布日期文本，支持多种格式
    
    支持的格式：
    - "Posted 13d ago"
    - "Posted 2w ago"
    - "Posted 1 month ago"
    - "Posted 21/01/2026"
    - "2026-01-21"
    """
    if not date_text:
        return None
    
    date_text = date_text.strip()
    
    # 尝试解析相对时间格式（如 "13d ago", "2w ago"）
    relative_patterns = [
        (r'(\d+)\s*d\s*ago', lambda m: timedelta(days=int(m.group(1)))),
        (r'(\d+)\s*day\s*ago', lambda m: timedelta(days=int(m.group(1)))),
        (r'(\d+)\s*days?\s*ago', lambda m: timedelta(days=int(m.group(1)))),
        (r'(\d+)\s*w\s*ago', lambda m: timedelta(weeks=int(m.group(1)))),
        (r'(\d+)\s*week\s*ago', lambda m: timedelta(weeks=int(m.group(1)))),
        (r'(\d+)\s*weeks?\s*ago', lambda m: timedelta(weeks=int(m.group(1)))),
        (r'(\d+)\s*m\s*ago', lambda m: timedelta(days=int(m.group(1)) * 30)),
        (r'(\d+)\s*month\s*ago', lambda m: timedelta(days=int(m.group(1)) * 30)),
        (r'(\d+)\s*months?\s*ago', lambda m: timedelta(days=int(m.group(1)) * 30)),
        (r'(\d+)\s*y\s*ago', lambda m: timedelta(days=int(m.group(1)) * 365)),
        (r'(\d+)\s*year\s*ago', lambda m: timedelta(days=int(m.group(1)) * 365)),
        (r'(\d+)\s*years?\s*ago', lambda m: timedelta(days=int(m.group(1)) * 365)),
    ]
    
    for pattern, delta_func in relative_patterns:
        match = re.search(pattern, date_text, re.IGNORECASE)
        if match:
            try:
                delta = delta_func(match)
                return datetime.utcnow() - delta
            except:
                continue
    
    # 尝试解析绝对日期格式
    absolute_patterns = [
        (r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        (r'(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})', lambda m: datetime(int(m.group(3)) if len(m.group(3)) == 4 else 2000 + int(m.group(3)), int(m.group(2)), int(m.group(1)))),
        (r'(\d{1,2})\s+(\w+)\s+(\d{4})', lambda m: _parse_month_day_year(m.group(1), m.group(2), m.group(3))),
    ]
    
    for pattern, parse_func in absolute_patterns:
        match = re.search(pattern, date_text, re.IGNORECASE)
        if match:
            try:
                return parse_func(match)
            except:
                continue
    
    return None


def _parse_month_day_year(day: str, month: str, year: str) -> Optional[datetime]:
    """解析 "21 January 2026" 格式的日期"""
    month_map = {
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12,
    }
    
    month_num = month_map.get(month.lower())
    if month_num:
        try:
            return datetime(int(year), month_num, int(day))
        except:
            return None
    return None


def extract_posted_date_from_text(text: str) -> Optional[datetime]:
    """
    从文本中提取发布日期
    查找包含"Posted"、"posted"、"Date posted"等关键词的文本
    优先匹配Seek格式："Posted 13d ago"
    """
    if not text:
        return None
    
    # 优先查找Seek格式："Posted Xd ago" 或 "Posted X days ago"
    seek_patterns = [
        r'posted\s+(\d+\s*[dwmyh])\s*ago',  # "Posted 13d ago", "Posted 2w ago"
        r'posted\s+(\d+\s*(?:day|days|week|weeks|month|months|hour|hours|minute|minutes))\s*ago',  # "Posted 13 days ago"
    ]
    
    for pattern in seek_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                # 提取包含"Posted"的完整文本
                full_match = match.group(0)
                date = parse_posted_date(full_match)
                if date:
                    return date
            except:
                continue
    
    # 查找包含"Posted"的行
    lines = text.split('\n')
    for line in lines:
        line_lower = line.lower().strip()
        if 'posted' in line_lower or 'date posted' in line_lower:
            # 尝试从这一行提取日期
            date = parse_posted_date(line)
            if date:
                return date
    
    # 查找常见的日期模式
    date_patterns = [
        r'posted\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'posted\s+(\d{1,2}\s+\w+\s+\d{4})',
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # 通用日期格式
    ]
    
    for pattern in date_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                date_str = match.group(1) if match.groups() else match.group(0)
                date = parse_posted_date(date_str)
                if date:
                    return date
            except:
                continue
    
    return None
