"""导出jobs和关键词到CSV"""
import sys
import csv
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))

from sqlmodel import Session, select
from app.database import engine
from app.models import Job, Extraction


def export_to_csv(output_file: str = "jobs_export.csv"):
    """导出jobs和关键词到CSV文件"""
    with Session(engine) as session:
        # 获取所有jobs和对应的extractions
        jobs = session.exec(select(Job).order_by(Job.captured_at.desc())).all()
        job_count = len(jobs)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入标题行
            writer.writerow([
                'job_id', 'title', 'company', 'location', 'source', 'url',
                'status', 'role_family', 'seniority', 'posted_date', 'captured_at',
                'years_required', 'degree_required',
                'top_skills', 'must_have_skills', 'nice_to_have_skills',
                'certifications', 'top_keywords'
            ])
            
            for job in jobs:
                extraction = session.exec(
                    select(Extraction).where(Extraction.job_id == job.id)
                ).first()
                
                # 提取关键词数据
                if extraction:
                    keywords_data = extraction.keywords_json.get("keywords", [])
                    must_have = extraction.must_have_json.get("keywords", [])
                    nice_to_have = extraction.nice_to_have_json.get("keywords", [])
                    certifications = extraction.certifications_json.get("certifications", [])
                    
                    # 获取top 10技能
                    top_skills = [k["term"] for k in keywords_data[:10] if k.get("category") == "language" or k.get("category") == "framework"]
                    top_keywords = [k["term"] for k in keywords_data[:10]]
                else:
                    top_skills = []
                    must_have = []
                    nice_to_have = []
                    certifications = []
                    top_keywords = []
                    extraction = None
                
                # 写入数据行
                writer.writerow([
                    str(job.id),
                    job.title,
                    job.company,
                    job.location or '',
                    job.source,
                    job.url or '',
                    job.status.value if job.status else '',
                    job.role_family or '',
                    job.seniority.value if job.seniority else '',
                    job.posted_date.isoformat() if job.posted_date else '',
                    job.captured_at.isoformat(),
                    extraction.years_required if extraction else '',
                    extraction.degree_required or '' if extraction else '',
                    ', '.join(top_skills),
                    ', '.join(must_have),
                    ', '.join(nice_to_have),
                    ', '.join(certifications),
                    ', '.join(top_keywords)
                ])
    
    print(f"✓ 已导出 {job_count} 条记录到 {output_file}")


if __name__ == "__main__":
    output_file = sys.argv[1] if len(sys.argv) > 1 else "jobs_export.csv"
    export_to_csv(output_file)