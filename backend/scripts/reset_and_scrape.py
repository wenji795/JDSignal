"""
重置数据库并重新抓取职位数据（用于测试AI增强提取功能）
"""
import os
import sys
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))

def reset_database():
    """删除数据库文件并重新创建表"""
    db_files = [
        backend_dir / "jobs.db",
        backend_dir / "scripts" / "jobs.db",
        project_root / "jobs.db"
    ]
    
    print("="*60)
    print("正在清理数据库...")
    print("="*60)
    
    for db_file in db_files:
        if db_file.exists():
            print(f"删除: {db_file}")
            db_file.unlink()
        else:
            print(f"不存在: {db_file}")
    
    # 重新创建数据库表
    print("\n重新创建数据库表...")
    from app.database import create_db_and_tables
    create_db_and_tables()
    print("✓ 数据库表创建完成")
    
    print("\n" + "="*60)
    print("数据库重置完成！")
    print("="*60)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='重置数据库并重新抓取职位数据')
    parser.add_argument('--skip-scrape', action='store_true', help='仅重置数据库，不进行抓取')
    parser.add_argument('--max-per-keyword', type=int, default=5, help='每个关键词最多抓取多少个职位（默认5，用于测试）')
    parser.add_argument('--headless', action='store_true', help='使用无头模式（不显示浏览器）')
    parser.add_argument('--browser', type=str, choices=['chromium', 'firefox', 'webkit'], default='firefox', help='使用的浏览器引擎（默认firefox）')
    
    args = parser.parse_args()
    
    # 重置数据库
    reset_database()
    
    if args.skip_scrape:
        print("\n跳过抓取步骤（--skip-scrape）")
        return
    
    # 检查后端服务是否运行
    print("\n" + "="*60)
    print("准备开始抓取...")
    print("="*60)
    print("\n⚠️  重要提示：")
    print("1. 确保后端服务正在运行:")
    print("   cd backend && uvicorn app.main:app --reload")
    print("2. 确保已设置 AI_BUILDER_TOKEN 环境变量（在 .env 文件中）")
    print("3. 抓取过程可能需要一些时间...")
    print()
    
    response = input("是否继续抓取？(y/n): ")
    if response.lower() != 'y':
        print("已取消抓取")
        return
    
    # 运行抓取脚本
    print("\n开始抓取职位数据...")
    import asyncio
    from scripts.scrape_nz_jobs import scrape_nz_jobs
    
    asyncio.run(scrape_nz_jobs(
        max_per_keyword=args.max_per_keyword,
        headless=args.headless,
        browser=args.browser
    ))
    
    print("\n" + "="*60)
    print("完成！")
    print("="*60)
    print("\n现在可以检查数据库中的职位数据，验证AI增强提取功能是否正常工作。")
    print("查看提取结果的方法：")
    print("1. 访问 http://localhost:8000/docs 查看API文档")
    print("2. 调用 GET /jobs 查看所有职位")
    print("3. 调用 GET /jobs/{job_id} 查看职位详情（包含extraction字段）")
    print("4. 检查 extraction.extraction_method 字段，应该是 'ai-enhanced' 或 'rule-based'")


if __name__ == "__main__":
    main()
