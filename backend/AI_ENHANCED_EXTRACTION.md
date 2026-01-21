# AI 增强的关键词提取功能

## 概述

JDSignal 现在支持使用 AI Builder Space Backend 的 Chat Completions API 来增强关键词提取功能。AI 增强提取提供了以下优势：

1. **更智能的上下文理解**：使用 LLM 理解职位描述的语义，而非仅依赖规则
2. **更准确的分类**：更准确地区分"必须拥有"和"加分项"技能
3. **角色族推断**：自动从描述中推断角色类型（fullstack/devops/data engineer 等）
4. **资历级别推断**：自动推断资历级别（graduate/junior/intermediate/senior 等）
5. **职位摘要生成**：自动生成简洁的职位摘要（2-3句话）

## 配置

### 1. 设置 API Token

创建 `backend/.env` 文件并添加你的 AI Builder Token：

```bash
AI_BUILDER_TOKEN=your_token_here
```

**获取 Token 的方法：**
- 访问 https://space.ai-builders.com/explorer
- 登录后查看右上角的 "Authorize" 按钮
- 或者使用 MCP 工具 `get_auth_token` 获取

### 2. 安装依赖

确保已安装所有依赖：

```bash
pip install -r requirements.txt
```

新增的依赖：
- `nest-asyncio==1.6.0` - 用于在同步上下文中运行异步函数

## 使用方法

### 自动模式（默认）

系统会自动尝试使用 AI 增强提取，如果失败则回退到规则提取：

```python
from app.extractors.keyword_extractor import extract_and_save_sync

# 自动尝试 AI 提取，失败时回退到规则提取
extract_and_save_sync(
    job_id=job.id,
    jd_text=job.jd_text,
    session=session,
    job_title=job.title,
    company=job.company,
    use_ai=True  # 默认 True
)
```

### 仅使用规则提取

如果不想使用 AI 提取，可以设置 `use_ai=False`：

```python
extract_and_save_sync(
    job_id=job.id,
    jd_text=job.jd_text,
    session=session,
    use_ai=False  # 仅使用规则提取
)
```

## API 响应

提取结果现在包含以下新字段：

```json
{
  "extraction": {
    "keywords_json": {...},
    "must_have_json": {...},
    "nice_to_have_json": {...},
    "summary": "这是一个中级后端开发职位，需要Python和FastAPI经验...",
    "extraction_method": "ai-enhanced"  // 或 "rule-based"
  }
}
```

## 工作原理

### AI 增强提取流程

1. **调用 Chat Completions API**：使用 `supermind-agent-v1` 模型分析职位描述
2. **结构化提取**：AI 返回 JSON 格式的结构化数据，包括：
   - 技术关键词列表
   - 必须拥有和加分项技能
   - 角色族类型
   - 资历级别
   - 经验年限
   - 学历要求
   - 证书要求
   - 职位摘要
3. **数据验证和规范化**：验证 AI 返回的数据格式，确保符合系统要求
4. **自动更新 Job 模型**：如果 AI 提取成功，自动更新 Job 的 `role_family` 和 `seniority` 字段

### 回退机制

如果 AI 提取失败（例如 API 不可用、Token 未设置等），系统会自动回退到基于规则的关键词提取，确保系统始终可用。

## 性能考虑

- **API 调用延迟**：AI 提取需要调用外部 API，可能需要 2-5 秒
- **成本**：每次 AI 提取都会消耗 API Token，请合理使用
- **并发**：系统使用异步调用，支持并发处理多个提取请求

## 故障排除

### AI 提取失败

如果看到 `extraction_method: "rule-based"`，说明 AI 提取失败，已回退到规则提取。可能的原因：

1. **Token 未设置**：检查 `.env` 文件中的 `AI_BUILDER_TOKEN`
2. **Token 无效**：验证 Token 是否正确
3. **网络问题**：检查网络连接
4. **API 限制**：检查 API 使用限制

### 查看提取方法

在 API 响应中检查 `extraction_method` 字段：
- `"ai-enhanced"` - 成功使用 AI 提取
- `"rule-based"` - 使用规则提取（AI 提取失败或禁用）

## 未来改进

- [ ] 支持批量 AI 提取
- [ ] 添加提取结果缓存
- [ ] 支持自定义 AI 提示词
- [ ] 添加提取质量评分
- [ ] 支持多语言职位描述
