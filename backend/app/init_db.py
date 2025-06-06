"""
数据库初始化脚本，用于导入助手配置到数据库
"""

from sqlalchemy.orm import Session
from .models.database import get_db, engine
from .models.models import Base, AIPersonality
from .prompts.assistant import ASSISTANT_MAP


def init_db():
    """初始化数据库"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)


def import_assistants():
    """将预定义的助手导入到数据库"""
    db = next(get_db())

    try:
        # 清空原有助手表
        db.query(AIPersonality).delete()
        db.commit()

        # 导入所有助手
        for assistant_id, assistant in ASSISTANT_MAP.items():
            metadata = assistant.METADATA
            # 创建助手记录
            db_assistant = AIPersonality(
                id=assistant_id,
                name=metadata["name"],
                description=metadata["description"],
                system_prompt=assistant.SYSTEM_PROMPT,
                is_default=assistant_id == 1,  # 设置第一个助手为默认
            )
            db.add(db_assistant)

        db.commit()
        print(f"成功导入 {len(ASSISTANT_MAP)} 个助手配置到数据库")

    except Exception as e:
        db.rollback()
        print(f"导入助手配置失败: {str(e)}")
        raise


if __name__ == "__main__":
    print("初始化数据库...")
    init_db()
    print("导入助手配置...")
    import_assistants()
    print("数据库初始化完成!")
