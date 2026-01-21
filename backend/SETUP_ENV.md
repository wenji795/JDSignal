# 设置 AI_BUILDER_TOKEN 环境变量

## 问题

当前数据库中的提取结果都是 `rule-based`，说明 AI 提取没有成功。原因是 `AI_BUILDER_TOKEN` 环境变量未设置。

## 解决方案

### 方法1：创建 .env 文件（推荐）

在 `backend` 目录下创建 `.env` 文件：

```bash
cd backend
echo "AI_BUILDER_TOKEN=sk_44cb1c79_94bae8042e317d3992f618e8d97242f378a5" > .env
```

**注意**：确保 `.env` 文件在 `.gitignore` 中，不要提交到版本控制。

### 方法2：在启动时设置环境变量

```bash
cd backend
export AI_BUILDER_TOKEN=sk_44cb1c79_94bae8042e317d3992f618e8d97242f378a5
uvicorn app.main:app --reload
```

### 方法3：修改代码支持从 .env 加载

如果还没有安装 `python-dotenv`，需要先安装：

```bash
pip install python-dotenv
```

然后在 `backend/app/main.py` 开头添加：

```python
from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件
```

## 验证设置

运行以下命令验证 token 是否设置成功：

```bash
cd backend
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('AI_BUILDER_TOKEN')
if token:
    print(f'✓ AI_BUILDER_TOKEN 已设置 (长度: {len(token)})')
else:
    print('✗ AI_BUILDER_TOKEN 未设置')
"
```

## 重新提取现有职位

设置好环境变量后，需要重新提取现有职位才能使用 AI 提取：

```bash
cd backend
python scripts/re_extract_keywords.py
```

或者删除数据库重新抓取：

```bash
cd backend
python scripts/reset_and_scrape.py --max-per-keyword 5 --headless
```

## 检查提取结果

设置完成后，检查提取结果：

```bash
cd backend
python -c "
from sqlmodel import Session, select, create_engine
from app.models import Extraction
from dotenv import load_dotenv
import os

load_dotenv()
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

如果看到 `AI增强提取` 数量大于 0，说明设置成功！
