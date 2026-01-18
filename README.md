# JDSignal - 新西兰IT职位市场分析与关键词提取系统

一个智能化的职位描述（JD）追踪和分析系统，专注于新西兰IT职位市场。系统能够自动抓取Seek NZ职位信息、智能提取和分类关键词、分析市场趋势，帮助求职者和招聘方更好地理解市场需求。

## 🆕 最新功能

- ✅ **月度关键词对比**：自动对比上月和本月的关键词变化，显示Top 7总体变化和Top 5角色族变化
- ✅ **关键词规范化**：自动合并CI/CD、.NET等变体关键词，避免重复统计
- ✅ **智能过滤**：自动过滤通用词、日期、月份等无意义关键词
- ✅ **仅支持Seek NZ**：专注于新西兰市场，自动过滤非新西兰职位

## ✨ 主要功能

### 🎯 核心特性

- **智能关键词提取**：自动从职位描述中提取技术关键词，并智能分类为"必须拥有"和"加分项"
- **自动职位抓取**：支持从Seek NZ自动抓取最新职位信息（使用Playwright）
- **增量抓取与去重**：自动检测重复职位，只保存新职位，避免数据冗余
- **定时任务**：每小时自动抓取最新职位（使用APScheduler）
- **角色与资历推断**：自动从职位标题和描述中推断角色族（fullstack/devops等）和资历级别
- **趋势分析**：提供关键词趋势、角色分布、资历分布等可视化分析
- **手动添加职位**：支持手动输入职位描述文本，快速添加到系统

### 📊 关键词提取能力

- **智能分类**：基于上下文分析，准确区分"必须拥有"和"加分项"技能
- **技能字典**：内置丰富的IT技能字典，支持别名识别（如C#、JavaScript、React等）
- **动态提取**：对于不在字典中的关键词，通过上下文智能推断类别
- **证书识别**：自动识别AWS、Azure、GCP等各类技术认证
- **学历要求**：提取学士、硕士、博士等学历要求
- **经验年限**：提取所需工作经验年限

## 🛠️ 技术栈

### 后端
- **FastAPI** - 现代Python Web框架
- **SQLModel** - 基于SQLAlchemy的ORM
- **Playwright** - 浏览器自动化，用于网页抓取
- **APScheduler** - 定时任务调度
- **Pydantic** - 数据验证

### 前端
- **Next.js 14** - React框架（App Router）
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式框架
- **Recharts** - 数据可视化

### 数据库
- **SQLite** - 轻量级数据库（默认）

## 📦 安装与运行

### 前置要求

- Python 3.9+
- Node.js 18+
- npm 或 yarn

### 1. 克隆项目

```bash
git clone <repository-url>
cd JDSignal
```

### 2. 后端设置

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 安装Python依赖
pip install -r requirements.txt

# 安装Playwright浏览器驱动（用于网页抓取）
playwright install firefox
# 或
playwright install chromium
```

### 3. 前端设置

```bash
cd frontend
npm install
```

### 4. 启动服务

**启动后端（终端1）：**

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端将在 http://127.0.0.1:8000 启动

**启动前端（终端2）：**

```bash
cd frontend
npm run dev
```

前端将在 http://localhost:3000 启动

### 5. 初始化数据（可选）

如果需要示例数据来测试：

```bash
cd backend
python scripts/seed.py
```

## 🚀 使用指南

### Web界面

访问 http://localhost:3000 使用Web界面：

1. **首页** (`/`)
   - 查看系统概览
   - 手动触发职位抓取
   - 快速导航到各个功能页面

2. **职位列表** (`/jobs`)
   - 浏览所有职位
   - 按角色族（fullstack）和资历级别（graduate/junior/intermediate/senior）过滤
   - 按关键词搜索
   - 点击职位查看详细信息
   - 自动每30秒刷新，或手动点击刷新按钮

3. **职位详情** (`/jobs/[id]`)
   - 查看完整的职位信息
   - 查看提取的关键词（按类别分组）
   - 查看必须拥有和加分项技能
   - 查看证书和学历要求

4. **趋势分析** (`/trends`)
   - 查看总体职位统计
   - 角色族分布（饼图，颜色与标签一致）
   - 资历级别分布（饼图，颜色与标签一致）
   - Top 20关键词（柱状图，自动过滤通用词、日期、月份）
   - 按角色族查看Top 20关键词
   - **上月vs本月关键词对比**：
     - 总体Top 7变化最大的关键词
     - 各角色族Top 5变化最大的关键词
     - 显示变化量、变化率和状态（新增/增长/下降/不变）

5. **手动添加职位** (`/manual-job`)
   - 输入职位标题、公司、地点、URL
   - 粘贴职位描述文本
   - 系统自动提取关键词并保存

### API使用

访问 http://127.0.0.1:8000/docs 查看完整的API文档（Swagger UI）

#### 主要API端点

**职位管理**
- `GET /jobs` - 获取职位列表（支持过滤）
- `GET /jobs/{id}` - 获取职位详情
- `POST /jobs` - 创建新职位
- `PATCH /jobs/{id}` - 更新职位
- `GET /jobs/{id}/extraction` - 获取关键词提取结果

**职位抓取**
- `POST /scraper/trigger` - 手动触发职位抓取（仅支持Seek NZ）
- `POST /capture` - 捕获职位信息（用于Chrome扩展）

**手动添加**
- `POST /manual-job` - 手动提交职位描述

**趋势分析**
- `GET /analytics/trends` - 获取趋势分析数据
  - 支持按角色族、资历级别、地点过滤
  - 返回总体Top 30关键词、各角色族Top 20关键词
  - 返回上月vs本月对比（总体Top 7、各角色族Top 5）

#### API示例

```bash
# 获取所有职位
curl http://127.0.0.1:8000/jobs

# 按角色族过滤
curl "http://127.0.0.1:8000/jobs?role_family=fullstack"

# 手动触发抓取
curl -X POST http://127.0.0.1:8000/scraper/trigger

# 获取趋势分析
curl http://127.0.0.1:8000/analytics/trends
```

### 定时抓取

系统启动后会自动配置定时任务，每小时整点自动抓取最新职位。如果需要禁用定时任务，可以在 `backend/app/main.py` 中注释掉相关代码。

## 📁 项目结构

```
JDSignal/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── main.py            # FastAPI应用入口
│   │   ├── database.py       # 数据库配置
│   │   ├── models.py         # 数据模型
│   │   ├── schemas.py        # API数据模式
│   │   ├── routers/          # API路由
│   │   │   ├── jobs.py       # 职位管理端点
│   │   │   ├── capture.py    # 职位捕获端点
│   │   │   ├── analytics.py  # 趋势分析端点
│   │   │   ├── manual_job.py # 手动添加端点
│   │   │   └── scraper.py    # 抓取控制端点
│   │   ├── extractors/       # 关键词提取模块
│   │   │   ├── keyword_extractor.py  # 核心提取逻辑
│   │   │   ├── dynamic_extractor.py  # 动态关键词提取
│   │   │   ├── role_inferrer.py      # 角色推断
│   │   │   └── skill_dictionary.json # 技能字典
│   │   └── services/         # 服务层
│   │       ├── scraper_service.py    # 抓取服务
│   │       └── scheduler_service.py  # 定时任务服务
│   ├── scripts/              # 工具脚本
│   │   ├── scrape_jobs.py   # Seek职位抓取脚本
│   │   ├── scrape_nz_jobs.py # 新西兰职位抓取脚本
│   │   ├── seed.py          # 种子数据
│   │   ├── export_csv.py    # CSV导出
│   │   ├── export_jsonl.py  # JSONL导出
│   │   ├── re_extract_keywords.py  # 重新提取关键词脚本
│   │   └── clean_non_nz_jobs.py    # 清理非新西兰职位脚本
│   ├── tests/               # 测试代码
│   ├── jobs.db             # SQLite数据库（自动创建）
│   └── requirements.txt    # Python依赖
│
├── frontend/                # 前端代码
│   ├── app/                # Next.js App Router
│   │   ├── page.tsx       # 首页
│   │   ├── jobs/          # 职位相关页面
│   │   ├── trends/        # 趋势分析页面
│   │   └── manual-job/    # 手动添加页面
│   ├── lib/
│   │   └── api.ts         # API客户端
│   └── package.json       # Node.js依赖
│
├── requirements.txt        # Python依赖（根目录）
└── README.md              # 本文档
```

## 🔧 配置说明

### 数据库

默认使用SQLite数据库，文件位置：`backend/jobs.db`

如需使用其他数据库（如PostgreSQL），修改 `backend/app/database.py` 中的连接字符串。

### 抓取配置

抓取相关的配置在 `backend/app/services/scraper_service.py` 中：

- `NZ_IT_KEYWORDS` - 搜索关键词列表
- `max_per_keyword` - 每个关键词最多抓取的职位数
- `headless` - 是否使用无头模式

**注意**：系统仅支持Seek NZ（seek.co.nz）的职位抓取，自动过滤非新西兰职位。

### 定时任务

定时任务配置在 `backend/app/services/scheduler_service.py` 中：

- 默认每小时整点执行一次
- 可通过修改 `CronTrigger` 调整执行频率

## 📊 数据导出

### 导出为CSV

```bash
cd backend
python scripts/export_csv.py [output.csv]
```

### 导出为JSONL

```bash
cd backend
python scripts/export_jsonl.py [output.jsonl]
```

## 🧪 测试

```bash
cd backend
pytest tests/ -v
```

## ⚠️ 注意事项

1. **Playwright安装**：首次使用前需要运行 `playwright install` 安装浏览器驱动
2. **定时任务**：确保后端服务持续运行，定时任务才能正常工作
3. **去重机制**：系统使用URL作为主要去重标识，相同URL的职位只会保存一次
4. **数据隐私**：所有数据存储在本地，不会上传到任何服务器
5. **抓取频率**：请遵守目标网站的robots.txt和使用条款，避免过于频繁的请求

## 🐛 常见问题

### 后端启动失败

**问题**：`ModuleNotFoundError: No module named 'apscheduler'` 或 `playwright`

**解决**：
```bash
pip install -r requirements.txt
playwright install firefox
```

### 抓取没有新职位

1. 检查后端日志，查看是否有错误信息
2. 确认Playwright浏览器驱动已正确安装
3. 手动触发抓取测试：访问 http://127.0.0.1:8000/docs，调用 `/scraper/trigger` 端点

### 新职位没有显示在列表中

1. 点击职位列表页面的"刷新"按钮
2. 检查是否有重复的职位被去重逻辑过滤
3. 查看浏览器控制台是否有API错误

### 关键词提取不准确

- 系统使用上下文分析来分类关键词，但某些复杂的职位描述可能需要手动调整
- 可以通过修改 `backend/app/extractors/skill_dictionary.json` 添加新的技能和别名
- 如果发现通用词未被过滤，可以运行重新提取脚本：`python scripts/re_extract_keywords.py`

### 关键词重复（如CI和CD分开显示）

- 系统会自动合并CI和CD为CI/CD（当两者同时出现时）
- 如果仍看到重复，可能是数据库中已有旧数据，运行重新提取脚本更新
- 如果发现通用词未被过滤，可以运行重新提取脚本：`python scripts/re_extract_keywords.py`


## 📝 开发说明

### 添加新的技能关键词

编辑 `backend/app/extractors/skill_dictionary.json`，添加新的技能条目：

```json
{
  "skill_name": {
    "category": "language|framework|tool|...",
    "aliases": ["别名1", "别名2"]
  }
}
```

### 修改抓取逻辑

主要抓取逻辑在 `backend/scripts/scrape_jobs.py` 中，可以根据需要修改搜索策略或添加新的数据源。

### 添加新的分析维度

在 `backend/app/routers/analytics.py` 中添加新的分析端点，在前端 `frontend/app/trends/page.tsx` 中添加可视化。

