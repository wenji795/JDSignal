# 开始重新抓取职位数据

## ✅ 数据库已重置

数据库已删除并重新创建，现在可以开始抓取新数据。

## 📋 抓取步骤

### 1. 确保环境变量已设置

检查 `.env` 文件是否存在并包含 `AI_BUILDER_TOKEN`：

```bash
cd backend
cat .env
```

如果文件不存在，创建它：

```bash
cd backend
echo "AI_BUILDER_TOKEN=your_token_here" > .env
```

**重要**：将 `your_token_here` 替换为你的实际 AI Builder Token。请确保 `.env` 文件在 `.gitignore` 中，不要提交到版本控制。

### 2. 启动后端服务（终端1）

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

确保看到：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 3. 运行抓取脚本（终端2）

**快速测试（每个关键词5个职位）：**

```bash
cd backend
python scripts/reset_and_scrape.py --max-per-keyword 5 --headless
```

**完整抓取（每个关键词10个职位）：**

```bash
cd backend
python scripts/reset_and_scrape.py --max-per-keyword 10 --headless
```

**不使用无头模式（可以看到浏览器）：**

```bash
cd backend
python scripts/reset_and_scrape.py --max-per-keyword 5
```

### 4. 等待抓取完成

抓取过程可能需要一些时间，取决于：
- 关键词数量（默认20个）
- 每个关键词的职位数
- 网络速度

你会看到类似输出：
```
============================================================
开始抓取新西兰Seek上的IT职位数据
关键词数量: 20
每个关键词最多抓取: 5 个职位
预计最多抓取: 100 个职位
============================================================

处理关键词 1/20: software engineer
正在访问: https://www.seek.co.nz/job/...
✓ 完成关键词: software engineer
```

### 5. 验证AI提取结果

抓取完成后，检查提取结果：

```bash
cd backend
python -c "
from sqlmodel import Session, select, create_engine
from app.models import Job, Extraction
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_engine('sqlite:///./jobs.db')
with Session(engine) as session:
    jobs = session.exec(select(Job)).all()
    extractions = session.exec(select(Extraction)).all()
    
    print(f'职位总数: {len(jobs)}')
    print(f'提取结果总数: {len(extractions)}')
    
    ai_count = sum(1 for e in extractions if e.extraction_method == 'ai-enhanced')
    rule_count = sum(1 for e in extractions if e.extraction_method == 'rule-based')
    
    print(f'\n提取方法统计:')
    print(f'  AI增强提取: {ai_count} ({ai_count/len(extractions)*100:.1f}%)')
    print(f'  规则提取: {rule_count} ({rule_count/len(extractions)*100:.1f}%)')
    
    summaries = sum(1 for e in extractions if e.summary)
    print(f'\n有摘要的职位: {summaries}')
    
    # 显示前3个AI提取的职位
    ai_extractions = [e for e in extractions if e.extraction_method == 'ai-enhanced']
    if ai_extractions:
        print(f'\n前3个AI提取的职位摘要:')
        for i, ext in enumerate(ai_extractions[:3], 1):
            job = session.get(Job, ext.job_id)
            print(f'\n{i}. {job.title if job else \"Unknown\"}')
            print(f'   摘要: {ext.summary[:100] if ext.summary else \"无\"}...')
"
```

## 🎯 预期结果

如果一切正常，你应该看到：

1. **职位总数** > 0
2. **AI增强提取** > 0（如果设置了 AI_BUILDER_TOKEN）
3. **有摘要的职位** > 0
4. API 响应中 `extraction.extraction_method` 为 `"ai-enhanced"`

## ⚠️ 注意事项

1. **后端服务必须运行**：抓取脚本会调用后端API，所以必须先启动后端服务
2. **网络连接**：需要能够访问 seek.co.nz
3. **Playwright浏览器**：确保已安装 Playwright 浏览器驱动：
   ```bash
   playwright install firefox
   ```
4. **抓取速度**：为避免被封IP，脚本会在每个关键词之间等待5秒

## 🔍 查看结果

抓取完成后，可以通过以下方式查看：

1. **API文档**：访问 http://localhost:8000/docs
2. **职位列表**：调用 `GET /jobs`
3. **职位详情**：调用 `GET /jobs/{job_id}` 查看完整的提取结果

## 🐛 故障排除

### 抓取失败

- 检查后端服务是否运行
- 检查网络连接
- 检查 Playwright 是否已安装

### AI提取失败（显示 rule-based）

- 检查 `.env` 文件是否存在
- 检查 `AI_BUILDER_TOKEN` 是否正确
- 重启后端服务以加载新的环境变量

### 浏览器启动失败

```bash
playwright install firefox
# 或
playwright install chromium
```

## ✅ 完成！

抓取完成后，新的职位数据将使用 AI 增强提取功能，你会看到 `extraction_method: "ai-enhanced"` 和 `summary` 字段有内容。
