# 快速开始指南

## 前置要求

1. Python 3.11+ （后端）
2. Node.js 18+ 和 npm （前端）

## 启动步骤

### 1. 启动后端服务

```bash
# 进入项目根目录
cd /Users/swj_795/Desktop/AIBuilder/AIBuilder_projects/JDSignal

# 创建虚拟环境（如果还没有）
python3 -m venv venv
source venv/bin/activate

# 安装后端依赖
pip install -r requirements.txt

# 启动后端服务（在后台运行）
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

后端服务将在 http://127.0.0.1:8000 运行

### 2. （可选）填充示例数据

在另一个终端窗口：

```bash
cd backend
python scripts/seed.py
```

### 3. 启动前端服务

在新终端窗口：

```bash
# 进入前端目录
cd /Users/swj_795/Desktop/AIBuilder/AIBuilder_projects/JDSignal/frontend

# 安装依赖（首次运行需要）
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 http://localhost:3000 运行

## 访问

- **前端界面**: http://localhost:3000
- **后端API文档**: http://127.0.0.1:8000/docs

## 验证

1. 打开浏览器访问 http://localhost:3000
2. 应该能看到首页
3. 点击"职位列表"查看职位
4. 点击"趋势分析"查看统计图表

## 常见问题

### 前端无法连接到后端

确保：
- 后端服务运行在 http://127.0.0.1:8000
- 检查 `frontend/lib/api.ts` 中的 `API_BASE_URL` 是否正确

### 前端显示"加载中"或错误

- 检查浏览器控制台（F12）的错误信息
- 确认后端服务正常运行
- 尝试访问 http://127.0.0.1:8000/docs 确认后端可用