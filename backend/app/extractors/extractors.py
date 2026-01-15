"""关键词提取器：技能、证书、学位、经验年限"""
import re
from typing import Set, Dict, Any, List
from collections import defaultdict


# 技能关键词字典
COMMON_SKILLS = {
    "python", "java", "javascript", "typescript", "react", "vue", "angular",
    "node.js", "django", "flask", "fastapi", "spring", "express",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "docker", "kubernetes", "aws", "azure", "gcp", "terraform",
    "git", "jenkins", "ci/cd", "agile", "scrum",
    "machine learning", "deep learning", "tensorflow", "pytorch",
    "rest api", "graphql", "microservices", "kafka",
    "html", "css", "sass", "less", "bootstrap", "tailwind",
    "linux", "unix", "bash", "shell scripting", "golang", "go", "rust",
    "c++", "c#", ".net", "ruby", "rails", "php", "laravel"
}

# 证书关键词
CERT_KEYWORDS = {
    "aws certified", "azure certified", "gcp certified",
    "pmp", "scrum master", "certified scrum master",
    "cissp", "cisco", "certified", "certification",
    "oracle certified", "microsoft certified", "aws solutions architect",
    "aws developer", "kubernetes certified"
}

# 学位关键词
DEGREE_KEYWORDS = {
    "bachelor", "master", "phd", "doctorate",
    "bs", "ms", "mba", "ph.d", "b.sc", "m.sc", "bachelor's",
    "master's", "ph.d.", "bachelor of science", "master of science"
}

# 经验年限正则模式
EXPERIENCE_PATTERNS = [
    r'(\d+)\+?\s*years?\s+of?\s+experience',
    r'(\d+)\+?\s*yrs?\s+of?\s+experience',
    r'experience.*?(\d+)\+?\s*years?',
    r'(\d+)\+?\s*years?\s+experience',
    r'minimum\s+of\s+(\d+)\s*years?',
    r'at\s+least\s+(\d+)\s*years?',
]


def extract_skills(text: str) -> Set[str]:
    """从文本中提取技能关键词"""
    text_lower = text.lower()
    found_skills = set()
    
    for skill in COMMON_SKILLS:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower, re.IGNORECASE):
            found_skills.add(skill)
    
    return found_skills


def extract_certifications(text: str) -> Set[str]:
    """从文本中提取证书关键词"""
    text_lower = text.lower()
    found_certs = set()
    
    for cert in CERT_KEYWORDS:
        pattern = r'\b' + re.escape(cert.lower()) + r'\b'
        if re.search(pattern, text_lower, re.IGNORECASE):
            found_certs.add(cert)
    
    return found_certs


def extract_degrees(text: str) -> Set[str]:
    """从文本中提取学位关键词"""
    text_lower = text.lower()
    found_degrees = set()
    
    for degree in DEGREE_KEYWORDS:
        pattern = r'\b' + re.escape(degree.lower()) + r'\b'
        if re.search(pattern, text_lower, re.IGNORECASE):
            found_degrees.add(degree)
    
    return found_degrees


def extract_experience_years(text: str) -> int:
    """从文本中提取经验年限（返回最大年限）"""
    text_lower = text.lower()
    found_years = []
    
    for pattern in EXPERIENCE_PATTERNS:
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            years = int(match.group(1))
            found_years.append(years)
    
    return max(found_years) if found_years else None


def extract_degree_required(text: str) -> str:
    """提取所需的学位"""
    degrees = extract_degrees(text)
    text_lower = text.lower()
    
    # 优先级：PhD > Master > Bachelor
    if any(d in text_lower for d in ["phd", "ph.d", "doctorate"]):
        return "PhD"
    elif any(d in text_lower for d in ["master", "mba", "ms"]):
        return "Master"
    elif any(d in text_lower for d in ["bachelor", "bs", "b.sc"]):
        return "Bachelor"
    
    return max(degrees, key=len).title() if degrees else None


def split_required_preferred(text: str) -> tuple:
    """
    尝试将JD文本分为required和preferred部分
    这是一个简化的实现，实际可以更复杂
    """
    text_lower = text.lower()
    
    # 查找常见分隔关键词
    required_indicators = ["required", "must have", "must", "need", "essential", "qualifications"]
    preferred_indicators = ["preferred", "nice to have", "bonus", "plus", "advantage"]
    
    # 简化实现：基于关键词密度分配
    required_text = text
    preferred_text = ""
    
    # 如果找到preferred部分，分割文本
    for indicator in preferred_indicators:
        if indicator in text_lower:
            parts = re.split(rf'\b{indicator}\b', text, flags=re.IGNORECASE)
            if len(parts) > 1:
                required_text = parts[0]
                preferred_text = " ".join(parts[1:])
                break
    
    return required_text, preferred_text


def extract_job_details(jd_text: str) -> Dict[str, Any]:
    """
    从JD文本中提取所有详细信息
    返回包含keywords_json, must_have_json, nice_to_have_json等的字典
    """
    # 提取所有技能
    all_skills = extract_skills(jd_text)
    all_certs = extract_certifications(jd_text)
    all_degrees = extract_degrees(jd_text)
    
    # 分割required和preferred部分
    required_text, preferred_text = split_required_preferred(jd_text)
    
    # 提取required部分的技能
    required_skills = extract_skills(required_text)
    required_certs = extract_certifications(required_text)
    
    # 提取preferred部分的技能
    preferred_skills = extract_skills(preferred_text) if preferred_text else set()
    preferred_certs = extract_certifications(preferred_text) if preferred_text else set()
    
    # 提取年限和学位
    years_required = extract_experience_years(required_text) or extract_experience_years(jd_text)
    degree_required = extract_degree_required(required_text) or extract_degree_required(jd_text)
    
    # 构建返回字典
    return {
        "keywords_json": {
            "skills": sorted(list(all_skills)),
            "certifications": sorted(list(all_certs)),
            "degrees": sorted(list(all_degrees)),
            "technologies": sorted(list(all_skills)),  # 技术栈
        },
        "must_have_json": {
            "skills": sorted(list(required_skills)),
            "certifications": sorted(list(required_certs)),
        },
        "nice_to_have_json": {
            "skills": sorted(list(preferred_skills)),
            "certifications": sorted(list(preferred_certs)),
        },
        "years_required": years_required,
        "degree_required": degree_required,
        "certifications_json": {
            "certifications": sorted(list(all_certs)),
        }
    }