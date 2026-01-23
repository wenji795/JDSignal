"""为Job表添加industry字段的迁移脚本"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.database import engine


def add_industry_field():
    """为Job表添加industry字段"""
    print("="*80)
    print("为Job表添加industry字段")
    print("="*80)
    
    try:
        with engine.connect() as conn:
            # 检查字段是否已存在
            result = conn.execute(text("PRAGMA table_info(job)"))
            columns = [row[1] for row in result]
            
            if 'industry' in columns:
                print("✓ industry字段已存在，跳过迁移")
                return
            
            # 添加industry字段
            print("正在添加industry字段...")
            conn.execute(text("ALTER TABLE job ADD COLUMN industry VARCHAR"))
            conn.commit()
            
            print("✓ 成功添加industry字段")
            
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    add_industry_field()
