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
    
    # 全栈相关关键词（包括React Native，因为需要前后端知识）
    fullstack_title_keywords = [
        'full stack', 'fullstack', 'full-stack', 'full stack developer',
        'fullstack developer', 'full stack engineer', 'fullstack engineer',
        'react native developer'  # React Native通常需要全栈技能
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
    
    # 移动开发相关关键词（不包括React Native，因为React Native归类为全栈）
    mobile_title_keywords = [
        'mobile developer', 'ios developer', 'android developer',
        'flutter developer', 'mobile engineer'
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
    
    策略：
    1. 优先检查标题中的明确级别关键词（senior, junior, mid等）
    2. 如果标题不明确，提取JD中的经验年限要求
    3. 根据经验年限判断：0-2年=JUNIOR, 3-4年=MID, 5+年=SENIOR
    
    Args:
        title: 职位标题
        jd_text: 职位描述文本（可选）
    
    Returns:
        Seniority枚举值
    """
    # 合并标题和描述文本，转为小写进行匹配
    text = f"{title} {jd_text}".lower()
    title_lower = title.lower()
    
    # 排除词：如果标题中包含这些词，不应该被推断为高级别
    exclusion_keywords = ['assistant', 'coordinator', 'intern', 'trainee', 'junior', 'graduate']
    
    # 检查是否是assistant/coordinator等初级职位
    is_assistant_role = any(keyword in text for keyword in ['assistant', 'coordinator', 'intern', 'trainee'])
    
    # 第一步：检查标题中的明确级别关键词（优先级最高）
    # 注意：所有manager职位（包括assistant manager和senior manager）都应该标记为MANAGER
    # 注意：所有包含lead的职位都应该标记为LEAD
    # 注意：所有包含architect的职位都应该标记为ARCHITECT（优先级最高）
    
    # 检查architect职位（优先级最高，必须在其他检查之前）
    if 'architect' in title_lower:
        # 所有包含architect的职位都应该是ARCHITECT级别
        # 包括：solution architect, software architect, system architect, data architect等
        return Seniority.ARCHITECT
    
    # 检查manager职位（包括senior manager和assistant manager）
    if 'manager' in title_lower:
        # 所有manager职位都应该是MANAGER级别
        # 包括：senior manager, assistant manager, product manager, project manager等
        return Seniority.MANAGER
    
    # 检查lead职位（必须在manager检查之后，避免manager lead被误判）
    if 'lead' in title_lower:
        # 所有包含lead的职位都应该是LEAD级别
        # 包括：tech lead, team lead, engineering lead, product lead等
        return Seniority.LEAD
    
    if any(keyword in title_lower for keyword in ['principal', 'distinguished', 'fellow']):
        if not is_assistant_role:  # assistant不应该是principal
            return Seniority.PRINCIPAL
    
    if any(keyword in title_lower for keyword in ['head of', 'director']):
        # assistant/coordinator不应该被推断为lead
        if not is_assistant_role:
            return Seniority.LEAD
    
    if any(keyword in title_lower for keyword in ['staff', 'senior staff']):
        if not is_assistant_role:
            return Seniority.STAFF
    
    # 检查标题中的明确级别关键词（必须在manager检查之后，避免senior manager被误判）
    # 优先检查graduate（必须在junior之前）
    # 使用单词边界确保"graduate"或"grad"是独立的词，不是其他词的一部分
    if re.search(r'\bgraduate\b', title_lower) or re.search(r'\bgrad\b', title_lower):
        return Seniority.GRADUATE
    
    if any(keyword in title_lower for keyword in ['senior', 'sr.', 'sr ']):
        return Seniority.SENIOR
    
    if any(keyword in title_lower for keyword in ['mid', 'middle', 'intermediate']):
        return Seniority.MID
    
    # 只有标题中明确标注Junior才标记为JUNIOR
    # 注意：只在标题中检查，不在JD中检查，因为JD中的"intern"可能是其他含义（如"internship program"）
    if any(keyword in title_lower for keyword in ['junior', 'jr.', 'jr ', 'entry', 'intern']):
        return Seniority.JUNIOR
    
    # 第二步：检查JD中的经验年限要求（优先级最高，在graduate检查之前）
    # 如果JD中明确提到经验年限要求，应该优先根据经验年限判断，而不是graduate关键字
    jd_lower = jd_text.lower() if jd_text else ''
    
    # 提取所有经验年限要求
    experience_patterns = [
        r'(\d+)\+?\s*years?\s+of?\s+experience',
        r'(\d+)\+?\s*yrs?\s+of?\s+experience',
        r'minimum\s+of\s+(\d+)\+?\s*years?',
        r'at\s+least\s+(\d+)\+?\s*years?',
        r'(\d+)\+?\s*years?\s+experience',
        r'(\d+)[-–]\s*(\d+)\s*years?',  # 范围格式
    ]
    
    found_years = []
    for pattern in experience_patterns:
        matches = re.finditer(pattern, jd_lower, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) == 2:
                # 范围格式
                min_years = int(match.group(1))
                max_years = int(match.group(2))
                found_years.append(max(min_years, max_years))
            else:
                years = int(match.group(1))
                found_years.append(years)
    
    # 如果找到了经验年限要求，优先根据年限判断级别
    if found_years:
        max_years = max(found_years)
        # 如果明确要求5+年经验，应该是SENIOR，不应该被标记为Graduate
        if max_years >= 5:
            return Seniority.SENIOR
        elif max_years >= 3:
            return Seniority.MID
        elif max_years < 2:
            # 只有小于2年才标记为JUNIOR
            return Seniority.JUNIOR
        # 2-3年之间，继续后续检查
    
    # 检查明确的少于2年的经验要求
    # 注意：使用单词边界确保"0"是独立的数字，不是其他数字的一部分（如"160 years"）
    less_than_2_years_patterns = [
        r'less\s+than\s+2\s*years?',
        r'under\s+2\s*years?',
        r'<2\s*years?',
        r'\b0\s*years?\b',  # 使用单词边界，避免匹配"160 years"中的"0 years"
        r'\b1\s+year\b',  # 使用单词边界
    ]
    
    for pattern in less_than_2_years_patterns:
        if re.search(pattern, jd_lower, re.IGNORECASE):
            return Seniority.JUNIOR
    
    # 检查范围格式，如果最大值小于2年，标记为JUNIOR
    # 注意：先检查范围格式，避免"0-2 years"被误判（因为最大值是2，不是<2）
    range_pattern = r'(\d+)\s*[-–]\s*(\d+)\s*years?'
    range_matches = re.finditer(range_pattern, jd_lower, re.IGNORECASE)
    for match in range_matches:
        min_years = int(match.group(1))
        max_years = int(match.group(2))
        # 如果范围的最大值小于2年（不包括2年），标记为JUNIOR
        if max_years < 2:
            return Seniority.JUNIOR
    
    # 第三步：检查JD文本中的其他级别关键词
    # 注意：经验年限检查已经在第二步完成，如果JD中明确要求5+年经验，已经返回SENIOR
    # 优先检查graduate（必须在其他检查之前，但要在经验年限检查之后）
    # 使用单词边界和上下文检查，确保"graduate"或"grad"是作为职位级别出现的
    # 避免匹配"graduation"、"grading"、"grade"、"it graduate"等其他词
    graduate_patterns = [
        r'\bgraduate\s+(?:engineer|developer|programmer|analyst|designer|tester|specialist|role|position|job)',
        r'\bgrad\s+(?:engineer|developer|programmer|analyst|designer|tester|specialist|role|position|job)',
        r'(?:looking\s+for|seeking|hiring|recruiting)\s+(?:a\s+)?graduate\s+(?:engineer|developer|programmer|analyst|designer|tester|specialist|role|position|job)',
        r'graduate\s+(?:or|/)\s+(?:junior|entry)',
        # 注意：不使用单独的\bgraduate\b，因为可能匹配到"it graduate"等非职位级别上下文
    ]
    for pattern in graduate_patterns:
        if re.search(pattern, jd_lower, re.IGNORECASE):
            return Seniority.GRADUATE
    
    if any(keyword in jd_lower for keyword in ['senior', 'sr.', 'sr ', 'experienced', '5+ years', '5 years', '6+ years', '7+ years', '8+ years']):
        return Seniority.SENIOR
    
    if any(keyword in jd_lower for keyword in ['mid', 'middle', 'intermediate', '3+ years', '3 years', '4 years', '4+ years']):
        return Seniority.MID
    
    # 如果所有检查都没有匹配，返回UNKNOWN（资历不明）
    return Seniority.UNKNOWN


def infer_role_and_seniority(title: str, jd_text: str = "") -> Tuple[Optional[str], Optional[Seniority]]:
    """
    同时推断角色族和资历级别
    
    Returns:
        (role_family, seniority) 元组
    """
    role_family = infer_role_family(title, jd_text)
    seniority = infer_seniority(title, jd_text)
    return role_family, seniority
