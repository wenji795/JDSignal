# 重置数据库并测试 AI 增强提取功能

## ✅ 数据库已重置

数据库文件已删除并重新创建。现在可以开始重新抓取数据来测试 AI 增强提取功能。

## 📋 步骤

### 1. 设置环境变量（如果还没有）

创建 `backend/.env` 文件并添加你的 AI Builder Token：

```bash
cd backend
echo "AI_BUILDER_TOKEN=your_token_here" > .env
```

**获取 Token：**
- 访问 https://space.ai-builders.com/explorer
- 登录后查看右上角的 "Authorize" 按钮
- 或者使用 MCP 工具 `get_auth_token` 获取

### 2. 启动后端服务

在终端1中启动后端服务：

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

确保服务正常运行，你应该看到类似输出：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. 运行抓取脚本

在终端2中运行抓取脚本：

```bash
cd backend
python scripts/reset_and_scrape.py --max-per-keyword 5 --headless
```

**参数说明：**
- `--max-per-keyword 5`: 每个关键词最多抓取5个职位（用于快速测试）
- `--headless`: 使用无头模式（不显示浏览器窗口）
- `--browser firefox`: 指定浏览器引擎（默认firefox）

**完整抓取（更多数据）：**
```bash
python scripts/reset_and_scrape.py --max-per-keyword 10 --headless
```

### 4. 验证 AI 提取结果

抓取完成后，可以通过以下方式验证：

#### 方法1：使用 API 文档

访问 http://localhost:8000/docs

1. 调用 `GET /jobs` 查看所有职位
2. 选择一个职位ID
3. 调用 `GET /jobs/{job_id}` 查看职位详情
4. 检查 `extraction` 字段：
   - `extraction_method`: 应该是 `"ai-enhanced"` 或 `"rule-based"`
   - `summary`: 如果使用AI提取，应该有职位摘要
   - `keywords_json`: 包含提取的关键词

#### 方法2：使用 curl

```bash
# 获取所有职位
curl http://localhost:8000/jobs | jq '.[0].extraction.extraction_method'

# 获取特定职位的详细信息
curl http://localhost:8000/jobs/{job_id} | jq '.extraction'
```

#### 方法3：检查数据库

```bash
cd backend
python -c "
from sqlmodel import Session, select, create_engine
from app.models import Extraction
engine = create_engine('sqlite:///./jobs.db')
with Session(engine) as session:
    extractions = session.exec(select(Extraction)).all()
    ai_count = sum(1 for e in extractions if e.extraction_method == 'ai-enhanced')
    rule_count = sum(1 for e in extractions if e.extraction_method == 'rule-based')
    print(f'AI增强提取: {ai_count}')
    print(f'规则提取: {rule_count}')
    print(f'总计: {len(extractions)}')
"
```

## 🔍 预期结果

### AI 增强提取成功时

```json
{
  "extraction": {
    "extraction_method": "ai-enhanced",
    "summary": "这是一个中级后端开发职位，需要Python和FastAPI经验...",
    "keywords_json": {
      "keywords": ["Python", "FastAPI", "PostgreSQL", ...]
    },
    "must_have_json": {
      "keywords": ["Python", "FastAPI", ...]
    },
    "nice_to_have_json": {
      "keywords": ["Docker", "Kubernetes", ...]
    }
  },
  "role_family": "backend",
  "seniority": "mid"
}
```

### 回退到规则提取时

```json
{
  "extraction": {
    "extraction_method": "rule-based",
    "summary": null,
    "keywords_json": {
      "keywords": [...]
    }
  }
}
```

## ⚠️ 故障排除

### AI 提取失败（显示 rule-based）

1. **检查环境变量**：
   ```bash
   cd backend
   cat .env | grep AI_BUILDER_TOKEN
   ```

2. **检查后端日志**：查看是否有错误信息

3. **手动测试 API**：
   ```bash
   curl -X POST http://localhost:8000/manual-job \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Test Job",
       "company": "Test Company",
       "jd_text": "We need a Python developer with FastAPI experience."
     }'
   ```

### 抓取失败

1. **确保后端服务正在运行**
2. **检查网络连接**
3. **检查 Playwright 浏览器是否已安装**：
   ```bash
   playwright install firefox
   ```

## 📊 统计信息

抓取完成后，可以运行以下脚本查看统计：

```bash
cd backend
python -c "
from sqlmodel import Session, select, create_engine
from app.models import Job, Extraction
engine = create_engine('sqlite:///./jobs.db')
with Session(engine) as session:
    jobs = session.exec(select(Job)).all()
    extractions = session.exec(select(Extraction)).all()
    
    print(f'职位总数: {len(jobs)}')
    print(f'提取结果总数: {len(extractions)}')
    
    ai_extractions = [e for e in extractions if e.extraction_method == 'ai-enhanced']
    rule_extractions = [e for e in extractions if e.extraction_method == 'rule-based']
    
    print(f'AI增强提取: {len(ai_extractions)} ({len(ai_extractions)/len(extractions)*100:.1f}%)')
    print(f'规则提取: {len(rule_extractions)} ({len(rule_extractions)/len(extractions)*100:.1f}%)')
    
    summaries = [e for e in extractions if e.summary]
    print(f'有摘要的职位: {len(summaries)}')
"
```

## 🎉 完成！

如果看到 `extraction_method: "ai-enhanced"` 和 `summary` 字段有内容，说明 AI 增强提取功能正常工作！
