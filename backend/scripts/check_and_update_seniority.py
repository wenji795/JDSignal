"""
检查并更新数据库中已有职位的资历级别
使用改进后的资历推断逻辑（基于经验年限）
"""
import sys
from pathlib import Path
from collections import defaultdict

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine
from app.models import Job, Seniority
from app.extractors.role_inferrer import infer_seniority
from app.database import create_db_and_tables

# 使用与主应用相同的数据库路径
db_path = backend_dir / "jobs.db"
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def check_and_update_seniority(dry_run: bool = True):
    """
    检查并更新所有职位的资历级别
    
    Args:
        dry_run: 如果为True，只检查不更新；如果为False，会实际更新数据库
    """
    # 确保数据库表存在
    create_db_and_tables()
    
    with Session(engine) as session:
        # 获取所有职位
        jobs = session.exec(select(Job)).all()
        
        print(f"找到 {len(jobs)} 个职位，开始检查资历级别...")
        print("="*80)
        
        # 统计信息
        stats = {
            'total': len(jobs),
            'no_change': 0,
            'changed': 0,
            'was_none': 0,
            'now_none': 0,
            'changes_by_type': defaultdict(int),
            'changes_detail': []
        }
        
        # 按资历级别统计
        current_distribution = defaultdict(int)
        new_distribution = defaultdict(int)
        
        for i, job in enumerate(jobs, 1):
            # 统计当前的资历分布
            if job.seniority:
                current_distribution[job.seniority.value] += 1
            else:
                current_distribution['None'] += 1
            
            # 使用新的逻辑重新推断资历级别
            new_seniority = infer_seniority(job.title, job.jd_text)
            
            # 统计新的资历分布
            if new_seniority:
                new_distribution[new_seniority.value] += 1
            else:
                new_distribution['None'] += 1
            
            # 对比现有和新的资历级别
            old_value = job.seniority.value if job.seniority else None
            new_value = new_seniority.value if new_seniority else None
            
            if old_value == new_value:
                stats['no_change'] += 1
            else:
                stats['changed'] += 1
                change_type = f"{old_value or 'None'} -> {new_value or 'None'}"
                stats['changes_by_type'][change_type] += 1
                
                # 记录详细信息（只记录前50个，避免输出过多）
                if len(stats['changes_detail']) < 50:
                    stats['changes_detail'].append({
                        'id': str(job.id)[:8],
                        'title': job.title[:60],
                        'company': job.company[:30] if job.company else 'N/A',
                        'old': old_value or 'None',
                        'new': new_value or 'None'
                    })
                
                # 如果不是dry_run，更新数据库
                if not dry_run:
                    job.seniority = new_seniority
                    session.add(job)
            
            # 显示进度（每100个职位显示一次）
            if i % 100 == 0:
                print(f"已处理 {i}/{len(jobs)} 个职位...")
        
        # 如果不是dry_run，提交更改
        if not dry_run:
            session.commit()
            print(f"\n✓ 已更新数据库")
        
        # 打印统计信息
        print(f"\n{'='*80}")
        print("统计结果")
        print(f"{'='*80}")
        print(f"总职位数: {stats['total']}")
        print(f"无需更改: {stats['no_change']}")
        print(f"需要更改: {stats['changed']}")
        print(f"原本为None: {stats['was_none']}")
        print(f"现在为None: {stats['now_none']}")
        
        print(f"\n{'='*80}")
        print("当前资历分布")
        print(f"{'='*80}")
        for level, count in sorted(current_distribution.items()):
            print(f"  {level:15s}: {count:5d}")
        
        print(f"\n{'='*80}")
        print("新的资历分布")
        print(f"{'='*80}")
        for level, count in sorted(new_distribution.items()):
            print(f"  {level:15s}: {count:5d}")
        
        if stats['changes_by_type']:
            print(f"\n{'='*80}")
            print("更改类型统计（前20个）")
            print(f"{'='*80}")
            sorted_changes = sorted(stats['changes_by_type'].items(), key=lambda x: x[1], reverse=True)
            for change_type, count in sorted_changes[:20]:
                print(f"  {change_type:30s}: {count:5d}")
        
        if stats['changes_detail']:
            print(f"\n{'='*80}")
            print("详细更改示例（前50个）")
            print(f"{'='*80}")
            print(f"{'ID':<10} {'标题':<40} {'公司':<20} {'旧值':<15} {'新值':<15}")
            print("-" * 80)
            for detail in stats['changes_detail']:
                print(f"{detail['id']:<10} {detail['title']:<40} {detail['company']:<20} {detail['old']:<15} {detail['new']:<15}")
        
        print(f"\n{'='*80}")
        if dry_run:
            print("注意：这是预览模式（dry_run），数据库未被修改")
            print("要实际更新数据库，请运行: python check_and_update_seniority.py --update")
        else:
            print("✓ 数据库已更新")
        print(f"{'='*80}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="检查并更新数据库中已有职位的资历级别")
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
    print("检查并更新数据库中已有职位的资历级别")
    print("使用改进后的资历推断逻辑（基于经验年限）")
    print("="*80)
    print("\n改进点：")
    print("- 优先检查标题中的明确级别关键词")
    print("- 提取JD中的经验年限要求")
    print("- 根据经验年限判断：0-2年=JUNIOR, 3-4年=MID, 5+年=SENIOR")
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
        
        check_and_update_seniority(dry_run=False)
    else:
        print("当前为预览模式（dry_run），只检查不更新")
        print("要实际更新数据库，请添加 --update 参数")
        print("要跳过确认，请添加 --yes 参数")
        print()
        check_and_update_seniority(dry_run=True)
