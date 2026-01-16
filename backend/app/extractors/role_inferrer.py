"""
从职位标题和描述中自动推断role_family和seniority
"""
import re
from typing import Optional, Tuple
from app.models import Seniority


def infer_role_family(title: str, jd_text: str = "") -> Optional[str]:
    """
    从职位标题和描述中推断角色族
    
    策略：
    1. 优先检查职位标题（更准确）
    2. 如果标题不明确，再检查JD文本
    3. 避免将JD中的技能关键词误判为职位类型
    
    Args:
        title: 职位标题
        jd_text: 职位描述文本（可选）
    
    Returns:
        角色族字符串，如 'testing', 'backend', 'frontend', 'ai' 等
    """
    title_lower = title.lower()
    jd_lower = jd_text.lower() if jd_text else ""
    
    # 软件测试相关关键词（必须在标题中明确出现，避免误判JD中的技能要求）
    testing_title_keywords = [
        'test engineer', 'qa engineer', 'quality assurance engineer', 'software tester',
        'test automation engineer', 'qa analyst', 'test specialist', 'qa specialist',
        'testing engineer', 'test lead', 'qa lead', 'test manager',
        'quality engineer', 'test developer', 'qa developer',
        'automation tester', 'manual tester', 'performance tester', 'security tester'
    ]
    
    # AI相关关键词
    ai_title_keywords = [
        'ai engineer', 'ai developer', 'artificial intelligence engineer',
        'machine learning engineer', 'ml engineer', 'ai researcher',
        'ai specialist', 'ml specialist', 'ai architect', 'ml architect'
    ]
    
    # 后端相关关键词（标题优先）
    backend_title_keywords = [
        'backend engineer', 'backend developer', 'back-end engineer', 'back-end developer',
        'server-side developer', 'api developer', 'server developer',
        'python developer', 'java developer', 'go developer', 'rust developer',
        'node.js developer', 'php developer', '.net developer', 'c# developer',
        'ruby developer', 'scala developer'
    ]
    
    # 前端相关关键词（标题优先）
    frontend_title_keywords = [
        'frontend engineer', 'frontend developer', 'front-end engineer', 'front-end developer',
        'ui developer', 'ux developer', 'ui engineer',
        'react developer', 'vue developer', 'angular developer',
        'javascript developer', 'typescript developer', 'web developer'
    ]
    
    # 全栈相关关键词
    fullstack_title_keywords = [
        'full stack', 'fullstack', 'full-stack', 'full stack developer',
        'fullstack developer', 'full stack engineer', 'fullstack engineer'
    ]
    
    # DevOps相关关键词
    devops_title_keywords = [
        'devops engineer', 'dev ops engineer', 'sre', 'site reliability engineer',
        'infrastructure engineer', 'cloud engineer', 'platform engineer'
    ]
    
    # 数据相关关键词
    data_title_keywords = [
        'data engineer', 'data scientist', 'data analyst', 'data architect'
    ]
    
    # 移动开发相关关键词
    mobile_title_keywords = [
        'mobile developer', 'ios developer', 'android developer',
        'react native developer', 'flutter developer', 'mobile engineer'
    ]
    
    # 通用开发岗位关键词（如果标题中有这些，优先判断为开发岗位）
    general_dev_keywords = [
        'software engineer', 'software developer', 'developer', 'programmer',
        'engineer', 'software', 'development'
    ]
    
    # 第一步：检查标题中的明确职位类型关键词（优先级最高）
    # 测试岗位（必须在标题中明确，避免误判JD中的技能要求）
    if any(keyword in title_lower for keyword in testing_title_keywords):
        return 'testing'
    
    # AI岗位
    if any(keyword in title_lower for keyword in ai_title_keywords):
        return 'ai'
    
    # 全栈岗位
    if any(keyword in title_lower for keyword in fullstack_title_keywords):
        return 'fullstack'
    
    # 后端岗位 - 统一归类为全栈
    if any(keyword in title_lower for keyword in backend_title_keywords):
        return 'fullstack'
    
    # 前端岗位 - 统一归类为全栈
    if any(keyword in title_lower for keyword in frontend_title_keywords):
        return 'fullstack'
    
    # DevOps岗位
    if any(keyword in title_lower for keyword in devops_title_keywords):
        return 'devops'
    
    # 数据岗位
    if any(keyword in title_lower for keyword in data_title_keywords):
        return 'data'
    
    # 移动开发岗位
    if any(keyword in title_lower for keyword in mobile_title_keywords):
        return 'mobile'
    
    # 第二步：如果标题中有通用开发关键词，根据JD中的技术栈推断
    if any(keyword in title_lower for keyword in general_dev_keywords):
        # 检查JD中的技术栈关键词（但排除测试相关的技能要求）
        # 后端技术栈
        backend_tech_keywords = ['backend', 'server-side', 'api', 'microservices', 'rest api', 'graphql',
                                 'python', 'java', 'go', 'rust', 'node.js', 'php', '.net', 'c#', 'ruby', 'scala']
        # 前端技术栈
        frontend_tech_keywords = ['frontend', 'front-end', 'client-side', 'ui', 'ux',
                                  'react', 'vue', 'angular', 'javascript', 'typescript', 'web']
        # 全栈技术栈
        fullstack_tech_keywords = ['full stack', 'fullstack']
        
        # 检查JD中的技术栈（但排除测试技能，避免误判）
        jd_tech_text = jd_lower
        # 移除测试相关的技能描述，避免误判
        test_skill_patterns = ['test automation', 'automation testing', 'integration testing', 
                               'performance testing', 'unit testing', 'end-to-end testing',
                               'testing experience', 'testing skills']
        for pattern in test_skill_patterns:
            jd_tech_text = jd_tech_text.replace(pattern, '')
        
        if any(keyword in jd_tech_text for keyword in fullstack_tech_keywords):
            return 'fullstack'
        elif any(keyword in jd_tech_text for keyword in backend_tech_keywords):
            return 'fullstack'  # 后端统一归类为全栈
        elif any(keyword in jd_tech_text for keyword in frontend_tech_keywords):
            return 'fullstack'  # 前端统一归类为全栈
        else:
            # 默认推断为全栈
            return 'fullstack'
    
    # 第三步：如果标题不明确，检查JD文本（但降低优先级）
    # 只在标题完全没有线索时才使用JD文本
    if not any(keyword in title_lower for keyword in general_dev_keywords + testing_title_keywords + 
               ai_title_keywords + backend_title_keywords + frontend_title_keywords + 
               fullstack_title_keywords + devops_title_keywords + data_title_keywords + mobile_title_keywords):
        
        # 检查JD中的关键词（但要求更严格）
        if any(keyword in jd_lower for keyword in testing_title_keywords):
            return 'testing'
        if any(keyword in jd_lower for keyword in ai_title_keywords):
            return 'ai'
        if any(keyword in jd_lower for keyword in fullstack_title_keywords):
            return 'fullstack'
        if any(keyword in jd_lower for keyword in backend_title_keywords):
            return 'fullstack'  # 后端统一归类为全栈
        if any(keyword in jd_lower for keyword in frontend_title_keywords):
            return 'fullstack'  # 前端统一归类为全栈
        if any(keyword in jd_lower for keyword in devops_title_keywords):
            return 'devops'
        if any(keyword in jd_lower for keyword in data_title_keywords):
            return 'data'
        if any(keyword in jd_lower for keyword in mobile_title_keywords):
            return 'mobile'
    
    return None


def infer_seniority(title: str, jd_text: str = "") -> Optional[Seniority]:
    """
    从职位标题和描述中推断资历级别
    
    Args:
        title: 职位标题
        jd_text: 职位描述文本（可选）
    
    Returns:
        Seniority枚举值
    """
    # 合并标题和描述文本，转为小写进行匹配
    text = f"{title} {jd_text}".lower()
    
    # 排除词：如果标题中包含这些词，不应该被推断为高级别
    exclusion_keywords = ['assistant', 'coordinator', 'intern', 'trainee', 'junior', 'graduate']
    
    # 检查是否是assistant/coordinator等初级职位
    is_assistant_role = any(keyword in text for keyword in ['assistant', 'coordinator', 'intern', 'trainee'])
    
    # 检查资历级别关键词（按从高到低的顺序）
    # 注意：assistant/coordinator等职位不应该被推断为manager/lead
    if any(keyword in text for keyword in ['principal', 'architect', 'distinguished', 'fellow']):
        if not is_assistant_role:  # assistant不应该是principal
            return Seniority.PRINCIPAL
    
    if any(keyword in text for keyword in ['lead', 'head of', 'director']):
        # assistant/coordinator不应该被推断为lead
        if not is_assistant_role:
            return Seniority.LEAD
    
    # manager关键词需要更严格的检查
    if 'manager' in text:
        # 排除assistant manager, office manager等（这些可能是初级职位）
        # 但保留engineering manager, product manager等（这些是高级职位）
        if is_assistant_role:
            # assistant manager通常是初级职位
            return Seniority.JUNIOR
        # 检查是否是真正的管理职位
        manager_contexts = ['engineering manager', 'product manager', 'project manager', 
                           'development manager', 'technical manager', 'team manager',
                           'engineering manager', 'software manager', 'it manager']
        if any(context in text for context in manager_contexts):
            return Seniority.MANAGER
        # 如果只是单独的manager，且不是assistant，可能是lead级别
        return Seniority.LEAD
    
    if any(keyword in text for keyword in ['staff', 'senior staff']):
        if not is_assistant_role:
            return Seniority.STAFF
    
    if any(keyword in text for keyword in ['senior', 'sr.', 'sr ', 'experienced', '5+ years', '5 years', '6+ years', '7+ years', '8+ years']):
        return Seniority.SENIOR
    
    # 中级：intermediate, mid等
    if any(keyword in text for keyword in ['mid', 'middle', 'intermediate', '3+ years', '3 years', '4 years', '4+ years']):
        return Seniority.MID
    
    # 初级：junior, graduate, entry等
    if any(keyword in text for keyword in ['junior', 'jr.', 'jr ', 'entry', 'graduate', 'intern', '0-2 years', '1-2 years', '2 years']):
        return Seniority.JUNIOR
    
    # 如果标题包含assistant/coordinator但没有明确的资历级别，默认为junior
    if is_assistant_role:
        return Seniority.JUNIOR
    
    return None


def infer_role_and_seniority(title: str, jd_text: str = "") -> Tuple[Optional[str], Optional[Seniority]]:
    """
    同时推断角色族和资历级别
    
    Returns:
        (role_family, seniority) 元组
    """
    role_family = infer_role_family(title, jd_text)
    seniority = infer_seniority(title, jd_text)
    return role_family, seniority
