"""检查数据库中 product manager 职位的情况"""
import sys
from pathlib import Path
from collections import Counter

backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine
from app.models import Job
from app.extractors.role_inferrer import infer_role_family

db_path = backend_dir / "jobs.db"
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def check_product_manager():
    with Session(engine) as session:
        # 1. 检查数据库中已标记为 product manager 的职位
        pm_jobs = session.exec(
            select(Job).where(Job.role_family == "product manager")
        ).all()
        
        print("=" * 60)
        print("📊 Product Manager 职位检查")
        print("=" * 60)
        print(f"\n数据库中已标记为 'product manager' 的职位数: {len(pm_jobs)}")
        
        if pm_jobs:
            print("\n已标记的职位列表:")
            for i, job in enumerate(pm_jobs[:20], 1):  # 只显示前20个
                print(f"  {i}. {job.title} - {job.company}")
            if len(pm_jobs) > 20:
                print(f"  ... 还有 {len(pm_jobs) - 20} 个职位")
        
        # 2. 检查标题中包含 product manager 相关关键词的职位
        all_jobs = session.exec(select(Job)).all()
        print(f"\n数据库总职位数: {len(all_jobs)}")
        
        # Product Manager 相关关键词
        pm_keywords = [
            'product manager', 'product owner', 'po',
            'senior product manager', 'associate product manager',
            'technical product manager', 'it product manager',
            'software product manager', 'digital product manager',
            'product lead', 'product specialist'
        ]
        
        potential_pm_jobs = []
        for job in all_jobs:
            title_lower = job.title.lower()
            if any(keyword in title_lower for keyword in pm_keywords):
                potential_pm_jobs.append(job)
        
        print(f"\n标题中包含 Product Manager 相关关键词的职位数: {len(potential_pm_jobs)}")
        
        if potential_pm_jobs:
            print("\n这些职位的当前分类:")
            role_family_counter = Counter()
            for job in potential_pm_jobs:
                current_role = job.role_family or "未分类"
                role_family_counter[current_role] += 1
                
                # 使用推断函数检查应该是什么分类
                inferred_role = infer_role_family(job.title, job.jd_text)
                
                if current_role != "product manager":
                    print(f"\n  ⚠️  {job.title[:60]}...")
                    print(f"     当前分类: {current_role}")
                    print(f"     推断分类: {inferred_role}")
            
            print(f"\n按当前分类统计:")
            for role, count in role_family_counter.most_common():
                print(f"  {role}: {count}")
            
            # 3. 检查推断结果
            print(f"\n使用推断函数重新检查这些职位:")
            should_be_pm = []
            for job in potential_pm_jobs:
                inferred_role = infer_role_family(job.title, job.jd_text)
                if inferred_role == "product manager":
                    should_be_pm.append(job)
            
            print(f"  应该被分类为 'product manager' 的职位数: {len(should_be_pm)}")
            
            if should_be_pm:
                print("\n应该被分类为 product manager 的职位:")
                for i, job in enumerate(should_be_pm[:10], 1):
                    current_role = job.role_family or "未分类"
                    print(f"  {i}. {job.title[:60]}... (当前: {current_role})")
        
        # 4. 总结
        print("\n" + "=" * 60)
        print("总结:")
        print(f"  已标记为 product manager: {len(pm_jobs)}")
        print(f"  标题包含相关关键词: {len(potential_pm_jobs)}")
        if potential_pm_jobs:
            should_be_pm_count = sum(
                1 for job in potential_pm_jobs 
                if infer_role_family(job.title, job.jd_text) == "product manager"
            )
            print(f"  应该被分类为 product manager: {should_be_pm_count}")
            if should_be_pm_count > len(pm_jobs):
                print(f"\n  ⚠️  发现 {should_be_pm_count - len(pm_jobs)} 个职位需要更新分类")
                print(f"  建议运行: python scripts/update_role_family.py --force")

if __name__ == "__main__":
    check_product_manager()
