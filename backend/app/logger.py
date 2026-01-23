"""日志配置模块"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

# 创建logs目录
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

# 日志文件路径
log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
error_log_file = log_dir / f"error_{datetime.now().strftime('%Y%m%d')}.log"

# 配置日志格式
log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 创建根日志记录器
logger = logging.getLogger('jdsignal')
logger.setLevel(logging.DEBUG)

# 清除已有的处理器（避免重复添加）
logger.handlers.clear()

# 控制台处理器（INFO级别及以上）
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

# 文件处理器（所有级别，带轮转）
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5,  # 保留5个备份文件
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

# 错误日志文件处理器（ERROR级别及以上）
error_handler = RotatingFileHandler(
    error_log_file,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5,  # 保留5个备份文件
    encoding='utf-8'
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(log_format)
logger.addHandler(error_handler)

# 配置SQLAlchemy日志（减少数据库查询日志的噪音）
sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
sqlalchemy_logger.setLevel(logging.WARNING)  # 只记录WARNING及以上级别

# 配置uvicorn访问日志
uvicorn_access_logger = logging.getLogger('uvicorn.access')
uvicorn_access_logger.setLevel(logging.INFO)

def get_logger(name: str = None):
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称（通常是模块名）
    
    Returns:
        Logger实例
    """
    if name:
        return logger.getChild(name)
    return logger
