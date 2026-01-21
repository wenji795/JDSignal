"""
清理数据库中的非IT岗位
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine
from app.models import Job, Extraction
from app.database import create_db_and_tables

# 使用与主应用相同的数据库路径
db_path = backend_dir / "jobs.db"
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def is_non_it_job(title: str, jd_text: str = "") -> bool:
    """
    检查职位是否是非IT岗位
    
    策略：
    1. 优先检查IT相关关键词，如果明确是IT岗位，返回False
    2. 检查非IT岗位的明确关键词组合
    3. 使用更精确的匹配，避免误判
    
    Args:
        title: 职位标题
        jd_text: 职位描述文本
    
    Returns:
        True如果是非IT岗位，False如果是IT岗位
    """
    title_lower = title.lower()
    text = f"{title} {jd_text}".lower()
    
    # IT岗位明确关键词（如果包含这些，肯定是IT岗位）
    it_keywords = [
        'software', 'developer', 'programmer', 'engineer', 'architect',
        'devops', 'sre', 'data engineer', 'data scientist', 'data analyst',
        'qa engineer', 'test engineer', 'quality engineer', 'automation engineer',
        'cloud engineer', 'security engineer', 'network engineer',
        'product manager', 'scrum master', 'agile', 'it ', 'information technology',
        'full stack', 'frontend', 'backend', 'mobile developer', 'ios developer',
        'android developer', 'web developer', 'ui developer', 'ux developer',
        'database', 'dba', 'system administrator', 'sysadmin', 'it support',
        'technical support', 'it support engineer', 'help desk', 'service desk',  # IT支持相关
        'business analyst', 'business intelligence', 'technical', 'tech lead', 
        'engineering manager', 'web development', 'team lead', 'qa analyst',
        'application support', 'dynamics', 'video encoder', 'data lead',  # 视频编码通常是IT相关
        'technical writer', 'technical documentation', 'technical content',  # 技术写作是IT相关
        'product marketing', 'ai solutions', 'test analyst', 'content specialist',  # IT相关岗位
        'marketing designer', 'instructional designer',  # IT相关的设计和内容岗位
        'data administrator', 'quality administrator', 'data and quality'  # 数据管理相关是IT岗位
    ]
    
    # 特殊处理：先检查明确的非IT岗位（优先级最高）
    # Site Engineer是建筑/施工相关，不是IT
    if 'site engineer' in title_lower:
        return True
    
    # Support Engineer需要检查上下文
    # 如果标题是"Support Engineer"但没有明确的IT支持描述，可能是非IT支持
    if 'support engineer' in title_lower:
        # 特殊处理：如果标题是"Level X.X Support Engineer"格式（如Level 2.5 Support Engineer）
        # 这类岗位通常是非IT支持（如设备支持、现场支持等），即使JD中可能提到IT相关词汇
        import re
        level_pattern = r'level\s+\d+\.?\d*\s+support\s+engineer'
        if re.search(level_pattern, title_lower):
            return True
        
        # 检查是否有明确的IT支持短语（需要更严格）
        it_support_indicators = [
            'it support', 'technical support', 'software support', 
            'system support', 'network support', 'cloud support',
            'application support', 'help desk', 'service desk',
            'computer support', 'server support', 'infrastructure support',
            'it help', 'technical help', 'information technology support'
        ]
        has_it_indicator = any(indicator in text for indicator in it_support_indicators)
        
        # 如果没有明确的IT指标，可能是非IT支持
        if not has_it_indicator:
            return True
    
    # 如果标题中包含明确的IT关键词，肯定是IT岗位
    if any(keyword in title_lower for keyword in it_keywords):
        return False
    
    # 非IT岗位的明确关键词组合（需要精确匹配）
    # 注意：先检查IT关键词，再检查非IT关键词
    non_it_patterns = [
        # 质量控制技术员（制造相关）
        r'quality\s+control\s+technician',
        r'qc\s+technician',
        r'quality\s+inspector',
        # 电气工程（非IT）- 使用简单匹配，因为已经排除了IT关键词
        r'electrical\s+engineer(?!.*(?:software|it|information\s+technology))',
        r'electrical\s+technician',
        r'electrical\s+designer',
        r'electrician',
        r'power\s+engineer',
        # 制造/生产（明确的生产岗位）
        r'production\s+technician',
        r'production\s+operator',
        r'manufacturing\s+technician',
        r'manufacturing\s+engineer',
        # 物流/运输
        r'logistics\s+',
        r'warehouse\s+',
        r'supply\s+chain\s+',
        # 生物技术/制药（明确的关键词）
        r'biotechnology',
        r'biotech\s+',
        r'pharmaceutical',
        r'bioora',
        r'car\s+t-cell',
        r'cell\s+therapy',
        # 机械/土木/结构工程
        r'mechanical\s+engineer',
        r'civil\s+engineer',
        r'structural\s+engineer',
        r'mechanical\s+designer',
        r'mechanical\s+technician',
        # 建筑/施工（建筑技术员，非IT架构师）
        r'architectural\s+technician',
        r'architectural\s+draftsperson',
        r'architectural\s+designer',
        r'construction\s+',
        r'site\s+engineer',  # 现场工程师/工地工程师（建筑/施工相关）
        # 实验室/科研技术员
        r'laboratory\s+technician',
        r'lab\s+technician',
        r'scientific\s+technician',
        r'research\s+technician',
        # 教育/教学辅助（排除IT技术写作和IT培训）
        r'reader\s*/\s*writer(?!.*(?:technical|software|it|developer))',  # Reader/Writer但不是技术写作
        r'teaching\s+aide(?!.*(?:technical|software|it))',
        r'teacher\s+aide(?!.*(?:technical|software|it))',
        r'learning\s+support(?!.*(?:technical|software|it|online))',  # Learning Support但不是技术学习支持
        r'education\s+support(?!.*(?:technical|software|it))',
        r'special\s+needs\s+',
        r'(?<!technical\s)(?<!software\s)(?<!it\s)teacher(?!.*(?:technical|software|it))',
        r'(?<!technical\s)(?<!software\s)educator(?!.*(?:technical|software|it))',
        r'(?<!technical\s)(?<!software\s)instructor(?!.*(?:technical|software|it))',
        r'(?<!technical\s)(?<!software\s)tutor(?!.*(?:technical|software|it))',
        r'lecturer(?!.*(?:technical|software|it))',
        r'professor(?!.*(?:technical|software|it))',
        r'curriculum\s+design(?!.*(?:technical|software|it))',  # 课程设计但不是技术课程
        r'principal\s+advisor(?!.*(?:technical|software|it))',  # 主要顾问但不是技术顾问
    ]
    
    # 检查是否匹配非IT岗位模式
    import re
    for pattern in non_it_patterns:
        try:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        except re.error:
            # 如果正则表达式有问题，跳过这个模式
            continue
    
    return False


def clean_non_it_jobs(dry_run: bool = True):
    """
    清理数据库中的非IT岗位
    
    Args:
        dry_run: 如果为True，只检查不删除；如果为False，会实际删除
    """
    # 确保数据库表存在
    create_db_and_tables()
    
    with Session(engine) as session:
        # 获取所有职位
        jobs = session.exec(select(Job)).all()
        
        print(f"找到 {len(jobs)} 个职位，开始检查非IT岗位...")
        print("="*80)
        
        non_it_jobs = []
        
        for i, job in enumerate(jobs, 1):
            if is_non_it_job(job.title, job.jd_text):
                non_it_jobs.append(job)
                if len(non_it_jobs) <= 20:  # 只显示前20个
                    print(f"  [{len(non_it_jobs)}] {job.title[:60]}...")
        
        print(f"\n{'='*80}")
        print(f"找到 {len(non_it_jobs)} 个非IT岗位")
        print(f"{'='*80}")
        
        if not non_it_jobs:
            print("没有需要清理的非IT岗位")
            return
        
        if dry_run:
            print("\n注意：这是预览模式（dry_run），数据库未被修改")
            print("要实际删除这些职位，请运行: python clean_non_it_jobs.py --delete")
        else:
            # 删除非IT岗位及其关联的Extraction
            deleted_count = 0
            for job in non_it_jobs:
                # 删除关联的Extraction
                extraction = session.exec(
                    select(Extraction).where(Extraction.job_id == job.id)
                ).first()
                if extraction:
                    session.delete(extraction)
                
                # 删除Job
                session.delete(job)
                deleted_count += 1
            
            session.commit()
            print(f"\n✓ 已删除 {deleted_count} 个非IT岗位")
        
        print(f"{'='*80}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="清理数据库中的非IT岗位")
    parser.add_argument(
        '--delete',
        action='store_true',
        help='实际删除非IT岗位（默认只检查不删除）'
    )
    parser.add_argument(
        '--yes',
        action='store_true',
        help='跳过确认，直接删除（需要配合 --delete 使用）'
    )
    
    args = parser.parse_args()
    
    print("="*80)
    print("清理数据库中的非IT岗位")
    print("="*80)
    print("\n排除的非IT岗位类型：")
    print("- 质量控制/质量保证（制造相关）")
    print("- 电气工程（非IT）")
    print("- 制造/生产")
    print("- 物流/运输")
    print("- 生物技术/制药")
    print("- 机械/土木/结构工程")
    print("- 建筑/施工")
    print("- 教育/教学辅助（Reader/Writer、Teaching Aide等）")
    print()
    
    if args.delete:
        if not args.yes:
            print("⚠️  警告：将实际删除非IT岗位！")
            try:
                confirm = input("是否继续？(y/n): ")
                if confirm.lower() != 'y':
                    print("已取消")
                    sys.exit(0)
            except EOFError:
                print("错误：无法读取输入。请使用 --yes 参数跳过确认，或手动运行脚本。")
                sys.exit(1)
        
        clean_non_it_jobs(dry_run=False)
    else:
        print("当前为预览模式（dry_run），只检查不删除")
        print("要实际删除非IT岗位，请添加 --delete 参数")
        print("要跳过确认，请添加 --yes 参数")
        print()
        clean_non_it_jobs(dry_run=True)
