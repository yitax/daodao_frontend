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


def import_assistants(force_reset=False):
    """将预定义的助手导入到数据库

    Args:
        force_reset: 是否强制清空并重置助手表
    """
    db = next(get_db())

    try:
        # 只有在force_reset为True时才清空原有助手表
        if force_reset:
            db.query(AIPersonality).delete()
            db.commit()
            print("已清空助手表")

        # 获取已存在的助手ID
        existing_assistant_ids = [a.id for a in db.query(AIPersonality.id).all()]
        imported_count = 0

        # 导入所有助手
        for assistant_id, assistant in ASSISTANT_MAP.items():
            # 如果助手已存在且不是强制重置模式，则跳过
            if assistant_id in existing_assistant_ids and not force_reset:
                continue

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
            imported_count += 1

        db.commit()
        if imported_count > 0:
            print(f"成功导入 {imported_count} 个新的助手配置到数据库")
        else:
            print("没有新的助手配置需要导入")

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
