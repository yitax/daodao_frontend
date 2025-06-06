"""
数据库迁移脚本，用于向Users表添加personality_id字段
"""

from sqlalchemy import text
from .models.database import engine, get_db
from .models.models import Base, User, AIPersonality


def migrate_users_table():
    """向Users表添加personality_id字段"""
    # 获取数据库连接
    db = next(get_db())
    connection = engine.connect()

    try:
        # 检查列是否已经存在
        result = connection.execute(text("PRAGMA table_info(users)")).fetchall()

        # 获取所有列名
        column_names = [row[1] for row in result]

        if "personality_id" not in column_names:
            print("添加 personality_id 列到用户表...")
            connection.execute(
                text(
                    "ALTER TABLE users ADD COLUMN personality_id INTEGER REFERENCES ai_personalities(id)"
                )
            )
            print("列添加成功！")
        else:
            print("personality_id 列已经存在，无需添加")

        # 提交事务
        connection.commit()
        print("迁移完成！")

    except Exception as e:
        print(f"迁移失败: {str(e)}")
        connection.rollback()
    finally:
        connection.close()


if __name__ == "__main__":
    print("开始用户表迁移...")
    migrate_users_table()
