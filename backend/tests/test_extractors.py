"""提取器单元测试"""
import pytest
from app.extractors.keyword_extractor import extract_keywords


def test_extract_keywords_basic():
    """测试基本关键词提取"""
    jd_text = """
    We are looking for a Senior Python Developer with 5+ years of experience.
    Required skills: Python, Django, PostgreSQL, Docker.
    Preferred: AWS Certified, Kubernetes.
    Bachelor's degree in Computer Science required.
    """
    
    result = extract_keywords(jd_text)
    
    assert "keywords" in result
    assert "must_have_keywords" in result
    assert "nice_to_have_keywords" in result
    assert "years_required" in result
    assert "degree_required" in result
    assert "certifications" in result
    
    # 检查关键词提取
    keywords = result["keywords"]
    assert len(keywords) > 0
    assert any(k["term"] == "Python" for k in keywords)
    assert any(k["term"] == "Django" for k in keywords)
    
    # 检查年限提取
    assert result["years_required"] == 5
    
    # 检查学位提取
    assert result["degree_required"] is not None
    assert "Bachelor" in result["degree_required"] or "bachelor" in result["degree_required"].lower()


def test_extract_keywords_must_have_section():
    """测试must-have区域的关键词提取"""
    jd_text = """
    Job Title: Backend Engineer
    
    Requirements:
    - Python (3+ years)
    - FastAPI
    - PostgreSQL
    - Docker
    
    Nice to Have:
    - Kubernetes
    - AWS Certified
    """
    
    result = extract_keywords(jd_text)
    
    # 检查must-have关键词
    must_have = result["must_have_keywords"]
    assert len(must_have) > 0
    assert "Python" in must_have or any("Python" in k for k in must_have)
    
    # 检查nice-to-have关键词
    nice_to_have = result["nice_to_have_keywords"]
    assert len(nice_to_have) > 0


def test_extract_keywords_certifications():
    """测试证书提取"""
    jd_text = """
    We require:
    - AWS Certified Solutions Architect
    - ISTQB certification preferred
    - Kubernetes Certified (CKA) is a plus
    """
    
    result = extract_keywords(jd_text)
    
    # 检查证书提取
    certifications = result["certifications"]
    assert len(certifications) > 0
    assert any("AWS" in cert for cert in certifications)
    assert any("ISTQB" in cert for cert in certifications) or any("Kubernetes" in cert for cert in certifications)


def test_extract_keywords_years_required():
    """测试经验年限提取"""
    jd_text = """
    Position requires at least 3 years of experience in software development.
    Minimum of 5 years experience with Python preferred.
    """
    
    result = extract_keywords(jd_text)
    
    # 检查年限提取（应该提取最大值）
    assert result["years_required"] is not None
    assert result["years_required"] >= 3


def test_extract_keywords_alias_mapping():
    """测试别名映射到规范名称"""
    jd_text = """
    We need someone with:
    - Python3 experience
    - React.js knowledge
    - Node.js backend skills
    - AWS (Amazon Web Services) experience
    """
    
    result = extract_keywords(jd_text)
    
    # 检查别名映射
    keywords = result["keywords"]
    keyword_terms = [k["term"] for k in keywords]
    
    # Python3应该映射到Python
    assert "Python" in keyword_terms
    # React.js应该映射到React
    assert "React" in keyword_terms
    # Node.js应该映射到Node.js
    assert "Node.js" in keyword_terms
    # AWS应该被识别
    assert "AWS" in keyword_terms


def test_extract_keywords_score_calculation():
    """测试评分计算"""
    jd_text = """
    Required: Python, Python, Python (appears multiple times)
    Docker experience essential.
    """
    
    result = extract_keywords(jd_text)
    
    # 检查评分
    keywords = result["keywords"]
    python_keyword = next((k for k in keywords if k["term"] == "Python"), None)
    
    if python_keyword:
        # Python出现多次，应该有更高的分数
        assert python_keyword["score"] >= 3.0


def test_extract_keywords_empty_text():
    """测试空文本"""
    jd_text = ""
    
    result = extract_keywords(jd_text)
    
    assert result["keywords"] == []
    assert result["must_have_keywords"] == []
    assert result["nice_to_have_keywords"] == []
    assert result["years_required"] is None
    assert result["degree_required"] is None
    assert result["certifications"] == []


def test_extract_keywords_complex_jd():
    """测试复杂JD"""
    jd_text = """
    Senior Software Engineer
    
    We are looking for an experienced engineer with:
    
    Requirements:
    - 5+ years of experience with Python
    - Strong knowledge of Django and FastAPI
    - Experience with PostgreSQL and Redis
    - Docker and Kubernetes experience
    - Bachelor's degree in Computer Science or related field
    - AWS Certified Solutions Architect preferred
    
    Must Have:
    - Python, Django, PostgreSQL
    - REST API design
    - Git version control
    
    Nice to Have:
    - GraphQL
    - Microservices architecture
    - CI/CD pipelines
    - Kubernetes Certified (CKA)
    """
    
    result = extract_keywords(jd_text)
    
    # 验证基本结构
    assert "keywords" in result
    assert "must_have_keywords" in result
    assert "nice_to_have_keywords" in result
    
    # 验证年限
    assert result["years_required"] == 5
    
    # 验证学位
    assert result["degree_required"] is not None
    
    # 验证关键词
    keywords = result["keywords"]
    keyword_terms = [k["term"] for k in keywords]
    assert "Python" in keyword_terms
    assert "Django" in keyword_terms
    
    # 验证must-have
    must_have = result["must_have_keywords"]
    assert len(must_have) > 0
    
    # 验证证书
    certifications = result["certifications"]
    assert len(certifications) > 0