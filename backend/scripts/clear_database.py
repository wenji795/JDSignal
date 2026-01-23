"""
清空数据库中的所有数据
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine, text
from app.models import Job, Extraction

db_path = backend_dir / "jobs.db"
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def main():
    """清空数据库中的所有数据"""
    with Session(engine) as session:
        # 统计当前数据量
        job_count = len(session.exec(select(Job)).all())
        extraction_count = len(session.exec(select(Extraction)).all())
        
        print("=" * 80)
        print("清空数据库")
        print("=" * 80)
        print(f"当前数据量:")
        print(f"  - 职位 (Job): {job_count} 条")
        print(f"  - 提取结果 (Extraction): {extraction_count} 条")
        
        if job_count == 0 and extraction_count == 0:
            print("\n数据库已经是空的，无需清空")
            return
        
        # 询问确认
        print(f"\n⚠️  警告：此操作将删除所有数据，且无法恢复！")
        print(f"是否确认清空数据库？(输入 'yes' 确认): ", end="")
        confirm = input().strip().lower()
        
        if confirm != 'yes':
            print("\n✗ 已取消清空操作")
            return
        
        # 使用SQL直接删除（更快更彻底）
        print("\n正在删除提取结果...")
        session.execute(text("DELETE FROM extraction"))
        session.commit()
        print(f"✓ 已删除 {extraction_count} 条提取结果")
        
        # 再删除job
        print("正在删除职位...")
        session.execute(text("DELETE FROM job"))
        session.commit()
        print(f"✓ 已删除 {job_count} 条职位")
        
        # 优化数据库（回收空间）
        print("正在优化数据库...")
        session.execute(text("VACUUM"))
        session.commit()
        print("✓ 数据库已优化")
        
        # 验证清空结果
        remaining_jobs = len(session.exec(select(Job)).all())
        remaining_extractions = len(session.exec(select(Extraction)).all())
        
        print("\n" + "=" * 80)
        print("清空完成")
        print("=" * 80)
        print(f"剩余数据量:")
        print(f"  - 职位 (Job): {remaining_jobs} 条")
        print(f"  - 提取结果 (Extraction): {remaining_extractions} 条")
        
        if remaining_jobs == 0 and remaining_extractions == 0:
            print("\n✓ 数据库已成功清空")
        else:
            print(f"\n⚠️  警告：仍有 {remaining_jobs + remaining_extractions} 条数据未删除")

if __name__ == "__main__":
    main()
