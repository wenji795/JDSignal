"""查看日志文件"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def view_logs(log_type: str = 'app', lines: int = 100, follow: bool = False):
    """
    查看日志文件
    
    Args:
        log_type: 日志类型 ('app' 或 'error')
        lines: 显示的行数（默认100行）
        follow: 是否持续跟踪日志（类似tail -f）
    """
    log_dir = project_root / "logs"
    
    if not log_dir.exists():
        print("❌ logs目录不存在")
        return
    
    # 查找最新的日志文件
    if log_type == 'app':
        pattern = "app_*.log"
    elif log_type == 'error':
        pattern = "error_*.log"
    else:
        print(f"❌ 未知的日志类型: {log_type}")
        print("可用类型: 'app', 'error'")
        return
    
    log_files = sorted(log_dir.glob(pattern), reverse=True)
    
    if not log_files:
        print(f"❌ 未找到 {log_type} 日志文件")
        return
    
    log_file = log_files[0]  # 使用最新的日志文件
    print(f"📄 查看日志文件: {log_file.name}")
    print(f"📁 完整路径: {log_file}")
    print(f"{'='*80}\n")
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            
            if lines > 0:
                # 显示最后N行
                display_lines = all_lines[-lines:]
            else:
                # 显示所有行
                display_lines = all_lines
            
            for line in display_lines:
                print(line.rstrip())
            
            if follow:
                print("\n⏳ 持续跟踪日志（按 Ctrl+C 退出）...")
                import time
                try:
                    while True:
                        time.sleep(1)
                        new_lines = f.readlines()
                        if new_lines:
                            for line in new_lines:
                                print(line.rstrip())
                except KeyboardInterrupt:
                    print("\n✓ 停止跟踪")
                    
    except Exception as e:
        print(f"❌ 读取日志文件失败: {e}")


def list_log_files():
    """列出所有日志文件"""
    log_dir = project_root / "logs"
    
    if not log_dir.exists():
        print("❌ logs目录不存在")
        return
    
    log_files = sorted(log_dir.glob("*.log"), reverse=True)
    
    if not log_files:
        print("❌ 未找到日志文件")
        return
    
    print("📋 日志文件列表：\n")
    for log_file in log_files:
        size = log_file.stat().st_size
        size_mb = size / (1024 * 1024)
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        print(f"  {log_file.name}")
        print(f"    大小: {size_mb:.2f} MB")
        print(f"    修改时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='查看日志文件')
    parser.add_argument(
        '--type', '-t',
        choices=['app', 'error'],
        default='app',
        help='日志类型 (app 或 error)'
    )
    parser.add_argument(
        '--lines', '-n',
        type=int,
        default=100,
        help='显示的行数（默认100行，0表示显示全部）'
    )
    parser.add_argument(
        '--follow', '-f',
        action='store_true',
        help='持续跟踪日志（类似 tail -f）'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='列出所有日志文件'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_log_files()
    else:
        view_logs(log_type=args.type, lines=args.lines, follow=args.follow)
