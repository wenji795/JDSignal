"""
重新提取已有职位的关键词（使用改进后的动态提取算法）
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine
from app.models import Job, Extraction
from app.extractors.keyword_extractor import extract_and_save_sync
from app.database import create_db_and_tables
import asyncio

# 使用与主应用相同的数据库路径
db_path = backend_dir / "jobs.db"
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def re_extract_all_jobs():
    """重新提取所有已有职位的关键词"""
    # 确保数据库表存在
    create_db_and_tables()
    
    with Session(engine) as session:
        # 获取所有职位
        jobs = session.exec(select(Job)).all()
        
        print(f"找到 {len(jobs)} 个职位，开始重新提取关键词...")
        print("="*60)
        
        updated_count = 0
        error_count = 0
        
        for i, job in enumerate(jobs, 1):
            try:
                print(f"\n[{i}/{len(jobs)}] 处理职位: {job.title[:60]}...")
                
                # 重新提取关键词（这会更新或创建Extraction记录）
                # 使用同步包装器，支持AI增强提取
                extract_and_save_sync(
                    job.id, 
                    job.jd_text, 
                    session,
                    job_title=job.title,
                    company=job.company,
                    use_ai=True  # 启用AI增强提取
                )
                
                # 获取提取结果以验证
                extraction = session.exec(
                    select(Extraction).where(Extraction.job_id == job.id)
                ).first()
                
                if extraction:
                    keyword_count = len(extraction.keywords_json.get("keywords", []))
                    method = extraction.extraction_method or "unknown"
                    has_summary = "有摘要" if extraction.summary else "无摘要"
                    print(f"  ✓ 成功提取 {keyword_count} 个关键词 ({method}, {has_summary})")
                    updated_count += 1
                else:
                    print(f"  ✗ 警告: 提取结果未找到")
                    error_count += 1
                    
            except Exception as e:
                print(f"  ✗ 错误: {e}")
                error_count += 1
                import traceback
                traceback.print_exc()
        
        print(f"\n{'='*60}")
        print(f"完成！")
        print(f"  成功更新: {updated_count} 个职位")
        print(f"  失败: {error_count} 个职位")
        print(f"{'='*60}")


if __name__ == "__main__":
    print("="*60)
    print("重新提取已有职位的关键词")
    print("使用改进后的动态提取算法（不依赖预定义字典）")
    print("="*60)
    print("\n注意：")
    print("- 新抓取的职位会自动使用新算法，无需运行此脚本")
    print("- 此脚本仅用于更新已有职位的关键词")
    print("- 运行时间取决于职位数量")
    print()
    
    confirm = input("是否继续？(y/n): ")
    if confirm.lower() == 'y':
        re_extract_all_jobs()
    else:
        print("已取消")
