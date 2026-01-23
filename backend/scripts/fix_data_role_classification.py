"""
修复被误分类为data角色族的职位
例如：C/C++ Developer不应该因为JD中提到"data structures"而被分类为data
"""
import sys
from pathlib import Path

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

def main():
    """修复被误分类为data的职位"""
    with Session(engine) as session:
        # 查找所有被分类为data的职位
        data_jobs = session.exec(select(Job).where(Job.role_family == "data")).all()
        print(f"找到 {len(data_jobs)} 个被分类为data的职位")
        
        if not data_jobs:
            print("没有需要修复的职位")
            return
        
        fixed_count = 0
        fixed_jobs = []
        
        print("\n检查每个职位...")
        for job in data_jobs:
            # 使用修复后的逻辑重新推断角色族
            inferred_role_family = infer_role_family(job.title, job.jd_text or "")
            
            # 如果推断结果不是data，说明之前被误分类了
            if inferred_role_family != "data":
                old_role_family = job.role_family or "未分类"
                job.role_family = inferred_role_family
                fixed_jobs.append((job, old_role_family, inferred_role_family))
                fixed_count += 1
                print(f"  ✓ {job.title[:50]}...")
                print(f"    角色族: {old_role_family} -> {inferred_role_family}")
        
        if fixed_count == 0:
            print("\n没有需要修复的职位（所有data分类都是正确的）")
            return
        
        print(f"\n共需要修复 {fixed_count} 个职位")
        print("\n修复详情:")
        for job, old_rf, new_rf in fixed_jobs:
            print(f"  - {job.title[:60]}")
            print(f"    公司: {job.company}")
            print(f"    角色族: {old_rf} -> {new_rf}")
        
        # 询问是否确认修复
        print(f"\n是否确认修复这 {fixed_count} 个职位？(y/n): ", end="")
        confirm = input().strip().lower()
        
        if confirm == 'y':
            session.commit()
            print(f"\n✓ 成功修复 {fixed_count} 个职位")
        else:
            session.rollback()
            print("\n✗ 已取消修复")

if __name__ == "__main__":
    main()
