"""清理数据库中非新西兰的职位"""
import sys
import argparse
from pathlib import Path
from typing import Optional

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine
from app.models import Job, Extraction

# 使用与主应用相同的数据库路径
db_path = backend_dir / "jobs.db"
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def is_nz_location(location: Optional[str]) -> bool:
    """
    检查location是否在新西兰
    
    Args:
        location: 地点字符串
        
    Returns:
        True如果是新西兰，False否则
    """
    if not location:
        return False
    
    location_lower = location.lower()
    
    # 新西兰城市和地区关键词
    nz_keywords = [
        'new zealand', 'nz', 'auckland', 'wellington', 'christchurch', 
        'hamilton', 'dunedin', 'tauranga', 'lower hutt', 'palmerston north',
        'napier', 'rotorua', 'new plymouth', 'whangarei', 'invercargill',
        'nelson', 'hastings', 'gisborne', 'blenheim', 'timaru',
        'queenstown', 'wanganui', 'masterton', 'levin', 'otago',
        'canterbury', 'waikato', 'bay of plenty', 'manawatu', 'taranaki',
        'northland', 'southland', 'westland', 'marlborough', 'tasman'
    ]
    
    # 检查是否包含新西兰关键词
    for keyword in nz_keywords:
        if keyword in location_lower:
            return True
    
    # 排除澳大利亚的地点
    au_keywords = [
        'australia', 'au', 'sydney', 'melbourne', 'brisbane', 'perth',
        'adelaide', 'gold coast', 'newcastle', 'canberra', 'sunshine coast',
        'wollongong', 'hobart', 'geelong', 'townsville', 'cairns',
        'darwin', 'toowoomba', 'ballarat', 'bendigo', 'albury',
        'launceston', 'mackay', 'rockhampton', 'bunbury', 'bundaberg',
        'coffs harbour', 'wagga wagga', 'hervey bay', 'port macquarie',
        'shepparton', 'gladstone', 'mildura', 'tamworth', 'traralgon',
        'orange', 'bowral', 'geraldton', 'nowra', 'bathurst',
        'warrnambool', 'albany', 'kalgoorlie', 'broome', 'mount gambier',
        'queensland', 'qld', 'new south wales', 'nsw', 'victoria', 'vic',
        'western australia', 'wa', 'south australia', 'sa', 'tasmania', 'tas',
        'northern territory', 'nt', 'australian capital territory', 'act'
    ]
    
    # 如果包含澳大利亚关键词，返回False
    for keyword in au_keywords:
        if keyword in location_lower:
            return False
    
    # 排除美国的地点
    us_keywords = [
        'united states', 'usa', 'us', 'america', 'american',
        'california', 'ca', 'texas', 'tx', 'new york', 'ny', 'florida', 'fl',
        'san francisco', 'los angeles', 'san diego', 'chicago', 'houston', 'phoenix',
        'philadelphia', 'san antonio', 'dallas', 'austin', 'seattle', 'portland',
        'boston', 'detroit', 'nashville', 'las vegas', 'atlanta', 'miami',
        'remote us', 'remote usa', 'us remote', 'usa remote', 'united states remote'
    ]
    
    # 如果包含美国关键词，返回False
    for keyword in us_keywords:
        if keyword in location_lower:
            return False
    
    # 如果没有明确标识，默认返回False（保守策略）
    return False


def clean_non_nz_jobs(dry_run: bool = True):
    """
    清理数据库中非新西兰的职位
    
    Args:
        dry_run: 如果为True，只显示将要删除的职位，不实际删除
    """
    with Session(engine) as session:
        # 获取所有jobs
        all_jobs = session.exec(select(Job)).all()
        total_count = len(all_jobs)
        
        # 找出非新西兰的职位
        non_nz_jobs = []
        for job in all_jobs:
            # 检查URL是否包含非新西兰域名
            if job.url:
                url_lower = job.url.lower()
                if 'seek.com.au' in url_lower or 'indeed.com.au' in url_lower:
                    non_nz_jobs.append(job)
                    continue
            
            # 检查location字段
            if not is_nz_location(job.location):
                non_nz_jobs.append(job)
        
        non_nz_count = len(non_nz_jobs)
        
        print(f"总职位数: {total_count}")
        print(f"非新西兰职位数: {non_nz_count}")
        print()
        
        if non_nz_count == 0:
            print("✓ 没有发现非新西兰的职位")
            return
        
        # 显示将要删除的职位
        print("以下职位将被删除:")
        print("-" * 80)
        for job in non_nz_jobs[:20]:  # 只显示前20个
            print(f"ID: {job.id}, 标题: {job.title}, 公司: {job.company}, 地点: {job.location}, URL: {job.url}")
        if non_nz_count > 20:
            print(f"... 还有 {non_nz_count - 20} 个职位")
        print("-" * 80)
        print()
        
        if dry_run:
            print("⚠️  这是预览模式（dry-run），没有实际删除任何数据")
            print("   要实际删除，请运行: python clean_non_nz_jobs.py --delete")
        else:
            # 实际删除
            deleted_count = 0
            for job in non_nz_jobs:
                # 先删除关联的Extraction记录
                extraction = session.exec(
                    select(Extraction).where(Extraction.job_id == job.id)
                ).first()
                if extraction:
                    session.delete(extraction)
                
                # 删除Job记录
                session.delete(job)
                deleted_count += 1
            
            session.commit()
            print(f"✓ 已删除 {deleted_count} 个非新西兰职位及其关联的提取数据")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="清理数据库中非新西兰的职位")
    parser.add_argument(
        "--delete",
        action="store_true",
        help="实际删除非新西兰职位（默认只预览）"
    )
    args = parser.parse_args()
    
    clean_non_nz_jobs(dry_run=not args.delete)
