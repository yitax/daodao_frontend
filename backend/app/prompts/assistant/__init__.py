"""
助手提示词模块
包含各种不同性格的AI助手的系统提示词和元数据
"""

from . import ruiji, xiaonuan, ledou, jian, qihang

# 所有助手列表
ASSISTANTS = [ruiji, xiaonuan, ledou, jian, qihang]

# 助手ID映射
ASSISTANT_MAP = {1: ruiji, 2: xiaonuan, 3: ledou, 4: jian, 5: qihang}

# 默认助手
DEFAULT_ASSISTANT = ruiji


def get_assistant(assistant_id):
    """
    根据ID获取助手提示词和元数据

    Args:
        assistant_id: 助手ID，如果不存在则返回默认助手

    Returns:
        tuple: (system_prompt, metadata)
    """
    assistant = ASSISTANT_MAP.get(assistant_id, DEFAULT_ASSISTANT)
    return assistant.SYSTEM_PROMPT, assistant.METADATA


def get_all_assistants_metadata():
    """
    获取所有助手的元数据

    Returns:
        list: 包含所有助手元数据的列表
    """
    result = []
    for i, assistant in ASSISTANT_MAP.items():
        metadata = assistant.METADATA.copy()
        metadata["id"] = i
        result.append(metadata)
    return result
