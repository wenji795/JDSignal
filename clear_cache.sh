#!/bin/bash
# 清除前端和后端缓存的脚本

echo "=========================================="
echo "清除缓存"
echo "=========================================="

# 清除Next.js缓存
if [ -d "frontend/.next" ]; then
    echo "正在删除 Next.js 缓存 (.next 目录)..."
    rm -rf frontend/.next
    echo "✓ Next.js 缓存已清除"
else
    echo "✓ Next.js 缓存目录不存在"
fi

# 清除Node模块缓存（可选）
# if [ -d "frontend/node_modules/.cache" ]; then
#     echo "正在删除 Node modules 缓存..."
#     rm -rf frontend/node_modules/.cache
#     echo "✓ Node modules 缓存已清除"
# fi

echo ""
echo "=========================================="
echo "验证数据库状态"
echo "=========================================="

# 检查数据库
if [ -f "backend/jobs.db" ]; then
    JOB_COUNT=$(sqlite3 backend/jobs.db "SELECT COUNT(*) FROM job;" 2>/dev/null || echo "0")
    EXT_COUNT=$(sqlite3 backend/jobs.db "SELECT COUNT(*) FROM extraction;" 2>/dev/null || echo "0")
    echo "数据库: backend/jobs.db"
    echo "  职位数量: $JOB_COUNT"
    echo "  提取结果数量: $EXT_COUNT"
    
    if [ "$JOB_COUNT" = "0" ] && [ "$EXT_COUNT" = "0" ]; then
        echo "✓ 数据库确实是空的"
    else
        echo "⚠️  警告：数据库中仍有数据！"
    fi
else
    echo "⚠️  数据库文件不存在"
fi

echo ""
echo "=========================================="
echo "下一步操作"
echo "=========================================="
echo "1. 重启后端服务："
echo "   cd backend && python -m uvicorn app.main:app --reload"
echo ""
echo "2. 重启前端服务："
echo "   cd frontend && npm run dev"
echo ""
echo "3. 在浏览器中硬刷新页面："
echo "   Mac: Cmd + Shift + R"
echo "   Windows/Linux: Ctrl + Shift + R"
echo ""
echo "4. 如果还有问题，清除浏览器缓存："
echo "   - 打开开发者工具 (F12)"
echo "   - 右键点击刷新按钮"
echo "   - 选择 '清空缓存并硬性重新加载'"
