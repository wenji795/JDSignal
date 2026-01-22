# 更新 Posted Date 指南

## 问题说明

数据库中现有的565个职位都没有 `posted_date`（发布日期），因为它们是在添加提取逻辑之前抓取的。UI会优先显示 `posted_date`，如果没有则显示 `captured_at`（抓取日期）。

## 解决方案

### 方法1：重新抓取 posted_date（推荐）

使用 `re_scrape_posted_dates.py` 脚本重新访问Seek页面提取 posted_date：

```bash
cd backend

# 更新前10个职位（测试）
python scripts/re_scrape_posted_dates.py --limit 10

# 更新所有seek来源的职位（需要较长时间）
python scripts/re_scrape_posted_dates.py --source seek

# 更新所有职位（不限制来源）
python scripts/re_scrape_posted_dates.py
```

**注意**：此脚本会重新访问每个职位的URL，可能需要较长时间（565个职位可能需要1-2小时）。

### 方法2：使用批量更新脚本

使用 `batch_update_posted_dates.py` 脚本批量更新（更快）：

```bash
cd backend

# 更新前50个职位
python scripts/batch_update_posted_dates.py --limit 50 --batch-size 10

# 更新所有职位
python scripts/batch_update_posted_dates.py --batch-size 10
```

### 方法3：使用AI提取（不推荐）

使用 `update_posted_dates.py` 从JD文本中提取（通常JD文本不包含"Posted Xd ago"信息）：

```bash
cd backend

# 检查状态
python scripts/update_posted_dates.py --check

# 更新前10个职位
python scripts/update_posted_dates.py --limit 10
```

## 检查更新状态

运行以下命令检查更新进度：

```bash
cd backend
python scripts/update_posted_dates.py --check
```

## 新抓取的职位

新抓取的职位会自动提取 `posted_date`，无需手动更新。

## 注意事项

1. 更新脚本需要网络连接（访问Seek网站）
2. 更新过程可能需要较长时间（取决于职位数量）
3. 建议先测试少量职位（使用 `--limit` 参数）
4. 如果遇到错误，可以分批更新（使用 `--limit` 和多次运行）
