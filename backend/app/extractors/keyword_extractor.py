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

# Must-have指示词
MUST_HAVE_INDICATORS = [
    r'\brequirements?\b', r'\bmust\s+have\b', r'\bessential\b',
    r'\bwe\s+require\b', r'\brequired\b', r'\bmandatory\b',
    r'\bqualifications?\b', r'\bneeded\b', r'\bnecessary\b'
]

# Nice-to-have指示词
NICE_TO_HAVE_INDICATORS = [
    r'\bnice\s+to\s+have\b', r'\bpreferred\b', r'\bbonus\b',
    r'\bdesirable\b', r'\badvantage\b', r'\bplus\b',
    r'\bwould\s+be\s+great\b', r'\boptional\b'
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
    pattern = r'\b' + re.escape(keyword) + r'\b'
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
            
            # 检查是否在标题中（前200字符）
            title_text = jd_text[:200].lower()
            if alias.lower() in title_text or canonical.lower() in title_text:
                title_bonus = 3.0  # 标题中的关键词权重很高
            
            for pos, _ in positions:
                if is_in_section(jd_text, pos, MUST_HAVE_INDICATORS):
                    must_have_bonus += 3.0  # must-have区域权重更高
                    must_have_terms.add(canonical)
                
                if is_in_section(jd_text, pos, NICE_TO_HAVE_INDICATORS):
                    nice_to_have_bonus += 1.5
                    nice_to_have_terms.add(canonical)
                
                if is_in_heading_or_bullet(jd_text, pos):
                    heading_bonus += 2.0  # 标题或列表项中的关键词权重更高
            
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
                title_bonus                     # 标题奖励
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
    
    return {
        "keywords": keywords,
        "must_have_keywords": sorted(list(must_have_terms)),
        "nice_to_have_keywords": sorted(list(nice_to_have_terms)),
        "years_required": years_required,
        "degree_required": degree_required,
        "certifications": certifications
    }


def extract_and_save(job_id, jd_text: str, session) -> None:
    """
    从JD文本中提取关键词并保存到数据库
    这是一个适配函数，将extract_keywords的输出转换为数据库格式
    
    Args:
        job_id: 职位ID (UUID)
        jd_text: 职位描述文本
        session: SQLModel Session
    """
    from sqlmodel import Session, select
    from app.models import Extraction
    from datetime import datetime
    from uuid import UUID
    
    # 提取关键词
    extracted = extract_keywords(jd_text)
    
    # 转换为数据库格式
    keywords_json = {"keywords": extracted["keywords"]}
    must_have_json = {"keywords": extracted["must_have_keywords"]}
    nice_to_have_json = {"keywords": extracted["nice_to_have_keywords"]}
    certifications_json = {"certifications": extracted["certifications"]}
    
    # 检查是否已存在提取结果
    statement = select(Extraction).where(Extraction.job_id == job_id)
    existing_extraction = session.exec(statement).first()
    
    if existing_extraction:
        # 更新现有记录
        existing_extraction.keywords_json = keywords_json
        existing_extraction.must_have_json = must_have_json
        existing_extraction.nice_to_have_json = nice_to_have_json
        existing_extraction.years_required = extracted["years_required"]
        existing_extraction.degree_required = extracted["degree_required"]
        existing_extraction.certifications_json = certifications_json
        existing_extraction.extracted_at = datetime.utcnow()
        session.add(existing_extraction)
    else:
        # 创建新记录
        extraction = Extraction(
            job_id=job_id,
            keywords_json=keywords_json,
            must_have_json=must_have_json,
            nice_to_have_json=nice_to_have_json,
            years_required=extracted["years_required"],
            degree_required=extracted["degree_required"],
            certifications_json=certifications_json,
            extracted_at=datetime.utcnow()
        )
        session.add(extraction)
    
    session.commit()