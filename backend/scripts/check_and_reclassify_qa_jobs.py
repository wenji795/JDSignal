"""检查数据库中的QA职位，根据行业信息重新分类角色族"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import Session, select
from app.database import engine
from app.models import Job
from app.extractors.role_inferrer import infer_role_family


def check_qa_jobs():
    """检查数据库中的QA职位"""
    print("="*80)
    print("检查数据库中的QA/Quality Assurance职位")
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
        
        # 按行业分类统计
        industry_stats = {}
        non_it_industries = []
        
        for job in qa_jobs:
            industry = job.industry or "未知行业"
            
            if industry not in industry_stats:
                industry_stats[industry] = []
            industry_stats[industry].append(job)
            
            # 检查是否是非IT行业
            industry_lower = industry.lower()
            non_it_keywords = [
                'manufacturing', 'transport', 'logistics', 'warehouse',
                'food', 'beverage', 'food safety',
                'science', 'scientific', 'laboratory', 'research',
                'pharmaceutical', 'biotechnology', 'biotech',
                'agriculture', 'farming', 'horticulture',
                'retail', 'wholesale', 'distribution',
                'construction', 'building', 'civil engineering',
                'automotive'
            ]
            
            if any(keyword in industry_lower for keyword in non_it_keywords):
                non_it_industries.append(job)
        
        # 打印统计信息
        print("行业分布：")
        print("-" * 80)
        for industry, jobs in sorted(industry_stats.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {industry}: {len(jobs)} 个职位")
        print()
        
        # 打印非IT行业的QA职位
        if non_it_industries:
            print(f"⚠️  发现 {len(non_it_industries)} 个非IT行业的QA职位：")
            print("-" * 80)
            for job in non_it_industries:
                print(f"  - {job.title} at {job.company}")
                print(f"    行业: {job.industry or '未知'}")
                print(f"    角色族: {job.role_family or '未分类'}")
                print(f"    URL: {job.url}")
                print()
        
        # 检查角色族分类
        print("\n角色族分类情况：")
        print("-" * 80)
        role_family_stats = {}
        for job in qa_jobs:
            role_family = job.role_family or "未分类"
            if role_family not in role_family_stats:
                role_family_stats[role_family] = []
            role_family_stats[role_family].append(job)
        
        for role_family, jobs in sorted(role_family_stats.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {role_family}: {len(jobs)} 个职位")
        
        # 询问是否重新分类
        print("\n" + "="*80)
        print("建议操作：")
        print("1. 非IT行业的QA职位应该被过滤（不抓取）")
        print("2. IT行业的QA职位应该分类为 'qa' 或 'testing' 角色族")
        print("3. 可以使用以下命令重新分类角色族：")
        print("   python scripts/reclassify_qa_jobs.py")
        print("="*80)


def reclassify_qa_jobs():
    """重新分类QA职位的角色族"""
    print("="*80)
    print("重新分类QA职位的角色族")
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
        
        updated_count = 0
        
        for job in qa_jobs:
            # 检查是否是非IT行业
            industry_lower = (job.industry or "").lower()
            non_it_keywords = [
                'manufacturing', 'transport', 'logistics', 'warehouse',
                'food', 'beverage', 'food safety',
                'science', 'scientific', 'laboratory', 'research',
                'pharmaceutical', 'biotechnology', 'biotech',
                'agriculture', 'farming', 'horticulture',
                'retail', 'wholesale', 'distribution',
                'construction', 'building', 'civil engineering',
                'automotive'
            ]
            
            is_non_it = any(keyword in industry_lower for keyword in non_it_keywords)
            
            # 检查JD中是否有IT相关关键词
            jd_text_lower = (job.jd_text or "").lower()
            it_keywords = [
                'software', 'qa', 'test', 'testing', 'automation', 'selenium',
                'test automation', 'qa engineer', 'test engineer',
                'quality assurance engineer', 'software testing',
                'api testing', 'performance testing', 'security testing',
                'it ', 'information technology', 'application', 'system',
                'web', 'mobile', 'agile', 'scrum', 'devops', 'ci/cd',
                'bug', 'defect', 'test case', 'test plan', 'test script',
                'jira', 'testrail', 'quality center', 'test management'
            ]
            
            has_it_context = any(keyword in jd_text_lower for keyword in it_keywords)
            
            # 决定角色族
            if is_non_it and not has_it_context:
                # 非IT行业的QA职位，标记为需要删除或标记
                print(f"⚠️  非IT行业QA职位: {job.title} (行业: {job.industry})")
                # 不更新角色族，保持原样或标记
            elif has_it_context or not is_non_it:
                # IT行业的QA职位，分类为qa或testing
                title_lower = job.title.lower()
                if 'automation' in title_lower or 'automation' in jd_text_lower:
                    new_role_family = 'qa'
                elif 'test' in title_lower:
                    new_role_family = 'testing'
                else:
                    new_role_family = 'qa'
                
                if job.role_family != new_role_family:
                    old_role_family = job.role_family or "未分类"
                    job.role_family = new_role_family
                    session.add(job)
                    updated_count += 1
                    print(f"✓ 更新: {job.title}")
                    print(f"  角色族: {old_role_family} -> {new_role_family}")
                    print(f"  行业: {job.industry or '未知'}")
        
        session.commit()
        
        print(f"\n✓ 成功更新 {updated_count} 个职位的角色族")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='检查或重新分类QA职位')
    parser.add_argument(
        '--reclassify',
        action='store_true',
        help='重新分类角色族（默认只检查）'
    )
    
    args = parser.parse_args()
    
    if args.reclassify:
        reclassify_qa_jobs()
    else:
        check_qa_jobs()
