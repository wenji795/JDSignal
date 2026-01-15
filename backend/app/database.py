"""数据库配置和会话管理"""
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator

# SQLite数据库文件路径
DATABASE_URL = "sqlite:///./jobs.db"

# 创建数据库引擎
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=True)


def create_db_and_tables():
    """创建数据库表"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """获取数据库会话"""
    with Session(engine) as session:
        yield session