"""
批量重新提取所有职位的关键词（无需确认）
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine
from app.models import Job, Extraction
from app.extractors.keyword_extractor import extract_and_save_sync
from app.database import create_db_and_tables

db_path = backend_dir / "jobs.db"
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def batch_re_extract(batch_size=50, use_ai=True):
    """
    批量重新提取所有职位的关键词
    
    Args:
        batch_size: 每批处理的职位数量
        use_ai: 是否使用AI增强提取
    """
    create_db_and_tables()
    
    with Session(engine) as session:
        # 获取所有职位
        jobs = session.exec(select(Job)).all()
        total_jobs = len(jobs)
        
        print(f"找到 {total_jobs} 个职位，开始批量提取关键词...")
        print(f"批量大小: {batch_size}, AI提取: {'启用' if use_ai else '禁用'}")
        print("="*60)
        
        updated_count = 0
        error_count = 0
        
        # 分批处理
        for batch_start in range(0, total_jobs, batch_size):
            batch_end = min(batch_start + batch_size, total_jobs)
            batch_jobs = jobs[batch_start:batch_end]
            
            print(f"\n处理批次 {batch_start//batch_size + 1} (职位 {batch_start+1}-{batch_end}/{total_jobs})...")
            
            for i, job in enumerate(batch_jobs, 1):
                global_index = batch_start + i
                try:
                    # 检查是否已有提取结果
                    existing = session.exec(
                        select(Extraction).where(Extraction.job_id == job.id)
                    ).first()
                    
                    if existing:
                        # 跳过已有提取结果的职位
                        continue
                    
                    # 重新提取关键词
                    extract_and_save_sync(
                        job.id, 
                        job.jd_text, 
                        session,
                        job_title=job.title,
                        company=job.company,
                        use_ai=use_ai
                    )
                    
                    # 验证提取结果
                    extraction = session.exec(
                        select(Extraction).where(Extraction.job_id == job.id)
                    ).first()
                    
                    if extraction:
                        keyword_count = len(extraction.keywords_json.get("keywords", []))
                        method = extraction.extraction_method or "unknown"
                        updated_count += 1
                        
                        # 每10个职位显示一次进度
                        if updated_count % 10 == 0:
                            print(f"  [{global_index}/{total_jobs}] ✓ 已处理 {updated_count} 个职位 (当前: {keyword_count} 关键词, {method})")
                    else:
                        error_count += 1
                        if error_count <= 5:  # 只显示前5个错误
                            print(f"  [{global_index}/{total_jobs}] ✗ 警告: 提取结果未找到")
                        
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:  # 只显示前5个错误
                        print(f"  [{global_index}/{total_jobs}] ✗ 错误: {str(e)[:100]}")
        
        print(f"\n{'='*60}")
        print(f"完成！")
        print(f"  成功更新: {updated_count} 个职位")
        print(f"  失败: {error_count} 个职位")
        print(f"  跳过（已有提取结果）: {total_jobs - updated_count - error_count} 个职位")
        print(f"{'='*60}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="批量重新提取所有职位的关键词")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="每批处理的职位数量（默认50）"
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="禁用AI提取，仅使用规则提取"
    )
    
    args = parser.parse_args()
    
    batch_re_extract(batch_size=args.batch_size, use_ai=not args.no_ai)
