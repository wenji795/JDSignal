"""数据库配置和会话管理"""
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator

# SQLite数据库文件路径
import os
import stat
from pathlib import Path

# 获取数据库文件的绝对路径
db_dir = Path(__file__).parent.parent
db_path = db_dir / "jobs.db"

# 确保数据库目录存在且可写
db_path.parent.mkdir(parents=True, exist_ok=True)

# 确保数据库文件存在且可写
if db_path.exists():
    # 确保文件有写权限
    current_permissions = db_path.stat().st_mode
    # 添加写权限（如果还没有）
    if not (current_permissions & stat.S_IWRITE):
        os.chmod(db_path, current_permissions | stat.S_IWRITE)
else:
    # 如果文件不存在，创建空文件并设置权限
    db_path.touch()
    os.chmod(db_path, 0o644)

# 使用绝对路径，确保使用正确的路径格式
# 在 macOS/Linux 上，路径需要以 / 开头
db_absolute_path = str(db_path.absolute())
# 确保路径格式正确（SQLite 需要绝对路径）
# 注意：SQLite连接字符串不需要查询参数，直接使用文件路径即可
DATABASE_URL = f"sqlite:///{db_absolute_path}"

# 创建数据库引擎
# 添加更多连接参数以确保可以写入
engine = create_engine(
    DATABASE_URL, 
    connect_args={
        "check_same_thread": False,
        "timeout": 30.0,  # 增加超时时间
    }, 
    echo=True,
    pool_pre_ping=True,  # 连接前ping数据库
)


def create_db_and_tables():
    """创建数据库表"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """获取数据库会话"""
    with Session(engine) as session:
        yield session