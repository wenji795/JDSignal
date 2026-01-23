"""清理和重新分类QA职位的数据清理脚本"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import Session, select
from app.database import engine
from app.models import Job
from app.extractors.role_inferrer import infer_role_family


def analyze_qa_jobs():
    """分析数据库中的QA职位"""
    print("="*80)
    print("分析数据库中的QA/Quality Assurance职位")
    print("="*80)
    
    with Session(engine) as session:
        # 查找所有QA相关的职位
        qa_keywords = ['qa', 'quality', 'test', 'testing']
        
        all_jobs = session.exec(select(Job)).all()
        qa_jobs = []
        
        for job in all_jobs:
            title_lower = job.title.lower()
            if any(keyword in title_lower for keyword in qa_keywords):
                qa_jobs.append(job)
        
        print(f"\n找到 {len(qa_jobs)} 个QA相关职位\n")
        
        # 分类统计
        stats = {
            'it_qa': [],
            'non_it_qa': [],
            'unknown_qa': [],
            'wrong_role_family': []
        }
        
        for job in qa_jobs:
            title_lower = job.title.lower()
            jd_text_lower = (job.jd_text or "").lower()
            industry_lower = (job.industry or "").lower()
            
            # 检查是否是非IT行业
            non_it_industry_keywords = [
                'manufacturing', 'transport', 'logistics', 'warehouse',
                'food', 'beverage', 'food safety', 'food production',
                'science', 'scientific', 'laboratory', 'research',
                'pharmaceutical', 'biotechnology', 'biotech',
                'agriculture', 'farming', 'horticulture',
                'retail', 'wholesale', 'distribution',
                'construction', 'building', 'civil engineering',
                'automotive', 'healthcare', 'medical', 'health'
            ]
            
            is_non_it_industry = any(keyword in industry_lower for keyword in non_it_industry_keywords)
            
            # 检查JD中是否有IT相关关键词
            it_keywords = [
                'software', 'qa', 'test', 'testing', 'automation', 'selenium', 'cypress',
                'test automation', 'qa engineer', 'test engineer', 'qa specialist',
                'quality assurance engineer', 'software testing', 'manual testing',
                'api testing', 'performance testing', 'security testing', 'it ',
                'information technology', 'application', 'system', 'web', 'mobile',
                'agile', 'scrum', 'devops', 'ci/cd', 'continuous integration',
                'bug', 'defect', 'test case', 'test plan', 'test script',
                'jira', 'testrail', 'quality center', 'test management'
            ]
            
            has_it_context = any(keyword in jd_text_lower for keyword in it_keywords)
            
            # 检查是否是制造/生产相关的Quality
            manufacturing_keywords = [
                'manufacturing', 'production', 'factory', 'plant', 'assembly',
                'food safety', 'haccp', 'iso 9001', 'iso 22000', 'gmp',
                'product quality', 'material quality', 'process quality',
                'inspection', 'sampling', 'batch', 'lot', 'packaging',
                'supply chain', 'warehouse', 'logistics', 'distribution'
            ]
            
            has_manufacturing_context = any(keyword in jd_text_lower for keyword in manufacturing_keywords)
            
            # 分类
            if is_non_it_industry or (has_manufacturing_context and not has_it_context):
                stats['non_it_qa'].append(job)
            elif has_it_context or (not is_non_it_industry and not has_manufacturing_context):
                stats['it_qa'].append(job)
                # 检查角色族是否正确
                current_role_family = job.role_family or "未分类"
                expected_role_family = infer_role_family(job.title, job.jd_text or "")
                if current_role_family != expected_role_family and expected_role_family in ['testing', 'qa']:
                    stats['wrong_role_family'].append((job, current_role_family, expected_role_family))
            else:
                stats['unknown_qa'].append(job)
        
        # 打印统计信息
        print("分类统计：")
        print("-" * 80)
        print(f"  IT QA职位: {len(stats['it_qa'])} 个")
        print(f"  非IT QA职位（应删除）: {len(stats['non_it_qa'])} 个")
        print(f"  未知类型QA职位: {len(stats['unknown_qa'])} 个")
        print(f"  角色族分类错误: {len(stats['wrong_role_family'])} 个")
        print()
        
        # 打印非IT QA职位详情
        if stats['non_it_qa']:
            print("⚠️  非IT行业的QA职位（建议删除）：")
            print("-" * 80)
            for job in stats['non_it_qa']:
                print(f"  - {job.title} at {job.company}")
                print(f"    行业: {job.industry or '未知'}")
                print(f"    角色族: {job.role_family or '未分类'}")
                print(f"    URL: {job.url}")
                print()
        
        # 打印角色族分类错误的职位
        if stats['wrong_role_family']:
            print("⚠️  角色族分类错误的IT QA职位：")
            print("-" * 80)
            for job, old_rf, new_rf in stats['wrong_role_family']:
                print(f"  - {job.title} at {job.company}")
                print(f"    当前角色族: {old_rf} -> 应该: {new_rf}")
                print()
        
        return stats


def cleanup_qa_jobs(dry_run=True):
    """清理和重新分类QA职位"""
    print("="*80)
    print(f"{'[DRY RUN] ' if dry_run else ''}清理和重新分类QA职位")
    print("="*80)
    
    stats = analyze_qa_jobs()
    
    with Session(engine) as session:
        updated_count = 0
        deleted_count = 0
        
        # 1. 重新分类IT QA职位的角色族
        print("\n1. 重新分类IT QA职位的角色族...")
        print("-" * 80)
        for job in stats['it_qa']:
            current_role_family = job.role_family or "未分类"
            expected_role_family = infer_role_family(job.title, job.jd_text or "")
            
            if expected_role_family in ['testing', 'qa'] and current_role_family != expected_role_family:
                if not dry_run:
                    job.role_family = expected_role_family
                    session.add(job)
                print(f"✓ {'[DRY RUN] ' if dry_run else ''}更新: {job.title}")
                print(f"  角色族: {current_role_family} -> {expected_role_family}")
                updated_count += 1
        
        # 2. 删除非IT QA职位
        print("\n2. 删除非IT QA职位...")
        print("-" * 80)
        for job in stats['non_it_qa']:
            if not dry_run:
                # 先删除关联的Extraction记录
                from app.models import Extraction
                extraction = session.exec(select(Extraction).where(Extraction.job_id == job.id)).first()
                if extraction:
                    session.delete(extraction)
                session.delete(job)
            print(f"✓ {'[DRY RUN] ' if dry_run else ''}删除: {job.title} at {job.company}")
            print(f"  原因: 非IT行业QA职位 (行业: {job.industry or '未知'})")
            deleted_count += 1
        
        # 3. 处理角色族分类错误的职位
        print("\n3. 修复角色族分类错误的职位...")
        print("-" * 80)
        for job, old_rf, new_rf in stats['wrong_role_family']:
            if not dry_run:
                job.role_family = new_rf
                session.add(job)
            print(f"✓ {'[DRY RUN] ' if dry_run else ''}修复: {job.title}")
            print(f"  角色族: {old_rf} -> {new_rf}")
            updated_count += 1
        
        if not dry_run:
            session.commit()
            print(f"\n✓ 成功更新 {updated_count} 个职位，删除 {deleted_count} 个非IT QA职位")
        else:
            print(f"\n[DRY RUN] 将更新 {updated_count} 个职位，删除 {deleted_count} 个非IT QA职位")
            print("运行时不带 --dry-run 参数来执行实际清理")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='清理和重新分类QA职位')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='只分析不执行（默认）'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='执行实际清理（需要明确指定）'
    )
    parser.add_argument(
        '--analyze-only',
        action='store_true',
        help='只分析不清理'
    )
    
    args = parser.parse_args()
    
    if args.analyze_only:
        analyze_qa_jobs()
    else:
        dry_run = not args.execute
        cleanup_qa_jobs(dry_run=dry_run)
