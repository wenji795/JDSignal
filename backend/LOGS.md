# 日志系统使用说明

## 📋 概述

系统已配置完整的日志记录功能，所有日志会自动保存到文件中，方便后续查看和调试。

## 📁 日志文件位置

日志文件保存在：`backend/logs/` 目录下

- **应用日志**：`app_YYYYMMDD.log` - 记录所有应用日志（DEBUG级别及以上）
- **错误日志**：`error_YYYYMMDD.log` - 只记录错误日志（ERROR级别及以上）

日志文件会自动轮转：
- 单个文件最大 10MB
- 保留最近 5 个备份文件
- 每天创建新的日志文件

## 🔍 查看日志的方法

### 方法1：使用命令行脚本（推荐）

```bash
cd backend

# 查看应用日志（最后100行）
python scripts/view_logs.py

# 查看错误日志
python scripts/view_logs.py --type error

# 查看指定行数
python scripts/view_logs.py --lines 200

# 查看所有行
python scripts/view_logs.py --lines 0

# 持续跟踪日志（类似 tail -f）
python scripts/view_logs.py --follow

# 列出所有日志文件
python scripts/view_logs.py --list
```

### 方法2：使用API端点

启动后端服务后，可以通过API查看日志：

```bash
# 列出所有日志文件
curl http://127.0.0.1:8000/logs/list

# 查看应用日志（最后50行）
curl http://127.0.0.1:8000/logs/latest?log_type=app&lines=50

# 查看错误日志
curl http://127.0.0.1:8000/logs/latest?log_type=error&lines=50

# 查看完整日志内容（最后100行）
curl http://127.0.0.1:8000/logs/view?log_type=app&lines=100
```

### 方法3：直接查看文件

```bash
cd backend/logs

# 查看最新的应用日志
tail -n 100 app_*.log | tail -n 100

# 查看最新的错误日志
tail -n 100 error_*.log | tail -n 100

# 持续跟踪日志
tail -f app_*.log
```

## 📊 日志级别

- **DEBUG**：详细的调试信息（仅写入文件）
- **INFO**：一般信息（控制台和文件）
- **WARNING**：警告信息
- **ERROR**：错误信息（同时写入error日志文件）
- **CRITICAL**：严重错误

## 🔧 在代码中使用日志

```python
from app.logger import get_logger

logger = get_logger(__name__)

# 记录不同级别的日志
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息", exc_info=True)  # exc_info=True 会包含异常堆栈
logger.critical("严重错误")
```

## 📝 日志格式

日志格式：`时间 - 模块名 - 级别 - 文件名:行号 - 消息`

示例：
```
2026-01-23 13:30:45 - app.main - INFO - main.py:50 - 数据库表初始化完成
2026-01-23 13:30:46 - app.routers.jobs - ERROR - jobs.py:95 - 提取失败: Connection timeout
```

## 🎯 常见使用场景

### 查看抓取任务的日志

```bash
# 查看最近的抓取相关日志
python scripts/view_logs.py | grep -i "scrape\|抓取"
```

### 查看错误日志

```bash
# 查看所有错误
python scripts/view_logs.py --type error
```

### 实时监控日志

```bash
# 持续跟踪日志，实时查看新日志
python scripts/view_logs.py --follow
```

## ⚙️ 配置说明

日志配置在 `backend/app/logger.py` 中，可以修改：

- 日志文件位置
- 日志级别
- 文件大小限制
- 备份文件数量
- 日志格式

## 🚨 注意事项

1. 日志文件会自动轮转，不会无限增长
2. 日志文件在 `.gitignore` 中，不会被提交到版本控制
3. 生产环境建议定期清理旧日志文件
4. 敏感信息（如API密钥）不会记录到日志中
