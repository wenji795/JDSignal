# Job JD Tracker & ATS Keyword Extractor

本地优先的职位JD追踪和ATS关键词提取系统。

## 快速开始

### 设置

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# 2. 安装依赖
pip install -r requirements.txt
```

### 运行服务

```bash
# 启动FastAPI服务（默认端口8000）
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用Makefile
make run
```

### 初始化数据

```bash
# 填充示例数据
cd backend
python scripts/seed.py

# 或使用Makefile
make seed
```

访问API文档：http://localhost:8000/docs

## 导出数据

```bash
# 导出到CSV（jobs + 关键词）
cd backend
python scripts/export_csv.py [output.csv]

# 导出到JSONL（原始JD + 提取结果）
python scripts/export_jsonl.py [output.jsonl]
```

## API端点

### 职位管理

#### 创建职位
```bash
# Direct模式（直接提供jd_text）
curl -X POST "http://localhost:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Developer",
    "company": "TechCorp",
    "jd_text": "We are looking for a Senior Python Developer with 5+ years of experience in Python, Django, and FastAPI.",
    "location": "San Francisco, CA",
    "role_family": "backend",
    "seniority": "senior"
  }'

# URL Capture模式（提供url和selected_text）
curl -X POST "http://localhost:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Full Stack Engineer",
    "company": "WebStart Inc",
    "url": "https://linkedin.com/jobs/67890",
    "selected_text": "We need a Full Stack Engineer with React and Node.js experience."
  }'
```

#### 列出职位（支持过滤）
```bash
# 列出所有职位
curl -X GET "http://localhost:8000/jobs"

# 按状态过滤
curl -X GET "http://localhost:8000/jobs?status=applied"

# 按角色族过滤
curl -X GET "http://localhost:8000/jobs?role_family=backend"

# 按资历级别过滤
curl -X GET "http://localhost:8000/jobs?seniority=senior"

# 关键词搜索
curl -X GET "http://localhost:8000/jobs?keyword=Python"
```

#### 获取特定职位
```bash
curl -X GET "http://localhost:8000/jobs/{job_id}"
```

#### 更新职位
```bash
curl -X PATCH "http://localhost:8000/jobs/{job_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Engineer",
    "status": "applied"
  }'
```

#### 获取提取结果
```bash
curl -X GET "http://localhost:8000/jobs/{job_id}/extraction"
```

### Chrome扩展捕获

```bash
curl -X POST "http://localhost:8000/capture" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "linkedin",
    "url": "https://linkedin.com/jobs/view/123456",
    "page_title": "Senior Python Developer at TechCorp",
    "company_guess": "TechCorp",
    "location_guess": "San Francisco, CA",
    "extracted_text": "We are looking for a Senior Python Developer with 5+ years of experience..."
  }'
```

### 趋势分析

```bash
# 获取趋势（默认30天）
curl -X GET "http://localhost:8000/analytics/trends"

# 自定义时间窗口
curl -X GET "http://localhost:8000/analytics/trends?days=60"

# 按角色族过滤
curl -X GET "http://localhost:8000/analytics/trends?role_family=backend"

# 按资历级别过滤
curl -X GET "http://localhost:8000/analytics/trends?seniority=senior"
```

## 数据模型

### Job字段
- `id` (UUID), `source`, `url`, `title`, `company`, `location`
- `posted_date`, `captured_at`, `jd_text`, `status`, `role_family`, `seniority`

### Extraction字段
- `job_id`, `keywords_json`, `must_have_json`, `nice_to_have_json`
- `years_required`, `degree_required`, `certifications_json`

## 测试

```bash
cd backend
pytest tests/ -v

# 或使用Makefile
make test
```

## 项目结构

```
backend/
├── app/
│   ├── main.py              # FastAPI应用
│   ├── models.py            # 数据模型
│   ├── schemas.py           # API schemas
│   ├── routers/
│   │   ├── jobs.py          # 职位端点
│   │   ├── capture.py       # Chrome扩展捕获端点
│   │   └── analytics.py     # 趋势分析端点
│   └── extractors/
│       ├── keyword_extractor.py  # 关键词提取
│       └── skill_dictionary.json # 技能字典
├── scripts/
│   ├── seed.py              # 种子数据
│   ├── export_csv.py        # CSV导出
│   └── export_jsonl.py      # JSONL导出
└── tests/                   # 测试
```

## 注意事项

- 数据库文件：`backend/jobs.db`（自动创建）
- CORS已配置：允许localhost和Chrome扩展
- 所有数据本地存储，不进行网络爬取
- 关键词提取在创建职位时自动运行