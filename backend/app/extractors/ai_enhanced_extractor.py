"""AI 增强的关键词提取器 - 使用 Chat Completions API"""
import json
import re
from typing import Dict, List, Optional, Any
from app.services.ai_builder_client import get_ai_builder_client


async def extract_with_ai(
    jd_text: str,
    job_title: Optional[str] = None,
    company: Optional[str] = None
) -> Dict[str, Any]:
    """
    使用 AI 增强的关键词提取
    
    Args:
        jd_text: 职位描述文本
        job_title: 职位标题（可选）
        company: 公司名称（可选）
    
    Returns:
        包含提取结果的字典：
        {
            "keywords": [...],
            "must_have_keywords": [...],
            "nice_to_have_keywords": [...],
            "role_family": "fullstack" | "backend" | "frontend" | "devops" | ...,
            "seniority": "junior" | "intermediate" | "senior" | ...,
            "years_required": 3,
            "degree_required": "bachelor" | "master" | ...,
            "certifications": [...],
            "summary": "职位摘要文本",
            "success": True/False,
            "error": "错误信息（如果失败）"
        }
    """
    client = get_ai_builder_client()
    
    if not client:
        return {
            "success": False,
            "error": "AI Builder 客户端未配置（AI_BUILDER_TOKEN 未设置）"
        }
    
    # 构建提示词
    system_prompt = """你是一个专业的IT职位分析专家。你的任务是分析职位描述，提取关键信息并分类。

请仔细分析职位描述，提取以下信息：

1. **技术关键词**：提取所有提到的技术栈、工具、框架、语言等
2. **必须拥有的技能**：明确标注为"required"、"must have"、"essential"的技能
3. **加分项技能**：标注为"nice to have"、"preferred"、"bonus"的技能
4. **角色族类型**：推断职位类型（fullstack, backend, frontend, devops, data engineer, mobile, qa, security等）
5. **资历级别**：推断级别（graduate, junior, intermediate, senior, lead, architect等）
6. **经验年限**：提取所需工作经验年限（数字）
7. **学历要求**：提取学历要求（bachelor, master, phd等）
8. **证书要求**：提取认证要求（AWS Certified, Azure Certified等）
9. **职位摘要**：生成一个简洁的职位摘要（2-3句话）
10. **发布日期**：如果职位描述中包含发布日期信息（如"Posted 25d ago"、"Posted 21/01/2026"等），提取发布日期。日期格式应为ISO格式（YYYY-MM-DD）或null

请以JSON格式返回结果，格式如下：
{
    "keywords": ["Python", "FastAPI", "PostgreSQL", ...],
    "must_have_keywords": ["Python", "FastAPI", ...],
    "nice_to_have_keywords": ["Docker", "Kubernetes", ...],
    "role_family": "backend",
    "seniority": "intermediate",
    "years_required": 3,
    "degree_required": "bachelor",
    "certifications": ["AWS Certified Solutions Architect"],
    "summary": "这是一个中级后端开发职位，需要Python和FastAPI经验...",
    "posted_date": "2026-01-21" 或 null
}

注意：
- keywords 包含所有技术关键词
- must_have_keywords 和 nice_to_have_keywords 是 keywords 的子集
- role_family 必须是以下之一：fullstack, backend, frontend, devops, data, mobile, qa, security, testing, ai, business analyst, product manager, 其他, other
- seniority 必须是以下之一：graduate, junior, intermediate, senior, lead, architect, manager, unknown
- 如果信息不明确，使用 null 或 "unknown"
- summary 应该是2-3句话的简洁摘要，突出关键要求"""
    
    user_prompt = f"""请分析以下职位描述：

职位标题：{job_title or "未提供"}
公司：{company or "未提供"}

职位描述：
{jd_text}

请提取关键信息并以JSON格式返回。特别注意：如果职位描述中包含发布日期信息（如"Posted 25d ago"、"Posted 21/01/2026"、"Date posted: 2026-01-21"等），请提取并返回posted_date字段。"""
    
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 调用 Chat Completions API
        response = await client.chat_completion(
            messages=messages,
            model="supermind-agent-v1",
            temperature=0.3,  # 较低温度以获得更一致的结果
            max_tokens=2000
        )
        
        # 提取回复内容
        content = response["choices"][0]["message"]["content"]
        
        # 尝试从回复中提取JSON
        # 处理可能的markdown代码块
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 如果没有代码块，尝试直接查找JSON对象
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("无法从回复中提取JSON")
        
        # 解析JSON
        result = json.loads(json_str)
        
        # 验证和规范化结果
        result = _normalize_ai_result(result)
        
        return {
            **result,
            "success": True
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"AI提取失败: {str(e)}"
        }


def _normalize_ai_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    规范化AI返回的结果
    
    Args:
        result: AI返回的原始结果
    
    Returns:
        规范化后的结果
    """
    # 确保所有字段都存在
    normalized = {
        "keywords": result.get("keywords", []),
        "must_have_keywords": result.get("must_have_keywords", []),
        "nice_to_have_keywords": result.get("nice_to_have_keywords", []),
        "role_family": result.get("role_family", "unknown"),
        "seniority": result.get("seniority", "unknown"),
        "years_required": result.get("years_required"),
        "degree_required": result.get("degree_required"),
        "certifications": result.get("certifications", []),
        "summary": result.get("summary", ""),
        "posted_date": result.get("posted_date")  # 可以是字符串或null
    }
    
    # 如果posted_date是字符串，尝试解析并验证
    if normalized["posted_date"]:
        try:
            from datetime import datetime
            # 尝试解析日期字符串
            if isinstance(normalized["posted_date"], str):
                parsed_date = datetime.fromisoformat(normalized["posted_date"].replace('Z', '+00:00'))
                normalized["posted_date"] = parsed_date.strftime('%Y-%m-%d')
            else:
                normalized["posted_date"] = None
        except:
            normalized["posted_date"] = None
    
    # 验证 role_family
    valid_role_families = {
        "fullstack", "backend", "frontend", "devops", "data", 
        "mobile", "qa", "security", "testing", "ai", "business analyst", 
        "product manager", "其他", "other", "unknown"
    }
    if normalized["role_family"] not in valid_role_families:
        normalized["role_family"] = "unknown"
    
    # 验证 seniority
    valid_seniorities = {
        "graduate", "junior", "intermediate", "senior", 
        "lead", "architect", "manager", "unknown"
    }
    if normalized["seniority"] not in valid_seniorities:
        normalized["seniority"] = "unknown"
    
    # 确保列表类型
    for key in ["keywords", "must_have_keywords", "nice_to_have_keywords", "certifications"]:
        if not isinstance(normalized[key], list):
            normalized[key] = []
    
    # 去重并排序
    normalized["keywords"] = sorted(list(set(normalized["keywords"])))
    normalized["must_have_keywords"] = sorted(list(set(normalized["must_have_keywords"])))
    normalized["nice_to_have_keywords"] = sorted(list(set(normalized["nice_to_have_keywords"])))
    normalized["certifications"] = sorted(list(set(normalized["certifications"])))
    
    return normalized


async def extract_keywords_hybrid(
    jd_text: str,
    job_title: Optional[str] = None,
    company: Optional[str] = None,
    use_ai: bool = True
) -> Dict[str, Any]:
    """
    混合提取：优先使用AI，AI找不到的字段用代码逻辑兜底
    
    Args:
        jd_text: 职位描述文本
        job_title: 职位标题（可选）
        company: 公司名称（可选）
        use_ai: 是否使用AI提取（默认True）
    
    Returns:
        提取结果字典
    """
    # 初始化结果
    result = {
        "keywords": [],
        "must_have_keywords": [],
        "nice_to_have_keywords": [],
        "role_family": None,
        "seniority": None,
        "years_required": None,
        "degree_required": None,
        "certifications": [],
        "summary": "",
        "posted_date": None,
        "success": True,
        "extraction_method": "rule-based"
    }
    
    # 如果启用AI且客户端可用，尝试AI提取
    ai_result = None
    if use_ai:
        ai_result = await extract_with_ai(jd_text, job_title, company)
        
        if ai_result.get("success"):
            # AI提取成功，使用AI的结果
            result.update({
                "keywords": ai_result.get("keywords", []),
                "must_have_keywords": ai_result.get("must_have_keywords", []),
                "nice_to_have_keywords": ai_result.get("nice_to_have_keywords", []),
                "years_required": ai_result.get("years_required"),
                "degree_required": ai_result.get("degree_required"),
                "certifications": ai_result.get("certifications", []),
                "summary": ai_result.get("summary", ""),
                "extraction_method": "ai-enhanced"
            })
            
            # 角色族：AI优先，如果AI返回unknown/other/None，使用代码逻辑兜底
            ai_role_family = ai_result.get("role_family")
            if ai_role_family and ai_role_family not in ["unknown", "other", "其他", None]:
                result["role_family"] = ai_role_family
            else:
                # AI找不到，使用代码逻辑兜底
                from app.extractors.role_inferrer import infer_role_family
                fallback_role_family = infer_role_family(job_title or "", jd_text)
                result["role_family"] = fallback_role_family
            
            # 资历级别：AI优先，如果AI返回unknown/None，使用代码逻辑兜底
            ai_seniority = ai_result.get("seniority")
            if ai_seniority and ai_seniority != "unknown":
                result["seniority"] = ai_seniority
            else:
                # AI找不到，使用代码逻辑兜底
                from app.extractors.role_inferrer import infer_seniority
                from app.models import Seniority
                fallback_seniority = infer_seniority(job_title or "", jd_text)
                if fallback_seniority:
                    # 映射到字符串格式
                    seniority_map = {
                        Seniority.GRADUATE: "graduate",
                        Seniority.JUNIOR: "junior",
                        Seniority.MID: "intermediate",
                        Seniority.SENIOR: "senior",
                        Seniority.LEAD: "lead",
                        Seniority.ARCHITECT: "architect",
                        Seniority.MANAGER: "manager",
                        Seniority.PRINCIPAL: "principal",
                        Seniority.STAFF: "staff",
                        Seniority.UNKNOWN: "unknown"
                    }
                    result["seniority"] = seniority_map.get(fallback_seniority, "unknown")
            
            # 发布日期：AI优先，如果AI返回None，使用代码逻辑兜底
            ai_posted_date = ai_result.get("posted_date")
            if ai_posted_date:
                result["posted_date"] = ai_posted_date
            else:
                # AI找不到，使用代码逻辑兜底
                try:
                    from app.extractors.date_extractor import extract_posted_date_from_text
                    fallback_posted_date = extract_posted_date_from_text(jd_text)
                    if fallback_posted_date:
                        # 转换为字符串格式
                        if hasattr(fallback_posted_date, 'strftime'):
                            result["posted_date"] = fallback_posted_date.strftime('%Y-%m-%d')
                        else:
                            result["posted_date"] = str(fallback_posted_date)
                except Exception as e:
                    print(f"使用代码逻辑提取posted_date失败: {e}")
    
    # 如果AI提取失败或未启用AI，完全使用规则提取
    if not ai_result or not ai_result.get("success"):
        from app.extractors.keyword_extractor import extract_keywords
        from app.extractors.role_inferrer import infer_role_family, infer_seniority
        from app.models import Seniority
        
        rule_result = extract_keywords(jd_text)
        
        # 使用规则提取的结果
        result.update({
            "keywords": [kw["term"] for kw in rule_result.get("keywords", [])],
            "must_have_keywords": rule_result.get("must_have_keywords", []),
            "nice_to_have_keywords": rule_result.get("nice_to_have_keywords", []),
            "years_required": rule_result.get("years_required"),
            "degree_required": rule_result.get("degree_required"),
            "certifications": rule_result.get("certifications", []),
            "summary": "",
            "extraction_method": "rule-based"
        })
        
        # 使用代码逻辑推断角色族和资历级别
        if job_title:
            result["role_family"] = infer_role_family(job_title, jd_text)
            fallback_seniority = infer_seniority(job_title, jd_text)
            if fallback_seniority:
                seniority_map = {
                    Seniority.GRADUATE: "graduate",
                    Seniority.JUNIOR: "junior",
                    Seniority.MID: "intermediate",
                    Seniority.SENIOR: "senior",
                    Seniority.LEAD: "lead",
                    Seniority.ARCHITECT: "architect",
                    Seniority.MANAGER: "manager",
                    Seniority.PRINCIPAL: "principal",
                    Seniority.STAFF: "staff",
                    Seniority.UNKNOWN: "unknown"
                }
                result["seniority"] = seniority_map.get(fallback_seniority, "unknown")
        
        # 使用代码逻辑提取发布日期
        try:
            from app.extractors.date_extractor import extract_posted_date_from_text
            fallback_posted_date = extract_posted_date_from_text(jd_text)
            if fallback_posted_date:
                if hasattr(fallback_posted_date, 'strftime'):
                    result["posted_date"] = fallback_posted_date.strftime('%Y-%m-%d')
                else:
                    result["posted_date"] = str(fallback_posted_date)
        except Exception as e:
            print(f"使用代码逻辑提取posted_date失败: {e}")
    
    return result
