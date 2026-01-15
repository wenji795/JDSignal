# Frontend - Job JD Tracker Dashboard

Next.js前端仪表板，用于可视化职位JD、ATS关键词提取和趋势分析。

## 快速开始

### 前置要求

- Node.js 18+ 
- npm 或 yarn
- 后端服务运行在 http://127.0.0.1:8000

### 安装

```bash
cd frontend
npm install
```

### 运行开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
npm start
```

## 页面

### 1. /jobs - 职位列表
- 显示所有职位（卡片列表）
- 过滤器：角色族、资历级别
- 点击职位查看详情

### 2. /jobs/[id] - 职位详情
- 显示职位基本信息
- 可折叠的原始JD文本
- 提取的关键词（标签形式）
- 必须拥有的技能
- 加分项
- 证书列表

### 3. /trends - 趋势分析
- 总职位数统计
- 角色族分布（饼图）
- 资历级别分布（饼图）
- Top 20关键词（柱状图）
- 关键词增长趋势（柱状图）
- 各角色族Top关键词

## 技术栈

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Recharts (图表库)
- Fetch API

## 项目结构

```
frontend/
├── app/
│   ├── page.tsx           # 首页
│   ├── layout.tsx         # 根布局
│   ├── globals.css        # 全局样式
│   ├── jobs/
│   │   ├── page.tsx       # 职位列表页
│   │   └── [id]/
│   │       └── page.tsx   # 职位详情页
│   └── trends/
│       └── page.tsx       # 趋势分析页
├── lib/
│   └── api.ts             # API客户端
└── package.json
```

## API端点

前端调用以下后端端点：

- `GET /jobs` - 获取职位列表（支持过滤）
- `GET /jobs/{id}` - 获取职位详情
- `GET /jobs/{id}/extraction` - 获取提取结果
- `GET /analytics/trends` - 获取趋势分析