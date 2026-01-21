"""
更新React Native Developer职位的role_family为fullstack
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine
from app.models import Job
from app.database import create_db_and_tables

# 使用与主应用相同的数据库路径
db_path = backend_dir / "jobs.db"
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def update_react_native_jobs(dry_run: bool = True):
    """
    更新React Native Developer职位的role_family为fullstack
    
    Args:
        dry_run: 如果为True，只检查不更新；如果为False，会实际更新数据库
    """
    # 确保数据库表存在
    create_db_and_tables()
    
    with Session(engine) as session:
        # 获取所有职位
        jobs = session.exec(select(Job)).all()
        
        print(f"找到 {len(jobs)} 个职位，开始检查React Native职位...")
        print("="*80)
        
        react_native_jobs = []
        
        for job in jobs:
            title_lower = job.title.lower()
            # 检查是否是React Native职位
            if 'react native' in title_lower:
                if job.role_family == 'mobile':
                    react_native_jobs.append(job)
                    if len(react_native_jobs) <= 20:  # 只显示前20个
                        print(f"  [{len(react_native_jobs)}] {job.title[:60]}... (当前: mobile -> fullstack)")
        
        print(f"\n{'='*80}")
        print(f"找到 {len(react_native_jobs)} 个React Native职位需要更新")
        print(f"{'='*80}")
        
        if not react_native_jobs:
            print("没有需要更新的React Native职位")
            return
        
        if dry_run:
            print("\n注意：这是预览模式（dry_run），数据库未被修改")
            print("要实际更新数据库，请运行: python update_react_native_role.py --update")
        else:
            # 更新React Native职位的role_family
            updated_count = 0
            for job in react_native_jobs:
                job.role_family = 'fullstack'
                session.add(job)
                updated_count += 1
            
            session.commit()
            print(f"\n✓ 已更新 {updated_count} 个React Native职位为fullstack")
        
        print(f"{'='*80}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="更新React Native Developer职位的role_family为fullstack")
    parser.add_argument(
        '--update',
        action='store_true',
        help='实际更新数据库（默认只检查不更新）'
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='跳过确认，直接更新（需要配合 --update 使用）'
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("更新React Native Developer职位的role_family为fullstack")
    print("="*80)
    print("\n原因：")
    print("- React Native开发者通常需要前后端知识")
    print("- React Native基于React，需要了解前端技术")
    print("- 需要与后端API集成")
    print()
    
    if args.update:
        if not args.yes:
            print("⚠️  警告：将实际更新数据库！")
            try:
                confirm = input("是否继续？(y/n): ")
                if confirm.lower() != 'y':
                    print("已取消")
                    sys.exit(0)
            except EOFError:
                print("错误：无法读取输入。请使用 --yes 参数跳过确认，或手动运行脚本。")
                sys.exit(1)
        
        update_react_native_jobs(dry_run=False)
    else:
        print("当前为预览模式（dry_run），只检查不更新")
        print("要实际更新数据库，请添加 --update 参数")
        print("要跳过确认，请添加 --yes 参数")
        print()
        update_react_native_jobs(dry_run=True)
