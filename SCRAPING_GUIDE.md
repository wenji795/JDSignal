# 使用Playwright抓取职位数据指南

## 安装

### 1. 安装Python依赖

```bash
pip install playwright httpx
```

或者：

```bash
pip install -r requirements.txt
```

### 2. 安装Playwright浏览器

```bash
playwright install chromium
```

## 使用方法

### 方式1: 命令行直接指定URL

```bash
cd backend
python scripts/scrape_jobs.py "https://www.seek.co.nz/job/12345678"
```

### 方式2: 从文件读取URL列表

创建URL文件（如 `urls.txt`）：
```
https://www.seek.co.nz/job/12345678
https://www.seek.co.nz/job/87654321
```

然后运行：

```bash
cd backend
python scripts/scrape_jobs.py --file urls.txt
```

### 方式3: 搜索模式（自动搜索并抓取）

```bash
cd backend
python scripts/scrape_jobs.py --search-seek "software test" --max-results 20
```

### 方式4: 无头模式（后台运行，不显示浏览器）

```bash
python scripts/scrape_jobs.py --headless --file urls.txt
```

## 注意事项

### Seek
- 仅支持Seek NZ（seek.co.nz）的职位
- Seek的公开职位通常不需要登录
- 如果遇到验证码，需要在浏览器窗口中手动完成
- 系统会自动过滤非新西兰的职位

## 工作原理

1. 使用Playwright打开Chrome浏览器（可见窗口）
2. 访问每个职位URL
3. 提取职位信息：
   - 标题
   - 公司名称
   - 地点
   - 职位描述
4. 自动调用 `/capture` API保存数据
5. 自动运行关键词提取

## 示例

```bash
# 抓取单个Seek职位
python scripts/scrape_jobs.py "https://www.seek.co.nz/job/12345678"

# 抓取多个职位
python scripts/scrape_jobs.py \
  "https://www.seek.co.nz/job/12345678" \
  "https://www.seek.co.nz/job/87654321"

# 从文件批量抓取
python scripts/scrape_jobs.py --file job_urls.txt

# 搜索并自动抓取
python scripts/scrape_jobs.py --search-seek "python developer" --max-results 30
```

## 故障排查

1. **无法提取数据**
   - 检查URL是否正确
   - 检查是否需要登录
   - 网站结构可能已变化，需要更新选择器

2. **浏览器无法启动**
   - 确保已运行 `playwright install chromium`
   - 检查系统权限

3. **API连接失败**
   - 确保后端服务运行在 http://127.0.0.1:8000
   - 检查网络连接