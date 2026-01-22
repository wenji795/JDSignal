"""检查提取状态和分析数据"""
import sys
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta

backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine
from app.models import Job, Extraction

db_path = backend_dir / "jobs.db"
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def check_status():
    with Session(engine) as session:
        # 1. 总职位数
        all_jobs = session.exec(select(Job)).all()
        total_jobs = len(all_jobs)
        print(f"📊 数据库统计")
        print(f"=" * 60)
        print(f"总职位数: {total_jobs}")
        
        # 2. 提取结果统计
        all_extractions = session.exec(select(Extraction)).all()
        total_extractions = len(all_extractions)
        print(f"\n提取结果统计:")
        print(f"  有提取结果的职位: {total_extractions}")
        print(f"  无提取结果的职位: {total_jobs - total_extractions}")
        print(f"  提取覆盖率: {total_extractions/total_jobs*100:.1f}%" if total_jobs > 0 else "  提取覆盖率: 0%")
        
        # 3. 提取方法统计
        extraction_methods = Counter()
        for ext in all_extractions:
            method = ext.extraction_method or "unknown"
            extraction_methods[method] += 1
        
        print(f"\n提取方法统计:")
        for method, count in extraction_methods.most_common():
            print(f"  {method}: {count} ({count/total_extractions*100:.1f}%)" if total_extractions > 0 else f"  {method}: {count}")
        
        # 4. 最近30天的职位
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_jobs = session.exec(
            select(Job).where(Job.captured_at >= thirty_days_ago)
        ).all()
        print(f"\n最近30天的职位: {len(recent_jobs)}")
        
        # 5. 最近30天的提取结果
        if recent_jobs:
            recent_job_ids = [job.id for job in recent_jobs]
            recent_extractions = session.exec(
                select(Extraction).where(Extraction.job_id.in_(recent_job_ids))
            ).all()
            print(f"最近30天有提取结果的职位: {len(recent_extractions)}")
            
            # 最近30天的提取方法统计
            recent_methods = Counter()
            for ext in recent_extractions:
                method = ext.extraction_method or "unknown"
                recent_methods[method] += 1
            
            print(f"\n最近30天提取方法统计:")
            for method, count in recent_methods.most_common():
                print(f"  {method}: {count}")
        
        # 6. 角色族统计
        role_families = Counter()
        for job in all_jobs:
            if job.role_family:
                role_families[job.role_family] += 1
        
        print(f"\n角色族统计:")
        for role, count in role_families.most_common():
            print(f"  {role}: {count}")
        
        # 7. 检查关键词数据
        print(f"\n关键词数据检查:")
        keywords_count = 0
        keywords_by_method = Counter()
        for ext in all_extractions:
            keywords_data = ext.keywords_json.get("keywords", [])
            if keywords_data:
                keywords_count += len(keywords_data)
                method = ext.extraction_method or "unknown"
                keywords_by_method[method] += len(keywords_data)
        
        print(f"  总关键词数: {keywords_count}")
        print(f"  平均每个职位关键词数: {keywords_count/total_extractions:.1f}" if total_extractions > 0 else "  平均每个职位关键词数: 0")
        print(f"\n按提取方法的关键词统计:")
        for method, count in keywords_by_method.most_common():
            method_extractions = extraction_methods.get(method, 0)
            avg = count / method_extractions if method_extractions > 0 else 0
            print(f"  {method}: {count} 个关键词 (平均 {avg:.1f} 个/职位)")
        
        # 8. 检查最近的提取结果示例
        print(f"\n最近的提取结果示例 (前5个):")
        recent_extractions_sorted = sorted(all_extractions, key=lambda x: x.extracted_at if hasattr(x, 'extracted_at') and x.extracted_at else datetime.min, reverse=True)
        for i, ext in enumerate(recent_extractions_sorted[:5], 1):
            job = session.get(Job, ext.job_id)
            if job:
                keywords_count = len(ext.keywords_json.get("keywords", []))
                method = ext.extraction_method or "unknown"
                print(f"  {i}. {job.title[:50]}...")
                print(f"     提取方法: {method}, 关键词数: {keywords_count}")
                if ext.summary:
                    print(f"     摘要: {ext.summary[:80]}...")
        
        # 9. 分析数据可用性检查
        print(f"\n分析数据可用性:")
        if total_extractions > 0:
            # 检查是否有足够的数据进行分析
            if len(recent_jobs) >= 10:
                print(f"  ✅ 有足够的数据进行分析 (最近30天有 {len(recent_jobs)} 个职位)")
            else:
                print(f"  ⚠️  数据量较少 (最近30天只有 {len(recent_jobs)} 个职位)")
            
            # 检查关键词数据
            if keywords_count > 0:
                print(f"  ✅ 关键词数据正常 (共 {keywords_count} 个关键词)")
            else:
                print(f"  ⚠️  没有关键词数据")
        else:
            print(f"  ❌ 没有提取结果，无法进行分析")
            print(f"     建议: 运行 python scripts/re_extract_keywords.py 重新提取关键词")

if __name__ == "__main__":
    check_status()
