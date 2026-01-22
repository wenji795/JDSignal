"""
使用AI优先推断重新判断数据库中所有职位的角色族和资历级别
"""
import sys
import asyncio
from pathlib import Path
from collections import Counter

backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine
from app.models import Job
from app.extractors.ai_role_inferrer import infer_role_and_seniority_with_ai
from app.database import create_db_and_tables

# 使用与主应用相同的数据库路径（相对于backend目录）
db_path = backend_dir / "jobs.db"
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


async def re_infer_all_jobs(use_ai: bool = True, force_update: bool = False):
    """
    重新推断所有职位的role_family和seniority（AI优先）
    
    Args:
        use_ai: 是否使用AI推断（默认True）
        force_update: 如果为True，强制更新所有职位（即使已有值）；如果为False，只更新空值
    """
    # 确保数据库表存在
    create_db_and_tables()
    
    with Session(engine) as session:
        # 获取所有职位
        jobs = session.exec(select(Job)).all()
        total_jobs = len(jobs)
        
        print(f"开始重新推断 {total_jobs} 个职位的角色族和资历级别...")
        print(f"使用AI推断: {'是' if use_ai else '否'}")
        print(f"强制更新: {'是' if force_update else '否（只更新空值）'}")
        print("=" * 60)
        
        updated_role_family_count = 0
        updated_seniority_count = 0
        unchanged_role_family_count = 0
        unchanged_seniority_count = 0
        
        # 统计变更
        role_family_changes = Counter()
        seniority_changes = Counter()
        
        for i, job in enumerate(jobs, 1):
            # 推断role_family和seniority（AI优先）
            new_role_family, new_seniority = await infer_role_and_seniority_with_ai(
                job.title,
                job.jd_text,
                use_ai=use_ai
            )
            
            # 更新role_family
            if new_role_family:
                old_role_family = job.role_family
                should_update = force_update or not job.role_family or job.role_family != new_role_family
                
                if should_update:
                    job.role_family = new_role_family
                    updated_role_family_count += 1
                    
                    # 记录变更
                    if old_role_family != new_role_family:
                        change_key = f"{old_role_family or 'None'} -> {new_role_family}"
                        role_family_changes[change_key] += 1
                        
                        if i <= 10 or (i % 50 == 0):  # 前10个或每50个显示一次
                            print(f"[{i}/{total_jobs}] ✓ 更新 role_family: {change_key}")
                            print(f"    标题: {job.title[:60]}...")
                else:
                    unchanged_role_family_count += 1
            
            # 更新seniority
            if new_seniority:
                old_seniority = job.seniority
                should_update = force_update or not job.seniority or job.seniority != new_seniority
                
                if should_update:
                    job.seniority = new_seniority
                    updated_seniority_count += 1
                    
                    # 记录变更
                    if old_seniority != new_seniority:
                        old_str = old_seniority.value if old_seniority else "None"
                        new_str = new_seniority.value if new_seniority else "None"
                        change_key = f"{old_str} -> {new_str}"
                        seniority_changes[change_key] += 1
                        
                        if i <= 10 or (i % 50 == 0):  # 前10个或每50个显示一次
                            print(f"[{i}/{total_jobs}] ✓ 更新 seniority: {change_key}")
                            print(f"    标题: {job.title[:60]}...")
                else:
                    unchanged_seniority_count += 1
            
            session.add(job)
            
            # 每100个职位提交一次，避免内存占用过大
            if i % 100 == 0:
                session.commit()
                print(f"已处理 {i}/{total_jobs} 个职位...")
        
        # 最终提交
        session.commit()
        
        print("\n" + "=" * 60)
        print("完成！统计信息：")
        print(f"  总职位数: {total_jobs}")
        print(f"  更新 role_family: {updated_role_family_count}")
        print(f"  未变更 role_family: {unchanged_role_family_count}")
        print(f"  更新 seniority: {updated_seniority_count}")
        print(f"  未变更 seniority: {unchanged_seniority_count}")
        
        if role_family_changes:
            print(f"\n角色族变更统计（Top 10）:")
            for change, count in role_family_changes.most_common(10):
                print(f"  {change}: {count}")
        
        if seniority_changes:
            print(f"\n资历级别变更统计（Top 10）:")
            for change, count in seniority_changes.most_common(10):
                print(f"  {change}: {count}")
        
        # 统计最终的角色族和资历级别分布
        print(f"\n最终角色族分布:")
        final_role_families = Counter()
        final_seniorities = Counter()
        
        session.refresh(jobs[0]) if jobs else None  # 刷新以确保数据最新
        all_jobs_refreshed = session.exec(select(Job)).all()
        
        for job in all_jobs_refreshed:
            if job.role_family:
                final_role_families[job.role_family] += 1
            if job.seniority:
                final_seniorities[job.seniority.value] += 1
        
        for role, count in final_role_families.most_common():
            print(f"  {role}: {count}")
        
        print(f"\n最终资历级别分布:")
        for seniority, count in final_seniorities.most_common():
            print(f"  {seniority}: {count}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="使用AI优先推断重新判断数据库中所有职位的角色族和资历级别")
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="不使用AI，只使用规则推断（默认使用AI）"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制更新所有职位（即使已有值），默认只更新空值"
    )
    
    args = parser.parse_args()
    
    print("开始重新推断数据库中所有职位的角色族和资历级别...")
    if args.no_ai:
        print("模式：仅使用规则推断（不使用AI）")
    else:
        print("模式：AI优先推断（失败时回退到规则推断）")
    
    if args.force:
        print("更新策略：强制更新所有职位")
    else:
        print("更新策略：只更新空值")
    
    print()
    
    asyncio.run(re_infer_all_jobs(use_ai=not args.no_ai, force_update=args.force))
