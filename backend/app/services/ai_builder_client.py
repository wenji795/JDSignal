"""AI Builder Space Backend API 客户端"""
import os
import httpx
from typing import Dict, List, Optional, Any
import json


class AIBuilderClient:
    """AI Builder Space Backend API 客户端"""
    
    BASE_URL = "https://space.ai-builders.com/backend/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            api_key: API密钥，如果不提供则从环境变量 AI_BUILDER_TOKEN 读取
        """
        self.api_key = api_key or os.getenv("AI_BUILDER_TOKEN")
        if not self.api_key:
            raise ValueError(
                "AI_BUILDER_TOKEN 未设置。请设置环境变量或在初始化时提供 api_key。"
            )
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "supermind-agent-v1",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用 Chat Completions API
        
        Args:
            messages: 消息列表，格式：[{"role": "user", "content": "..."}]
            model: 模型名称，默认 "supermind-agent-v1"
            temperature: 温度参数，默认 0.7
            max_tokens: 最大token数
            **kwargs: 其他参数
        
        Returns:
            API响应字典
        """
        url = f"{self.BASE_URL}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            **kwargs
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def create_embeddings(
        self,
        input_text: str | List[str],
        model: str = "text-embedding-3-small"
    ) -> Dict[str, Any]:
        """
        创建文本嵌入向量
        
        Args:
            input_text: 输入文本或文本列表
            model: 嵌入模型，默认 "text-embedding-3-small"
        
        Returns:
            API响应字典
        """
        url = f"{self.BASE_URL}/embeddings"
        
        payload = {
            "input": input_text,
            "model": model
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def web_search(
        self,
        keywords: List[str],
        max_results: int = 6
    ) -> Dict[str, Any]:
        """
        执行网络搜索
        
        Args:
            keywords: 搜索关键词列表
            max_results: 每个关键词的最大结果数，默认 6
        
        Returns:
            API响应字典
        """
        url = f"{self.BASE_URL}/search/"
        
        payload = {
            "keywords": keywords,
            "max_results": max_results
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()


# 全局客户端实例（懒加载）
_client_instance: Optional[AIBuilderClient] = None


def get_ai_builder_client() -> Optional[AIBuilderClient]:
    """
    获取全局 AI Builder 客户端实例
    
    Returns:
        AIBuilderClient 实例，如果未配置则返回 None
    """
    global _client_instance
    
    if _client_instance is None:
        try:
            _client_instance = AIBuilderClient()
        except ValueError:
            # 如果未配置 API key，返回 None（允许回退到规则提取）
            return None
    
    return _client_instance
