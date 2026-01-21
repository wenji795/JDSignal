"""
测试关键词提取功能
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, create_engine
from app.models import Job, Extraction, JobStatus
from app.extractors.keyword_extractor import extract_and_save_sync
from app.database import create_db_and_tables

# 创建数据库连接
db_path = backend_dir / "jobs.db"
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 测试数据
test_jd = """
We are looking for a Senior Python Developer with 5+ years of experience.

Requirements:
- Python, FastAPI, PostgreSQL
- Docker, Kubernetes
- AWS experience preferred

Nice to have:
- React, TypeScript
- CI/CD experience
"""

def test_extraction():
    """测试提取功能"""
    print("="*60)
    print("测试关键词提取功能")
    print("="*60)
    
    # 确保数据库表存在
    create_db_and_tables()
    
    with Session(engine) as session:
        # 创建测试职位
        job = Job(
            source="test",
            title="Senior Python Developer",
            company="Test Company",
            jd_text=test_jd,
            status=JobStatus.NEW
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        
        print(f"\n创建测试职位: {job.title}")
        print(f"职位ID: {job.id}")
        
        # 测试提取
        print("\n开始提取关键词...")
        try:
            extract_and_save_sync(
                job.id,
                job.jd_text,
                session,
                job_title=job.title,
                company=job.company,
                use_ai=True
            )
            print("✓ 提取完成")
            
            # 获取提取结果
            from sqlmodel import select
            extraction = session.exec(
                select(Extraction).where(Extraction.job_id == job.id)
            ).first()
            
            if extraction:
                print(f"\n提取结果:")
                print(f"  方法: {extraction.extraction_method}")
                print(f"  关键词数量: {len(extraction.keywords_json.get('keywords', []))}")
                print(f"  摘要: {extraction.summary[:100] if extraction.summary else '无'}...")
                print("✓ 测试成功")
            else:
                print("✗ 未找到提取结果")
                
        except Exception as e:
            print(f"✗ 提取失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_extraction()
