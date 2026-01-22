"""
AI优先的角色族和资历级别推断器
优先使用LLM判断，如果失败或返回unknown，则回退到规则推断
"""
from typing import Optional, Tuple
from app.models import Seniority
from app.extractors.role_inferrer import infer_role_family, infer_seniority
from app.services.ai_builder_client import get_ai_builder_client
import json
import re


async def infer_role_family_with_ai(
    title: str,
    jd_text: str = "",
    use_ai: bool = True
) -> Optional[str]:
    """
    使用AI优先推断角色族
    
    Args:
        title: 职位标题
        jd_text: 职位描述文本（可选）
        use_ai: 是否使用AI（默认True）
    
    Returns:
        角色族字符串，如 'testing', 'backend', 'frontend', 'ai' 等
    """
    # 如果启用AI，尝试使用AI推断
    if use_ai:
        ai_result = await _infer_with_ai(title, jd_text)
        if ai_result:
            role_family = ai_result.get("role_family")
            # 如果AI返回了有效的角色族（不是unknown），使用AI的结果
            if role_family and role_family not in ["unknown", "other", "其他", None]:
                return role_family
    
    # 回退到规则推断
    return infer_role_family(title, jd_text)


async def infer_seniority_with_ai(
    title: str,
    jd_text: str = "",
    use_ai: bool = True
) -> Optional[Seniority]:
    """
    使用AI优先推断资历级别
    
    Args:
        title: 职位标题
        jd_text: 职位描述文本（可选）
        use_ai: 是否使用AI（默认True）
    
    Returns:
        Seniority枚举值
    """
    # 如果启用AI，尝试使用AI推断
    if use_ai:
        ai_result = await _infer_with_ai(title, jd_text)
        if ai_result:
            seniority_str = ai_result.get("seniority")
            # 如果AI返回了有效的资历级别（不是unknown），使用AI的结果
            if seniority_str and seniority_str != "unknown":
                # 映射到Seniority枚举
                seniority_map = {
                    "graduate": Seniority.GRADUATE,
                    "junior": Seniority.JUNIOR,
                    "intermediate": Seniority.MID,
                    "mid": Seniority.MID,
                    "senior": Seniority.SENIOR,
                    "lead": Seniority.LEAD,
                    "architect": Seniority.ARCHITECT,
                    "manager": Seniority.MANAGER,
                    "principal": Seniority.PRINCIPAL,
                    "staff": Seniority.STAFF
                }
                seniority = seniority_map.get(seniority_str.lower())
                if seniority:
                    return seniority
    
    # 回退到规则推断
    return infer_seniority(title, jd_text)


async def infer_role_and_seniority_with_ai(
    title: str,
    jd_text: str = "",
    use_ai: bool = True
) -> Tuple[Optional[str], Optional[Seniority]]:
    """
    同时推断角色族和资历级别（AI优先）
    
    Args:
        title: 职位标题
        jd_text: 职位描述文本（可选）
        use_ai: 是否使用AI（默认True）
    
    Returns:
        (role_family, seniority) 元组
    """
    # 如果启用AI，尝试使用AI推断
    if use_ai:
        ai_result = await _infer_with_ai(title, jd_text)
        if ai_result:
            role_family = ai_result.get("role_family")
            seniority_str = ai_result.get("seniority")
            
            # 处理角色族
            final_role_family = None
            if role_family and role_family not in ["unknown", "other", "其他", None]:
                final_role_family = role_family
            else:
                # AI返回unknown，使用规则推断
                final_role_family = infer_role_family(title, jd_text)
            
            # 处理资历级别
            final_seniority = None
            if seniority_str and seniority_str != "unknown":
                seniority_map = {
                    "graduate": Seniority.GRADUATE,
                    "junior": Seniority.JUNIOR,
                    "intermediate": Seniority.MID,
                    "mid": Seniority.MID,
                    "senior": Seniority.SENIOR,
                    "lead": Seniority.LEAD,
                    "architect": Seniority.ARCHITECT,
                    "manager": Seniority.MANAGER,
                    "principal": Seniority.PRINCIPAL,
                    "staff": Seniority.STAFF
                }
                final_seniority = seniority_map.get(seniority_str.lower())
            
            # 如果AI没有返回有效的资历级别，使用规则推断
            if not final_seniority:
                final_seniority = infer_seniority(title, jd_text)
            
            return final_role_family, final_seniority
    
    # 如果AI未启用或失败，完全使用规则推断
    return infer_role_family(title, jd_text), infer_seniority(title, jd_text)


async def _infer_with_ai(title: str, jd_text: str = "") -> Optional[dict]:
    """
    使用AI推断角色族和资历级别（内部函数）
    
    Returns:
        包含 role_family 和 seniority 的字典，如果失败返回None
    """
    client = get_ai_builder_client()
    
    if not client:
        return None
    
    # 构建提示词
    system_prompt = """你是一个专业的IT职位分析专家。你的任务是分析职位标题和描述，推断角色族和资历级别。

请仔细分析职位信息，推断以下内容：

1. **角色族类型**：推断职位类型（fullstack, backend, frontend, devops, data, mobile, qa, security, testing, ai, business analyst, product manager, 其他, other）
2. **资历级别**：推断级别（graduate, junior, intermediate/mid, senior, lead, architect, manager, principal, staff, unknown）

请以JSON格式返回结果，格式如下：
{
    "role_family": "backend",
    "seniority": "intermediate"
}

注意：
- role_family 必须是以下之一：fullstack, backend, frontend, devops, data, mobile, qa, security, testing, ai, business analyst, product manager, 其他, other
- seniority 必须是以下之一：graduate, junior, intermediate, mid, senior, lead, architect, manager, principal, staff, unknown
- 如果信息不明确，使用 "unknown" 或 "其他"
- 只返回JSON，不要添加其他说明文字"""
    
    user_prompt = f"""请分析以下职位信息：

职位标题：{title}

职位描述：
{jd_text[:2000] if jd_text else "未提供"}

请推断角色族和资历级别，并以JSON格式返回。"""
    
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 调用 Chat Completions API
        response = await client.chat_completion(
            messages=messages,
            model="supermind-agent-v1",
            temperature=0.2,  # 较低温度以获得更一致的结果
            max_tokens=500
        )
        
        # 提取回复内容
        content = response["choices"][0]["message"]["content"]
        
        # 尝试从回复中提取JSON
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 如果没有代码块，尝试直接查找JSON对象
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                return None
        
        # 解析JSON
        result = json.loads(json_str)
        
        # 验证结果
        valid_role_families = {
            "fullstack", "backend", "frontend", "devops", "data", 
            "mobile", "qa", "security", "testing", "ai", "business analyst", 
            "product manager", "其他", "other", "unknown"
        }
        valid_seniorities = {
            "graduate", "junior", "intermediate", "mid", "senior", 
            "lead", "architect", "manager", "principal", "staff", "unknown"
        }
        
        role_family = result.get("role_family", "unknown")
        seniority = result.get("seniority", "unknown")
        
        # 验证并规范化
        if role_family not in valid_role_families:
            role_family = "unknown"
        if seniority not in valid_seniorities:
            seniority = "unknown"
        
        return {
            "role_family": role_family,
            "seniority": seniority
        }
        
    except Exception as e:
        # AI调用失败，返回None，让调用者使用规则推断
        print(f"AI推断失败: {str(e)}")
        return None
