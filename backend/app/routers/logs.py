"""日志查看API端点"""
from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
from typing import Optional

from app.logger import get_logger

router = APIRouter(prefix="/logs", tags=["logs"])
logger = get_logger(__name__)

# 获取backend目录路径
# logs.py 在 backend/app/routers/logs.py，需要向上3级才能到达 backend 目录
backend_dir = Path(__file__).parent.parent.parent


@router.get("/list")
def list_log_files():
    """列出所有日志文件"""
    log_dir = backend_dir / "logs"
    
    if not log_dir.exists():
        return {
            "message": "logs目录不存在",
            "files": []
        }
    
    log_files = []
    for log_file in sorted(log_dir.glob("*.log"), reverse=True):
        try:
            stat = log_file.stat()
            log_files.append({
                "name": log_file.name,
                "size": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": stat.st_mtime,
                "type": "app" if log_file.name.startswith("app_") else "error" if log_file.name.startswith("error_") else "other"
            })
        except Exception as e:
            logger.error(f"读取日志文件信息失败: {log_file.name}, {e}")
    
    return {
        "log_dir": str(log_dir),
        "files": log_files,
        "count": len(log_files)
    }


@router.get("/view")
def view_logs(
    log_type: str = Query("app", description="日志类型 (app 或 error)"),
    lines: int = Query(100, description="显示的行数（默认100行，0表示显示全部）"),
    tail: bool = Query(True, description="是否只显示最后N行（默认True）")
):
    """查看日志文件内容"""
    if log_type not in ['app', 'error']:
        raise HTTPException(status_code=400, detail="log_type必须是'app'或'error'")
    
    log_dir = backend_dir / "logs"
    
    if not log_dir.exists():
        raise HTTPException(status_code=404, detail="logs目录不存在")
    
    # 查找最新的日志文件
    pattern = f"{log_type}_*.log"
    log_files = sorted(log_dir.glob(pattern), reverse=True)
    
    if not log_files:
        raise HTTPException(status_code=404, detail=f"未找到 {log_type} 日志文件")
    
    log_file = log_files[0]
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            
            if lines > 0 and tail:
                # 显示最后N行
                display_lines = all_lines[-lines:]
            elif lines > 0:
                # 显示前N行
                display_lines = all_lines[:lines]
            else:
                # 显示所有行
                display_lines = all_lines
            
            return {
                "file": log_file.name,
                "path": str(log_file),
                "total_lines": len(all_lines),
                "display_lines": len(display_lines),
                "content": "".join(display_lines)
            }
    except Exception as e:
        logger.error(f"读取日志文件失败: {log_file}, {e}")
        raise HTTPException(status_code=500, detail=f"读取日志文件失败: {str(e)}")


@router.get("/latest")
def get_latest_logs(
    log_type: str = Query("app", description="日志类型 (app 或 error)"),
    lines: int = Query(50, description="显示的行数（默认50行）")
):
    """获取最新的日志内容（简化版）"""
    if log_type not in ['app', 'error']:
        raise HTTPException(status_code=400, detail="log_type必须是'app'或'error'")
    
    log_dir = backend_dir / "logs"
    
    if not log_dir.exists():
        return {
            "file": None,
            "lines": [],
            "message": "logs目录不存在"
        }
    
    # 查找最新的日志文件
    pattern = f"{log_type}_*.log"
    log_files = sorted(log_dir.glob(pattern), reverse=True)
    
    if not log_files:
        return {
            "file": None,
            "lines": [],
            "message": f"未找到 {log_type} 日志文件"
        }
    
    log_file = log_files[0]
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            display_lines = all_lines[-lines:] if lines > 0 else all_lines
            
            return {
                "file": log_file.name,
                "total_lines": len(all_lines),
                "lines": [line.rstrip() for line in display_lines]
            }
    except Exception as e:
        logger.error(f"读取日志文件失败: {log_file}, {e}")
        raise HTTPException(status_code=500, detail=f"读取日志文件失败: {str(e)}")
