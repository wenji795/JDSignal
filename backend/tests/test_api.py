"""API测试"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.database import get_session
from app.models import Job


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


def test_create_job(client: TestClient):
    """测试创建职位"""
    response = client.post(
        "/api/jobs",
        json={
            "title": "Test Job",
            "company": "Test Company",
            "description": "Test description with Python and React skills required."
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Job"
    assert data["company"] == "Test Company"
    assert data["id"] is not None


def test_get_job(client: TestClient, session: Session):
    """测试获取职位"""
    job = Job(
        title="Test Job",
        company="Test Company",
        description="Test description"
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    response = client.get(f"/api/jobs/{job.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Job"


def test_list_jobs(client: TestClient, session: Session):
    """测试列出职位"""
    job1 = Job(title="Job 1", company="Company 1", description="Desc 1")
    job2 = Job(title="Job 2", company="Company 2", description="Desc 2")
    session.add(job1)
    session.add(job2)
    session.commit()

    response = client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_extract_keywords(client: TestClient, session: Session):
    """测试关键词提取"""
    job = Job(
        title="Python Developer",
        company="TechCorp",
        description="We need a Python developer with 5+ years of experience. React and Docker skills required."
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    response = client.post(f"/api/analytics/jobs/{job.id}/extract")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job.id
    assert data["total_count"] > 0
    assert len(data["extracted_keywords"]) > 0