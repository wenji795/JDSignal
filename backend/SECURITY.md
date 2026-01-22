# 安全说明

## ⚠️ 重要安全提醒

### AI_BUILDER_TOKEN 泄露处理

如果 `AI_BUILDER_TOKEN` 被意外提交到版本控制系统（Git），请立即采取以下措施：

1. **立即撤销泄露的 Token**
   - 登录 AI Builder 平台
   - 找到对应的 API Token
   - 立即撤销（Revoke）该 Token
   - 生成新的 Token

2. **更新本地环境变量**
   - 删除旧的 `.env` 文件
   - 创建新的 `.env` 文件，使用新的 Token
   - 确保 `.env` 文件在 `.gitignore` 中

3. **清理 Git 历史（如果已提交）**
   ```bash
   # 警告：这会重写 Git 历史，需要强制推送
   # 仅在私有仓库中使用，或与团队协调
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch backend/.env" \
     --prune-empty --tag-name-filter cat -- --all
   ```

## 🔒 最佳实践

1. **永远不要提交敏感信息**
   - `.env` 文件应始终在 `.gitignore` 中
   - 不要在代码、注释或文档中硬编码 Token
   - 使用占位符（如 `your_token_here`）代替真实 Token

2. **使用环境变量**
   - 在本地开发时使用 `.env` 文件
   - 在生产环境使用系统环境变量或密钥管理服务
   - 使用 `python-dotenv` 加载 `.env` 文件

3. **定期轮换 Token**
   - 定期更新 API Token
   - 撤销不再使用的 Token
   - 为不同环境使用不同的 Token

4. **代码审查**
   - 在提交代码前检查是否包含敏感信息
   - 使用工具扫描代码库中的敏感信息
   - 定期审查 `.gitignore` 配置

## 📝 检查清单

在提交代码前，请确认：

- [ ] `.env` 文件在 `.gitignore` 中
- [ ] 代码中没有硬编码的 Token
- [ ] 文档中使用占位符而非真实 Token
- [ ] Git 历史中没有敏感信息（使用 `git log -p` 检查）

## 🛠️ 工具推荐

- **git-secrets**: 防止提交敏感信息
- **truffleHog**: 扫描 Git 历史中的敏感信息
- **gitguardian**: 自动检测代码中的敏感信息
