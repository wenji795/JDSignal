# QA职位问题修复说明

## 修复内容

### 1. ✅ 修复角色族推断

**问题：** QA职位（如 "Quality Assurance Specialist"）没有被正确识别为 `testing` 角色族，被归类为 `'其他'`

**修复：** 在 `backend/app/extractors/role_inferrer.py` 中添加了完整的QA职位关键词：
- `'quality assurance specialist'`
- `'quality assurance officer'`
- `'quality assurance manager'`
- `'quality assurance coordinator'`
- `'quality assurance analyst'`
- `'quality assurance lead'`
- `'qa specialist'`, `'qa officer'`, `'qa manager'` 等
- `'software quality assurance'`, `'it quality assurance'` 等

**效果：** 现在所有QA相关职位都会被正确识别为 `testing` 角色族

### 2. ✅ 创建数据清理脚本

**脚本位置：** `backend/scripts/cleanup_qa_jobs.py`

**功能：**
- 分析数据库中的所有QA职位
- 识别IT QA和非IT QA职位
- 重新分类IT QA职位的角色族
- 删除非IT QA职位（食品、制造、物流等）

**使用方法：**

```bash
# 1. 只分析，不执行（默认）
cd backend
python scripts/cleanup_qa_jobs.py

# 2. 只分析，不清理
python scripts/cleanup_qa_jobs.py --analyze-only

# 3. 执行实际清理（需要明确指定）
python scripts/cleanup_qa_jobs.py --execute
```

**清理逻辑：**
- **IT QA职位**：根据标题和JD重新推断角色族，更新为 `testing` 或 `qa`
- **非IT QA职位**：删除（包括食品、制造、物流、科学等行业的QA职位）
- **角色族分类错误**：修复为正确的角色族

### 3. ✅ 增强过滤逻辑

**问题：** 即使行业信息缺失，非IT QA职位也可能被抓取

**修复：** 在 `backend/scripts/scrape_jobs.py` 的 `is_non_it_job` 函数中增强了检查逻辑：

1. **行业信息存在时**：
   - 如果行业明确是非IT行业，直接过滤
   - 如果行业是IT行业，允许通过

2. **行业信息缺失时（新增）**：
   - 检查标题是否有明确的IT QA关键词
   - 检查JD文本中是否有IT相关关键词
   - 如果都没有，则过滤掉（严格模式）

3. **标题检查增强**：
   - 添加了更多IT QA关键词到检查列表
   - 包括 `'software tester'`, `'test developer'`, `'qa developer'` 等

**效果：** 未来抓取时，即使行业信息缺失，也能通过JD文本严格过滤非IT QA职位

## 使用步骤

### 步骤1：运行数据库迁移（如果还没有运行）

```bash
cd backend
python scripts/add_industry_field.py
```

### 步骤2：分析现有QA职位

```bash
python scripts/cleanup_qa_jobs.py --analyze-only
```

这会显示：
- IT QA职位数量
- 非IT QA职位数量（建议删除）
- 角色族分类错误的职位

### 步骤3：执行清理（可选）

**⚠️ 警告：** 这会删除非IT QA职位，请先备份数据库！

```bash
# 先查看会删除哪些职位
python scripts/cleanup_qa_jobs.py

# 确认无误后执行
python scripts/cleanup_qa_jobs.py --execute
```

### 步骤4：重新分类现有IT QA职位（如果需要）

如果只想重新分类角色族而不删除职位，可以运行：

```bash
python scripts/check_and_reclassify_qa_jobs.py --reclassify
```

## 验证修复

### 1. 验证角色族推断

创建新职位时，QA相关标题应该被正确识别为 `testing` 角色族：

```python
from app.extractors.role_inferrer import infer_role_family

# 应该返回 'testing'
print(infer_role_family("Quality Assurance Specialist", "Software testing experience..."))
print(infer_role_family("QA Officer", "Test automation with Selenium..."))
print(infer_role_family("Quality Assurance Manager", "Lead QA team..."))
```

### 2. 验证过滤逻辑

非IT QA职位应该被过滤：

```python
from scripts.scrape_jobs import is_non_it_job

# 应该返回 True（被过滤）
print(is_non_it_job(
    "Quality Assurance Specialist",
    "Food safety, HACCP, ISO 22000...",
    "Food & Beverage"
))

# 应该返回 False（IT QA，不过滤）
print(is_non_it_job(
    "QA Engineer",
    "Software testing, Selenium, test automation...",
    "Information & Communication Technology"
))
```

## 注意事项

1. **数据备份**：执行清理前请备份数据库
2. **行业信息**：新抓取的职位会包含行业信息，但旧数据可能没有
3. **严格模式**：过滤逻辑现在是严格模式，宁可少抓也不要抓错
4. **角色族**：IT QA职位会被分类为 `testing` 或 `qa`，不再归类为 `'其他'`

## 后续建议

1. **定期清理**：定期运行清理脚本，保持数据质量
2. **监控抓取**：关注抓取日志，确认非IT QA职位被正确过滤
3. **行业信息**：确保抓取时能正确提取行业信息
