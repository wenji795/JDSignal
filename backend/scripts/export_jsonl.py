"""导出原始JD和提取结果到JSONL"""
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir.parent))

from sqlmodel import Session, select
from app.database import engine
from app.models import Job, Extraction


def export_to_jsonl(output_file: str = "jobs_export.jsonl"):
    """导出原始JD和提取结果到JSONL文件"""
    with Session(engine) as session:
        # 获取所有jobs和对应的extractions
        jobs = session.exec(select(Job).order_by(Job.captured_at.desc())).all()
        job_count = len(jobs)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for job in jobs:
                extraction = session.exec(
                    select(Extraction).where(Extraction.job_id == job.id)
                ).first()
                
                # 构建导出记录
                record = {
                    "job": {
                        "id": str(job.id),
                        "source": job.source,
                        "url": job.url,
                        "title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "posted_date": job.posted_date.isoformat() if job.posted_date else None,
                        "captured_at": job.captured_at.isoformat(),
                        "jd_text": job.jd_text,
                        "status": job.status.value if job.status else None,
                        "role_family": job.role_family,
                        "seniority": job.seniority.value if job.seniority else None,
                    },
                    "extraction": None
                }
                
                if extraction:
                    record["extraction"] = {
                        "id": str(extraction.id),
                        "keywords_json": extraction.keywords_json,
                        "must_have_json": extraction.must_have_json,
                        "nice_to_have_json": extraction.nice_to_have_json,
                        "years_required": extraction.years_required,
                        "degree_required": extraction.degree_required,
                        "certifications_json": extraction.certifications_json,
                        "extracted_at": extraction.extracted_at.isoformat()
                    }
                
                # 写入JSONL（每行一个JSON对象）
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"✓ 已导出 {job_count} 条记录到 {output_file}")


if __name__ == "__main__":
    output_file = sys.argv[1] if len(sys.argv) > 1 else "jobs_export.jsonl"
    export_to_jsonl(output_file)