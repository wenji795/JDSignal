"""Analytics API测试"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from datetime import datetime, timedelta
from uuid import uuid4

from app.main import app
from app.database import get_session
from app.models import Job, Extraction, JobStatus, Seniority
from app.extractors.keyword_extractor import extract_and_save


@pytest.fixture(name="session")
def session_fixture():
    """测试数据库会话"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """测试客户端"""
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_trends_keyword_growth(client: TestClient, session: Session):
    """测试关键词增长分析"""
    now = datetime.utcnow()
    
    # 创建前半段（10天前）的jobs
    first_half_date = now - timedelta(days=5)
    first_half_jobs = []
    for i in range(3):
        job = Job(
            id=uuid4(),
            source="test",
            title=f"Job {i+1}",
            company="Company A",
            jd_text=f"Python developer with Django. Python is essential. React is nice to have.",
            captured_at=first_half_date,
            status=JobStatus.NEW,
            role_family="backend",
            seniority=Seniority.MID
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        
        # 运行提取
        extract_and_save(job.id, job.jd_text, session)
        first_half_jobs.append(job)
    
    # 创建后半段（2天前）的jobs，包含更多Python关键词
    second_half_date = now - timedelta(days=1)
    second_half_jobs = []
    for i in range(3):
        job = Job(
            id=uuid4(),
            source="test",
            title=f"Job {i+4}",
            company="Company B",
            jd_text=f"Python, Python, Python! Django and FastAPI required. React and Node.js preferred.",
            captured_at=second_half_date,
            status=JobStatus.NEW,
            role_family="backend",
            seniority=Seniority.SENIOR
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        
        # 运行提取
        extract_and_save(job.id, job.jd_text, session)
        second_half_jobs.append(job)
    
    # 调用trends端点
    response = client.get("/analytics/trends?days=30")
    assert response.status_code == 200
    
    data = response.json()
    
    # 验证基本结构
    assert "total_jobs" in data
    assert "count_by_role_family" in data
    assert "count_by_seniority" in data
    assert "top_keywords" in data
    assert "top_keywords_by_role_family" in data
    assert "keyword_growth" in data
    
    # 验证总职位数
    assert data["total_jobs"] == 6
    
    # 验证关键词增长
    keyword_growth = data["keyword_growth"]
    assert "Python" in keyword_growth
    
    python_growth = keyword_growth["Python"]
    assert "first_half_count" in python_growth
    assert "second_half_count" in python_growth
    assert "delta" in python_growth
    assert "percent_change" in python_growth
    
    # Python在后半段应该更多（因为JD中出现了更多次）
    assert python_growth["second_half_count"] >= python_growth["first_half_count"]
    assert python_growth["delta"] >= 0
    
    # 验证top_keywords
    top_keywords = data["top_keywords"]
    assert len(top_keywords) > 0
    assert any(kw["term"] == "Python" for kw in top_keywords)
    
    # 验证count_by_role_family
    count_by_role_family = data["count_by_role_family"]
    assert "backend" in count_by_role_family
    assert count_by_role_family["backend"] == 6
    
    # 验证count_by_seniority
    count_by_seniority = data["count_by_seniority"]
    assert "mid" in count_by_seniority
    assert "senior" in count_by_seniority