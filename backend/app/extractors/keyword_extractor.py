"""关键词提取主模块"""
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from app.extractors.dynamic_extractor import extract_dynamic_keywords

# 证书关键词
CERTIFICATIONS = [
    "AWS Certified", "AWS Solutions Architect", "AWS Developer",
    "Azure Certified", "Azure Solutions Architect",
    "GCP Certified", "Google Cloud Professional",
    "PMP", "Project Management Professional",
    "Scrum Master", "Certified Scrum Master", "CSM",
    "CISSP", "Cisco Certified", "CCNA", "CCNP",
    "Oracle Certified", "Microsoft Certified", "MCSE",
    "Kubernetes Certified", "CKA", "CKAD",
    "ISTQB", "Salesforce Certified", "Salesforce Administrator",
    "Teradata Certified", "Red Hat Certified", "RHCE"
]

# 学位关键词
DEGREE_KEYWORDS = {
    "bachelor": ["bachelor", "bachelor's", "bs", "b.sc", "ba", "b.a"],
    "master": ["master", "master's", "ms", "m.sc", "ma", "m.a", "mba"],
    "phd": ["phd", "ph.d", "doctorate", "doctoral"],
    "associate": ["associate", "a.a", "a.s"]
}

# 经验年限正则模式
EXPERIENCE_PATTERNS = [
    r'(\d+)\+?\s*years?\s+of?\s+experience',
    r'(\d+)\+?\s*yrs?\s+of?\s+experience',
    r'experience.*?(\d+)\+?\s*years?',
    r'(\d+)\+?\s*years?\s+experience',
    r'minimum\s+of\s+(\d+)\s*years?',
    r'at\s+least\s+(\d+)\s*years?',
    r'(\d+)\+?\s*years?\s+in',
    r'(\d+)\+?\s*years?\s+working'
]

# 需要过滤的通用关键词（对分析没有实际价值）
# 注意：使用小写，匹配时会转换为小写进行比较
COMMON_KEYWORDS_TO_FILTER = {
    # 网站和平台名称（大小写不敏感）
    'seek', 'seek.co.nz', 'linkedin', 'indeed',
    # 地理位置相关（新西兰特定）
    'nz', 'new zealand', 'cbd', 'auckland', 'wellington', 'christchurch',
    'hamilton', 'dunedin', 'tauranga', 'new', 'zealand',
    # 城市缩写
    'akl', 'wlg', 'chc', 'ham', 'dun', 'tau',  # Auckland, Wellington, Christchurch等的缩写
    # 通用职位相关词汇
    'job', 'jobs', 'position', 'positions', 'role', 'roles', 
    'opportunity', 'opportunities', 'vacancy', 'vacancies',
    'apply', 'application', 'applicant', 'applicants', 'candidate', 'candidates',
    'company', 'companies', 'employer', 'employers', 'organisation', 'organization',
    # 礼貌用语
    'please', 'thank', 'thanks', 'regards', 'sincerely',
    # 工作类型
    'full time', 'full-time', 'part time', 'part-time', 'permanent', 'contract',
    'temporary', 'temp', 'casual',
    # 工作地点类型
    'remote', 'hybrid', 'onsite', 'on-site', 'work from home', 'wfh',
    # 薪资和福利
    'salary', 'wage', 'wages', 'compensation', 'benefits', 'benefit',
    'package', 'remuneration',
    # 经验和时间
    'experience', 'years', 'year', 'month', 'months', 'yr', 'yrs',
    # 要求和资格
    'required', 'requirement', 'requirements', 'qualification', 'qualifications',
    'qualify', 'qualified', 'qualifying',
    # 技能和能力
    'skill', 'skills', 'ability', 'abilities', 'capability', 'capabilities',
    # 团队和工作
    'team', 'teams', 'work', 'working', 'workplace', 'workplace', 'workforce',
    # 通用行业术语
    'it', 'information technology',  # IT是通用术语，对分析没有价值
    # 国家相关
    'australia', 'au', 'us', 'usa', 'united states', 'america',
    # 地点相关
    'location', 'locations', 'area', 'areas', 'region', 'regions', 'city', 'cities',
    # 描述性词汇
    'description', 'about', 'overview', 'summary', 'detail', 'details',
    # 联系信息
    'contact', 'email', 'phone', 'telephone', 'website', 'www', 'http', 'https',
    # 导航和操作
    'click', 'here', 'more', 'information', 'details', 'view', 'see',
    # 平等机会
    'equal', 'opportunity', 'employer', 'eoe', 'eeo', 'diversity', 'inclusive',
    # 其他常见无意义词
    'the', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 'else',
    'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were',
    'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
    'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can'
}

# Must-have指示词
MUST_HAVE_INDICATORS = [
    r'\brequirements?\b', r'\bmust\s+have\b', r'\bessential\b',
    r'\bwe\s+require\b', r'\brequired\b', r'\bmandatory\b',
    r'\bqualifications?\b', r'\bneeded\b', r'\bnecessary\b'
]

# Nice-to-have指示词（增强版，包括更多表达方式）
NICE_TO_HAVE_INDICATORS = [
    r'\bnice\s+to\s+have\b', r'\bpreferred\b', r'\bbonus\b',
    r'\bdesirable\b', r'\badvantage\b', r'\bplus\b',
    r'\bwould\s+be\s+great\b', r'\boptional\b',
    r'\bbonus\s+experience\b', r'\bbonus\s+skills?\b',
    r'\bwould\s+be\s+advantageous\b', r'\bwould\s+be\s+an\s+advantage\b',
    r'\bhowever\s+knowledge\s+of\b',  # "however knowledge of X would be advantageous"
    r'\badvantageous\b', r'\bpreferred\s+but\s+not\s+required\b'
]


def load_skill_dictionary() -> Dict:
    """加载技能字典"""
    dict_path = Path(__file__).parent / "skill_dictionary.json"
    with open(dict_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_skill_mapping(skill_dict: Dict) -> Tuple[Dict[str, str], Dict[str, Dict]]:
    """
    创建技能映射：别名 -> 规范名称，以及规范名称 -> 技能信息
    返回：(alias_to_canonical, canonical_to_info)
    """
    alias_to_canonical = {}
    canonical_to_info = {}
    
    for skill in skill_dict["skills"]:
        term = skill["term"]
        canonical_to_info[term.lower()] = skill
        
        # 添加规范名称本身
        alias_to_canonical[term.lower()] = term
        
        # 添加别名
        for alias in skill.get("aliases", []):
            alias_to_canonical[alias.lower()] = term
    
    return alias_to_canonical, canonical_to_info


def find_keyword_positions(text: str, keyword: str) -> List[Tuple[int, int]]:
    """找到关键词在文本中的所有位置（字符位置）"""
    positions = []
    # 对于包含特殊字符的关键词（如C#），需要特殊处理
    escaped_keyword = re.escape(keyword)
    
    # 如果关键词包含非字母数字字符（如#、.、+等），使用更灵活的匹配
    if re.search(r'[^a-zA-Z0-9]', keyword):
        # 对于特殊字符，使用更宽松的边界匹配
        # 例如：C# 可以匹配 "C#", "C# ", " C#", "C#," 等
        pattern = r'(?<![a-zA-Z0-9])' + escaped_keyword + r'(?![a-zA-Z0-9])'
    else:
        # 对于普通关键词，使用单词边界
        pattern = r'\b' + escaped_keyword + r'\b'
    
    for match in re.finditer(pattern, text, re.IGNORECASE):
        positions.append((match.start(), match.end()))
    return positions


def is_in_section(text: str, position: int, indicators: List[str], window: int = 500) -> bool:
    """检查位置是否在包含特定指示词的区域内"""
    start = max(0, position - window)
    end = min(len(text), position + window)
    section = text[start:end].lower()
    
    for indicator in indicators:
        if re.search(indicator, section, re.IGNORECASE):
            return True
    return False


def is_in_tech_stack_section(text: str, position: int, window: int = 500) -> bool:
    """
    检查位置是否在tech stack区域
    例如："Our tech stack: C#, Reqnroll, Postman, JavaScript, k6, JMeter and Azure."
    """
    start = max(0, position - window)
    section_before = text[start:position].lower()
    
    # 检查是否在"tech stack"、"technology stack"、"tech"等区域
    tech_stack_patterns = [
        r'tech\s+stack[:：]',
        r'technology\s+stack[:：]',
        r'our\s+tech\s+stack[:：]',
        r'our\s+technology\s+stack[:：]',
        r'tech[:：]',
        r'technologies[:：]',
        r'stack[:：]'
    ]
    
    for pattern in tech_stack_patterns:
        if re.search(pattern, section_before, re.IGNORECASE):
            # 检查是否在"Bonus experience"之前
            remaining_text = text[start:position].lower()
            if not re.search(r'bonus\s+(?:experience|skills?)[:：]', remaining_text, re.IGNORECASE):
                return True
    
    return False


def is_in_main_skills_section(text: str, position: int, window: int = 1000) -> bool:
    """
    检查位置是否在主要技能区域（如"Skills and Tools"）
    如果在主要技能区域，即使有"however...would be advantageous"，也应该归类为must-have
    注意：如果已经在"Bonus experience"区域，则不应该返回True
    """
    # 首先检查是否在"Bonus experience"区域，如果是，则不是主要技能区域
    if is_in_bonus_experience_section(text, position):
        return False
    
    start = max(0, position - window)
    section_before = text[start:position].lower()
    
    # 检查是否在"Skills and Tools"、"Skills"、"Requirements"等主要技能区域
    main_skills_patterns = [
        r'skills?\s+and\s+tools?[:：]',
        r'skills?[:：]',
        r'requirements?[:：]',
        r'qualifications?[:：]',
        r'experience\s+and\s+other\s+requirements?[:：]',
        r'technical\s+skills?[:：]',
        r'core\s+skills?[:：]',
        r'essential\s+skills?[:：]'
    ]
    
    for pattern in main_skills_patterns:
        matches = list(re.finditer(pattern, section_before, re.IGNORECASE))
        if matches:
            # 找到最近的匹配
            last_match = matches[-1]
            # 检查是否在"Bonus experience"之前（如果在Bonus之后，就不是主要技能区域）
            remaining_text = text[start + last_match.end():position].lower()
            if not re.search(r'bonus\s+(?:experience|skills?)[:：]', remaining_text, re.IGNORECASE):
                return True
    
    return False


def is_in_bonus_experience_section(text: str, position: int, window: int = 2000) -> bool:
    """
    检查位置是否在"Bonus experience"区域
    这是最明确的nice-to-have区域
    """
    start = max(0, position - window)
    before_text = text[start:position].lower()
    
    # 查找最近的"Bonus experience:"或"Bonus:"标题
    bonus_patterns = [
        r'bonus\s+experience[:：]',
        r'bonus\s+skills?[:：]',
        r'bonus[:：]'
    ]
    
    for pattern in bonus_patterns:
        matches = list(re.finditer(pattern, before_text, re.IGNORECASE))
        if matches:
            # 找到最近的匹配
            last_match = matches[-1]
            bonus_pos = start + last_match.end()
            # 检查是否在"Bonus"之后，且距离不太远
            if position - bonus_pos < 1000:  # 在1000字符内
                # 检查是否在下一个主要章节之前（如"Requirements"、"Skills"等）
                remaining_text = text[bonus_pos:min(len(text), bonus_pos + 2000)].lower()
                next_section_match = re.search(r'^(?:skills?|requirements?|qualifications?|experience\s+and\s+other)[:：]', remaining_text, re.MULTILINE | re.IGNORECASE)
                if not next_section_match or position < bonus_pos + next_section_match.start():
                    return True
    
    return False


def check_contextual_nice_to_have(text: str, position: int, keyword: str, window: int = 300) -> bool:
    """
    检查关键词是否在明确的nice-to-have上下文中
    例如："however knowledge of Selenium would be advantageous"
    """
    # 首先检查是否在"Bonus experience"区域（最明确的nice-to-have区域）
    if is_in_bonus_experience_section(text, position):
        return True
    
    # 检查是否在主要技能区域
    if is_in_main_skills_section(text, position):
        # 如果在主要技能区域，即使有"however...would be advantageous"，也应该是must-have
        return False
    
    start = max(0, position - window)
    end = min(len(text), position + window)
    section = text[start:end]
    section_lower = section.lower()
    keyword_lower = keyword.lower()
    
    # 检查"however...would be advantageous"模式
    # 匹配: "however knowledge of [keyword] would be advantageous"
    pattern1 = r'however\s+[^.]*?' + re.escape(keyword_lower) + r'[^.]*?(?:would\s+be\s+advantageous|would\s+be\s+an\s+advantage|advantageous)'
    if re.search(pattern1, section_lower, re.IGNORECASE):
        return True
    
    # 检查"however...knowledge of [keyword]"模式（通常后面跟着advantageous）
    pattern2 = r'however\s+[^.]*?knowledge\s+of\s+[^.]*?' + re.escape(keyword_lower)
    if re.search(pattern2, section_lower, re.IGNORECASE):
        # 检查后面是否有advantageous相关词汇
        remaining_text = text[position:min(len(text), position + 200)].lower()
        if re.search(r'would\s+be\s+advantageous|would\s+be\s+an\s+advantage|advantageous', remaining_text, re.IGNORECASE):
            return True
    
    return False


def is_in_heading_or_bullet(text: str, position: int, window: int = 200) -> bool:
    """检查位置是否在标题或列表项附近"""
    start = max(0, position - window)
    section = text[start:position]
    
    # 检查是否有标题标记（#、大写字母开头、冒号前）
    if re.search(r'^#+\s+|^[A-Z][^.!?]*:$|^[-*•]\s+', section, re.MULTILINE):
        return True
    
    return False


def extract_years_required(text: str) -> Optional[int]:
    """提取所需经验年限"""
    text_lower = text.lower()
    found_years = []
    
    for pattern in EXPERIENCE_PATTERNS:
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            years = int(match.group(1))
            found_years.append(years)
    
    return max(found_years) if found_years else None


def extract_degree_required(text: str) -> Optional[str]:
    """提取所需学位"""
    text_lower = text.lower()
    
    # 检查是否有学位关键词
    for degree_type, keywords in DEGREE_KEYWORDS.items():
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower, re.IGNORECASE):
                # 尝试提取完整学位信息
                pattern = r'\b' + re.escape(keyword) + r'[^\n]*?(?:degree|in|of)?\s*([A-Z][a-zA-Z\s]+)?'
                match = re.search(pattern, text, re.IGNORECASE)
                if match and match.group(1):
                    field = match.group(1).strip()
                    if field and len(field) > 2:
                        return f"{degree_type.title()} in {field}"
                return degree_type.title()
    
    return None


def extract_certifications(text: str) -> List[str]:
    """提取证书列表"""
    text_lower = text.lower()
    found_certs = []
    
    for cert in CERTIFICATIONS:
        pattern = r'\b' + re.escape(cert.lower()) + r'\b'
        if re.search(pattern, text_lower, re.IGNORECASE):
            found_certs.append(cert)
    
    return list(set(found_certs))  # 去重


def extract_keywords(jd_text: str) -> Dict:
    """
    从JD文本中提取所有关键词信息
    
    返回：
    {
        "keywords": [{"term": str, "category": str, "score": float}],
        "must_have_keywords": [str],
        "nice_to_have_keywords": [str],
        "years_required": int | None,
        "degree_required": str | None,
        "certifications": [str]
    }
    """
    # 加载技能字典
    skill_dict = load_skill_dictionary()
    alias_to_canonical, canonical_to_info = create_skill_mapping(skill_dict)
    
    # 初始化结果
    keyword_scores = defaultdict(lambda: {"term": "", "category": "", "score": 0.0, "count": 0})
    must_have_terms = set()
    nice_to_have_terms = set()
    
    # 查找所有技能匹配
    text_lower = jd_text.lower()
    
    for alias, canonical in alias_to_canonical.items():
        positions = find_keyword_positions(jd_text, alias)
        
        if positions:
            info = canonical_to_info[canonical.lower()]
            category = info.get("category", "unknown")
            
            # 计算基础分数（出现次数）
            count = len(positions)
            base_score = float(count) * 1.0  # 每次出现基础分1.0
            
            # 检查是否在must-have区域
            must_have_bonus = 0.0
            nice_to_have_bonus = 0.0
            heading_bonus = 0.0
            title_bonus = 0.0  # 标题中的关键词权重更高
            tech_stack_bonus = 0.0  # tech stack区域的权重
            
            # 检查是否在标题中（前200字符）
            title_text = jd_text[:200].lower()
            if alias.lower() in title_text or canonical.lower() in title_text:
                title_bonus = 3.0  # 标题中的关键词权重很高
            
            # 收集所有位置的上下文信息，用于最终分类决策
            has_bonus_experience_context = False
            has_skills_tools_context = False
            has_tech_stack_context = False
            has_nice_to_have_indicator = False
            has_must_have_indicator = False
            
            for pos, _ in positions:
                # 检查是否在tech stack区域（给予很高权重）
                if is_in_tech_stack_section(jd_text, pos):
                    tech_stack_bonus += 5.0  # tech stack区域的技能权重非常高
                    has_tech_stack_context = True
                
                # 检查是否在"Bonus experience"区域（优先级最高，明确标注为nice-to-have）
                if is_in_bonus_experience_section(jd_text, pos):
                    has_bonus_experience_context = True
                    nice_to_have_bonus += 2.0
                elif check_contextual_nice_to_have(jd_text, pos, alias):
                    # 检查其他nice-to-have上下文（如"however...would be advantageous"）
                    has_nice_to_have_indicator = True
                    nice_to_have_bonus += 1.5
                
                # 检查是否在主要技能区域（"Skills and Tools"等）
                # 注意：如果已经在"Bonus experience"区域，is_in_main_skills_section会返回False
                if is_in_main_skills_section(jd_text, pos):
                    has_skills_tools_context = True
                    must_have_bonus += 3.0
                
                # 检查明确的nice-to-have指示词（仅在不在主要技能区域时）
                if not has_skills_tools_context and is_in_section(jd_text, pos, NICE_TO_HAVE_INDICATORS):
                    has_nice_to_have_indicator = True
                    nice_to_have_bonus += 1.5
                
                # 检查must-have指示词
                if is_in_section(jd_text, pos, MUST_HAVE_INDICATORS):
                    has_must_have_indicator = True
                    must_have_bonus += 3.0
                
                if is_in_heading_or_bullet(jd_text, pos):
                    heading_bonus += 2.0  # 标题或列表项中的关键词权重更高
            
            # 根据优先级规则决定最终分类（避免重复）
            # 优先级：Bonus experience > Skills and Tools/Tech Stack > 其他指示词
            # 重要：每个关键词只能出现在一个列表中，使用if-elif确保互斥
            if has_bonus_experience_context:
                # 明确在"Bonus experience"区域，归类为nice-to-have（最高优先级）
                nice_to_have_terms.add(canonical)
            elif has_skills_tools_context or has_tech_stack_context:
                # 在"Skills and Tools"或"Tech Stack"区域，归类为must-have
                must_have_terms.add(canonical)
            elif has_nice_to_have_indicator and not has_must_have_indicator:
                # 有nice-to-have指示词，且没有must-have指示词，归类为nice-to-have
                nice_to_have_terms.add(canonical)
            elif has_must_have_indicator:
                # 有must-have指示词，归类为must-have
                must_have_terms.add(canonical)
            # 如果都没有明确的上下文，默认不添加到任何列表（让动态提取器处理）
            
            # 根据类别调整权重（类似ATS系统）
            category_weights = {
                "testing": 1.5,  # 测试工具权重较高
                "language": 1.3,  # 编程语言权重较高
                "framework": 1.2,  # 框架权重较高
                "devops": 1.1,   # DevOps工具权重较高
                "cloud": 1.1,    # 云平台权重较高
                "platform": 1.0, # 平台权重正常
                "data": 1.0,     # 数据权重正常
                "process": 0.8,  # 流程方法权重较低
                "tool": 0.9,     # 工具权重较低
                "architecture": 1.0,  # 架构权重正常
                "unknown": 0.7   # 未知类别权重最低
            }
            
            category_weight = category_weights.get(category, 1.0)
            
            # 计算总分（类似ATS系统的权重计算）
            total_score = (
                base_score * category_weight +  # 基础分 × 类别权重
                must_have_bonus +                # must-have奖励
                nice_to_have_bonus +            # nice-to-have奖励
                heading_bonus +                 # 标题/列表奖励
                title_bonus +                   # 标题奖励
                tech_stack_bonus                # tech stack奖励（权重最高）
            )
            
            # 更新或添加关键词
            if canonical.lower() not in keyword_scores or keyword_scores[canonical.lower()]["score"] < total_score:
                keyword_scores[canonical.lower()] = {
                    "term": canonical,
                    "category": category,
                    "score": total_score,
                    "count": count
                }
    
    # 合并字典匹配和动态提取的结果
    # 1. 先进行动态提取（不依赖字典）
    dynamic_keywords = extract_dynamic_keywords(jd_text)
    
    # 2. 将动态提取的结果合并到keyword_scores中
    for dyn_kw in dynamic_keywords:
        term_lower = dyn_kw["term"].lower()
        # 如果字典中已有该词，保留字典的结果（通常更准确）
        if term_lower not in keyword_scores:
            keyword_scores[term_lower] = {
                "term": dyn_kw["term"],
                "category": dyn_kw["category"],
                "score": dyn_kw["score"],
                "count": dyn_kw["count"]
            }
        else:
            # 如果动态提取的分数更高，更新分数（但保留字典的类别）
            if dyn_kw["score"] > keyword_scores[term_lower]["score"]:
                keyword_scores[term_lower]["score"] = dyn_kw["score"]
                keyword_scores[term_lower]["count"] = max(
                    keyword_scores[term_lower]["count"],
                    dyn_kw["count"]
                )
    
    # 3. 构建keywords列表（按分数降序排列，类似ATS系统）
    keywords = [
        {
            "term": v["term"],
            "category": v["category"],
            "score": round(v["score"], 2),
            "count": v["count"]  # 添加出现次数
        }
        for v in sorted(keyword_scores.values(), key=lambda x: x["score"], reverse=True)
    ]
    
    # 提取其他信息
    years_required = extract_years_required(jd_text)
    degree_required = extract_degree_required(jd_text)
    certifications = extract_certifications(jd_text)
    
    # 确保must-have和nice-to-have不重复（双重保险）
    # 如果一个关键词同时出现在两个集合中：
    # 1. 如果它在"Bonus experience"区域出现，优先保留nice-to-have
    # 2. 否则，优先保留must-have
    # 但理论上不应该出现这种情况，因为上面的if-elif逻辑已经确保互斥
    # 这里作为最后的保险措施
    intersection = must_have_terms & nice_to_have_terms
    if intersection:
        # 检查这些重复的关键词，看它们是否在"Bonus experience"区域
        for term in intersection:
            # 如果这个关键词在"Bonus experience"区域出现，从must-have中移除
            term_positions = find_keyword_positions(jd_text, term)
            has_bonus = any(is_in_bonus_experience_section(jd_text, pos) for pos, _ in term_positions)
            if has_bonus:
                must_have_terms.discard(term)
            else:
                nice_to_have_terms.discard(term)
    
    # 最终确保没有重复
    nice_to_have_terms = nice_to_have_terms - must_have_terms
    
    # 过滤掉通用关键词（对分析没有实际价值）
    def should_filter_keyword(term: str) -> bool:
        """检查关键词是否应该被过滤"""
        if not term or len(term.strip()) == 0:
            return True
        
        term_lower = term.lower().strip()
        term_upper = term.upper().strip()
        
        # 检查是否完全匹配过滤列表（大小写不敏感）
        if term_lower in COMMON_KEYWORDS_TO_FILTER:
            return True
        
        # 检查大写形式（处理 "SEEK", "NZ", "CBD" 等全大写词）
        if term_upper in COMMON_KEYWORDS_TO_FILTER or term_upper.lower() in COMMON_KEYWORDS_TO_FILTER:
            return True
        
        # 检查是否以过滤词开头或结尾（处理复合词）
        # 例如："New Zealand" 应该被过滤，但 "New Zealand based" 可能不需要
        for filter_term in COMMON_KEYWORDS_TO_FILTER:
            # 完全匹配
            if term_lower == filter_term:
                return True
            # 如果关键词很短（<= 过滤词长度 + 3），且包含过滤词，则过滤
            # 这样可以过滤 "NZ", "CBD" 等，但保留 "NZ-based" 这样的复合词（如果它们存在）
            if len(term_lower) <= len(filter_term) + 3:
                if filter_term in term_lower:
                    return True
        
        # 特殊处理：过滤掉常见的2-3字母缩写（如果不是技术术语）
        if len(term_lower) <= 3:
            # 检查是否是已知的技术缩写（白名单）
            tech_short_acronyms = {'api', 'sql', 'xml', 'json', 'css', 'html', 'url', 'uri', 
                                   'aws', 'gcp', 'ci', 'cd', 'ui', 'ux', 'qa', 'sdk', 'ide', 
                                   'cli', 'ssh', 'tls', 'ssl', 'jwt', 'rpc', 'iot', 'ml', 'ai', 
                                   'etl', 'bi', 'crm', 'erp', 'dns', 'cdn', 'vpn', 'acl', 'iso',
                                   'tdd', 'bdd', 'ddd', 'k8s', 'pdf', 'csv', 'tsv', 'yaml'}
            if term_lower not in tech_short_acronyms:
                # 如果不在技术缩写白名单中，且是常见的地理/通用缩写，则过滤
                common_short = {'nz', 'au', 'us', 'uk', 'eu', 'cbd', 'hr', 'ceo', 'cto', 'cfo', 
                               'wfh', 'eoe', 'eeo', 'www', 'akl', 'wlg', 'chc', 'ham', 'dun', 'tau', 'it'}
                if term_lower in common_short:
                    return True
        
        # 过滤掉太短的关键词（少于2个字符，除非是技术缩写如 "C#"）
        if len(term_lower) < 2:
            return True
        
        # 过滤掉纯数字
        if term_lower.isdigit():
            return True
        
        # 过滤掉年份（4位数字，范围1900-2100）
        if term.isdigit() and len(term) == 4:
            year = int(term)
            if 1900 <= year <= 2100:
                return True
        
        # 过滤掉月份名称（全称和缩写）
        month_names = {
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'jan', 'feb', 'mar', 'apr', 'may', 'jun',
            'jul', 'aug', 'sep', 'sept', 'oct', 'nov', 'dec'
        }
        # 使用小写比较（term_lower已经转换为小写）
        if term_lower in month_names:
            return True
        
        # 过滤掉日期格式（如 01/01/2024, 2024-01-01, 01-01-2024）
        date_patterns = [
            r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$',  # 01/01/2024, 01-01-2024
            r'^\d{4}[/-]\d{1,2}[/-]\d{1,2}$',     # 2024-01-01, 2024/01/01
            r'^\d{1,2}\.\d{1,2}\.\d{2,4}$',      # 01.01.2024
        ]
        for pattern in date_patterns:
            if re.match(pattern, term):
                return True
        
        return False
    
    # 过滤keywords列表
    filtered_keywords = [
        kw for kw in keywords
        if not should_filter_keyword(kw["term"])
    ]
    
    # 过滤must-have和nice-to-have关键词
    filtered_must_have = [
        term for term in must_have_terms
        if not should_filter_keyword(term)
    ]
    
    filtered_nice_to_have = [
        term for term in nice_to_have_terms
        if not should_filter_keyword(term)
    ]
    
    return {
        "keywords": filtered_keywords,
        "must_have_keywords": sorted(filtered_must_have),
        "nice_to_have_keywords": sorted(filtered_nice_to_have),
        "years_required": years_required,
        "degree_required": degree_required,
        "certifications": certifications
    }


async def extract_and_save(
    job_id, 
    jd_text: str, 
    session,
    job_title: Optional[str] = None,
    company: Optional[str] = None,
    use_ai: bool = True
) -> None:
    """
    从JD文本中提取关键词并保存到数据库
    支持AI增强提取和规则提取的混合模式
    
    Args:
        job_id: 职位ID (UUID)
        jd_text: 职位描述文本
        session: SQLModel Session
        job_title: 职位标题（可选，用于AI提取）
        company: 公司名称（可选，用于AI提取）
        use_ai: 是否使用AI提取（默认True）
    """
    from sqlmodel import Session, select
    from app.models import Extraction, Job
    from datetime import datetime
    from uuid import UUID
    
    # 尝试使用AI增强提取
    try:
        from app.extractors.ai_enhanced_extractor import extract_keywords_hybrid
        
        extracted = await extract_keywords_hybrid(
            jd_text=jd_text,
            job_title=job_title,
            company=company,
            use_ai=use_ai
        )
        
        extraction_method = "ai-enhanced" if extracted.get("extraction_method") != "rule-based" else "rule-based"
        
        # 更新Job模型的角色族、资历级别和发布日期（无论使用AI还是规则提取）
        job = session.get(Job, job_id)
        if job:
            # 更新角色族（如果提取到了且不是unknown）
            if extracted.get("role_family") and extracted["role_family"] not in ["unknown", "other", "其他", None]:
                job.role_family = extracted["role_family"]
            
            # 更新资历级别（如果提取到了且不是unknown）
            if extracted.get("seniority") and extracted["seniority"] != "unknown":
                # 映射到Seniority枚举
                seniority_map = {
                    "graduate": "graduate",
                    "junior": "junior",
                    "intermediate": "mid",
                    "mid": "mid",
                    "senior": "senior",
                    "lead": "lead",
                    "architect": "architect",
                    "manager": "manager",
                    "principal": "principal",
                    "staff": "staff"
                }
                seniority_value = seniority_map.get(extracted["seniority"].lower())
                if seniority_value:
                    from app.models import Seniority
                    try:
                        job.seniority = Seniority(seniority_value)
                    except ValueError:
                        pass
            
            # 更新发布日期（如果提取到了且job还没有posted_date）
            if extracted.get("posted_date") and not job.posted_date:
                try:
                    posted_date_str = extracted.get("posted_date")
                    if isinstance(posted_date_str, str):
                        # 尝试解析日期字符串
                        posted_date = datetime.fromisoformat(posted_date_str.replace('Z', '+00:00'))
                        job.posted_date = posted_date
                except Exception as e:
                    print(f"解析提取的posted_date失败: {e}")
            
            session.add(job)
        
    except Exception as e:
        # 如果AI提取失败，回退到规则提取
        import traceback
        error_trace = traceback.format_exc()
        print(f"AI提取失败，回退到规则提取: {e}")
        print(f"错误详情: {error_trace}")
        extracted = extract_keywords(jd_text)
        extraction_method = "rule-based"
    
    # 转换为数据库格式
    # 处理keywords格式：AI返回的是字符串列表，规则提取返回的是字典列表
    try:
        keywords_raw = extracted.get("keywords", [])
        if keywords_raw and len(keywords_raw) > 0 and isinstance(keywords_raw[0], str):
            # AI格式：字符串列表
            keywords_list = keywords_raw
        else:
            # 规则格式：字典列表，提取term字段
            keywords_list = [kw["term"] if isinstance(kw, dict) else kw for kw in keywords_raw]
    except Exception as e:
        print(f"处理keywords时出错: {e}")
        keywords_list = []
    
    keywords_json = {"keywords": keywords_list}
    must_have_json = {"keywords": extracted.get("must_have_keywords", [])}
    nice_to_have_json = {"keywords": extracted.get("nice_to_have_keywords", [])}
    certifications_json = {"certifications": extracted.get("certifications", [])}
    
    # 检查是否已存在提取结果
    statement = select(Extraction).where(Extraction.job_id == job_id)
    existing_extraction = session.exec(statement).first()
    
    if existing_extraction:
        # 更新现有记录
        existing_extraction.keywords_json = keywords_json
        existing_extraction.must_have_json = must_have_json
        existing_extraction.nice_to_have_json = nice_to_have_json
        existing_extraction.years_required = extracted.get("years_required")
        existing_extraction.degree_required = extracted.get("degree_required")
        existing_extraction.certifications_json = certifications_json
        existing_extraction.summary = extracted.get("summary")
        existing_extraction.extraction_method = extraction_method
        existing_extraction.extracted_at = datetime.utcnow()
        session.add(existing_extraction)
    else:
        # 创建新记录
        extraction = Extraction(
            job_id=job_id,
            keywords_json=keywords_json,
            must_have_json=must_have_json,
            nice_to_have_json=nice_to_have_json,
            years_required=extracted.get("years_required"),
            degree_required=extracted.get("degree_required"),
            certifications_json=certifications_json,
            summary=extracted.get("summary"),
            extraction_method=extraction_method,
            extracted_at=datetime.utcnow()
        )
        session.add(extraction)
    
    session.commit()


def extract_and_save_sync(
    job_id, 
    jd_text: str, 
    session,
    job_title: Optional[str] = None,
    company: Optional[str] = None,
    use_ai: bool = True
) -> None:
    """
    同步包装器：从JD文本中提取关键词并保存到数据库
    在同步上下文中调用异步函数
    
    Args:
        job_id: 职位ID (UUID)
        jd_text: 职位描述文本
        session: SQLModel Session
        job_title: 职位标题（可选，用于AI提取）
        company: 公司名称（可选，用于AI提取）
        use_ai: 是否使用AI提取（默认True）
    """
    import asyncio
    
    # 尝试导入 nest_asyncio，如果未安装则跳过
    nest_asyncio_available = False
    try:
        import nest_asyncio
        nest_asyncio.apply()
        nest_asyncio_available = True
    except ImportError:
        # 如果没有 nest_asyncio，将使用其他方法
        pass
    
    try:
        # 检查是否有运行中的事件循环
        try:
            loop = asyncio.get_running_loop()
            # 如果有运行中的事件循环
            if nest_asyncio_available:
                # 使用 nest_asyncio 支持嵌套事件循环
                loop.run_until_complete(extract_and_save(
                    job_id, jd_text, session, job_title, company, use_ai
                ))
            else:
                # 如果没有 nest_asyncio，在新线程中运行
                import threading
                import queue
                result_queue = queue.Queue()
                exception_queue = queue.Queue()
                
                def run_async():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        result = new_loop.run_until_complete(extract_and_save(
                            job_id, jd_text, session, job_title, company, use_ai
                        ))
                        new_loop.close()
                        result_queue.put(result)
                    except Exception as e:
                        exception_queue.put(e)
                
                thread = threading.Thread(target=run_async)
                thread.start()
                thread.join()
                
                if not exception_queue.empty():
                    raise exception_queue.get()
        except RuntimeError:
            # 没有运行中的事件循环，直接使用 asyncio.run
            asyncio.run(extract_and_save(
                job_id, jd_text, session, job_title, company, use_ai
            ))
    except Exception as e:
        # 如果异步调用失败，回退到规则提取
        print(f"异步提取失败，回退到规则提取: {e}")
        import traceback
        traceback.print_exc()
        # 直接调用同步的规则提取
        try:
            extracted = extract_keywords(jd_text)
            extraction_method = "rule-based"
            
            # 转换为数据库格式
            keywords_list = [kw["term"] if isinstance(kw, dict) else kw for kw in extracted.get("keywords", [])]
            keywords_json = {"keywords": keywords_list}
            must_have_json = {"keywords": extracted.get("must_have_keywords", [])}
            nice_to_have_json = {"keywords": extracted.get("nice_to_have_keywords", [])}
            certifications_json = {"certifications": extracted.get("certifications", [])}
            
            # 保存到数据库
            from sqlmodel import select
            from app.models import Extraction
            from datetime import datetime
            
            try:
                statement = select(Extraction).where(Extraction.job_id == job_id)
                existing_extraction = session.exec(statement).first()
                
                if existing_extraction:
                    existing_extraction.keywords_json = keywords_json
                    existing_extraction.must_have_json = must_have_json
                    existing_extraction.nice_to_have_json = nice_to_have_json
                    existing_extraction.years_required = extracted.get("years_required")
                    existing_extraction.degree_required = extracted.get("degree_required")
                    existing_extraction.certifications_json = certifications_json
                    existing_extraction.summary = None
                    existing_extraction.extraction_method = extraction_method
                    existing_extraction.extracted_at = datetime.utcnow()
                    session.add(existing_extraction)
                else:
                    extraction = Extraction(
                        job_id=job_id,
                        keywords_json=keywords_json,
                        must_have_json=must_have_json,
                        nice_to_have_json=nice_to_have_json,
                        years_required=extracted.get("years_required"),
                        degree_required=extracted.get("degree_required"),
                        certifications_json=certifications_json,
                        summary=None,
                        extraction_method=extraction_method,
                        extracted_at=datetime.utcnow()
                    )
                    session.add(extraction)
                
                session.commit()
            except Exception as db_error:
                print(f"保存提取结果到数据库失败: {db_error}")
                import traceback
                traceback.print_exc()
                # 尝试回滚
                try:
                    session.rollback()
                except:
                    pass
                # 重新抛出异常，让调用者知道失败
                raise
        except Exception as fallback_error:
            print(f"规则提取也失败: {fallback_error}")
            import traceback
            traceback.print_exc()
            # 如果规则提取也失败，抛出异常
            raise