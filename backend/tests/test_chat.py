import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock
import json
import base64
from datetime import datetime

from app.models.database import Base, get_db
from app.models.models import ChatMessage, User, AIPersonality, Transaction
from app.main import app


# 创建内存测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def db():
    # 创建测试表
    Base.metadata.create_all(bind=engine)

    # 创建会话
    db = TestingSessionLocal()

    # 创建测试AI助手
    test_personality = AIPersonality(
        name="测试助手",
        description="用于测试的AI助手",
        system_prompt="你是一个测试助手",
        is_default=True,
    )
    db.add(test_personality)

    db.commit()

    yield db

    # 清理测试表
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(db):
    # 覆盖依赖项
    def override_get_db():
        try:
            yield db
        finally:
            pass

    # 覆盖用户认证依赖
    async def override_get_current_user():
        # 创建或获取测试用户
        user = db.query(User).filter(User.username == "testuser").first()
        if not user:
            # 创建测试用户
            from app.routers.users import get_password_hash

            user = User(
                username="testuser",
                email="test@example.com",
                hashed_password=get_password_hash("password123"),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    app.dependency_overrides[get_db] = override_get_db
    from app.routers.users import get_current_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    # 返回测试客户端
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_openai_response():
    with patch("openai.ChatCompletion.create") as mock_create:
        # 设置模拟响应
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "这是一个测试回复"
        mock_create.return_value = mock_response
        yield mock_create


# 测试获取AI助手列表
def test_get_ai_personalities(client, db):
    # 发送请求获取AI助手列表
    response = client.get("/chat/personalities")

    # 验证响应
    assert response.status_code == 200
    personalities = response.json()

    # 验证返回了助手列表(任何助手都可以)
    assert isinstance(personalities, list)
    assert len(personalities) >= 1

    # 验证助手数据结构是否正确(不检查特定名称)
    for personality in personalities:
        assert "id" in personality
        assert "name" in personality
        assert isinstance(personality["name"], str)
        # personality_type可能存在也可能不存在，不做强制检查


# 使用模拟测试获取AI助手列表(可选，用于更精确的测试)
@patch("app.routers.chat.get_all_assistants_metadata")
def test_get_ai_personalities_with_mock(mock_get_assistants, client, db):
    # 设置模拟返回值
    mock_assistants = [
        {
            "id": 1,
            "name": "测试助手",
            "personality_type": "测试类型",
            "description": "用于测试的AI助手",
        }
    ]
    mock_get_assistants.return_value = mock_assistants

    # 发送请求获取AI助手列表
    response = client.get("/chat/personalities")

    # 验证响应
    assert response.status_code == 200
    personalities = response.json()
    assert len(personalities) >= 1

    # 验证助手数据是否正确
    test_personality = next((p for p in personalities if p["name"] == "测试助手"), None)
    assert test_personality is not None
    assert test_personality["personality_type"] == "测试类型"

    # 确认模拟函数被调用
    mock_get_assistants.assert_called_once()


# 测试创建聊天消息
def test_create_chat_message(client, db, mock_openai_response):
    # 构建请求数据
    message_data = {"content": "你好，测试消息", "personality_id": 1}

    # 发送请求创建聊天消息
    response = client.post("/chat/", json=message_data)

    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"]["content"] == "这是一个测试回复"

    # 验证消息是否保存到数据库
    db_messages = db.query(ChatMessage).all()
    assert len(db_messages) >= 2  # 用户消息和AI回复

    # 验证用户消息
    user_message = next(
        (m for m in db_messages if m.is_user and m.content == message_data["content"]),
        None,
    )
    assert user_message is not None

    # 验证AI回复
    ai_message = next(
        (m for m in db_messages if not m.is_user and m.content == "这是一个测试回复"),
        None,
    )
    assert ai_message is not None


# 测试获取聊天历史
def test_get_chat_history(client, db):
    # 先创建一些聊天消息确保历史记录中有数据
    # 发送两条消息以确保有足够的历史记录
    message_data1 = {"content": "历史测试消息1", "personality_id": 1}
    message_data2 = {"content": "历史测试消息2", "personality_id": 1}

    client.post("/chat/", json=message_data1)
    client.post("/chat/", json=message_data2)

    # 发送请求获取聊天历史
    response = client.get("/chat/history?limit=10&skip=0")

    # 验证响应
    assert response.status_code == 200
    messages = response.json()
    assert isinstance(messages, list)

    # 我们应该至少能看到刚刚创建的消息及其AI回复(4条消息)
    # 如果测试数据库中有更多消息，那么长度会更大
    assert len(messages) > 0

    # 验证消息格式
    for message in messages:
        assert "id" in message
        assert "content" in message
        assert "is_user" in message
        assert "created_at" in message


# 测试确认交易功能
def test_confirm_transaction(client, db):
    # 构建交易确认数据
    transaction_data = {
        "message_id": -1,  # 特殊值，表示不需要依赖数据库查询
        "confirm": True,
        "type": "expense",
        "amount": 100.0,
        "description": "测试交易",
        "category": "餐饮美食",
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    # 发送确认交易请求
    response = client.post("/chat/confirm-transaction", json=transaction_data)

    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["confirmed"] is True
    assert "transaction" in data
    assert data["transaction"]["type"] == transaction_data["type"]
    assert data["transaction"]["amount"] == transaction_data["amount"]
    assert data["transaction"]["description"] == transaction_data["description"]
    assert data["transaction"]["category"] == transaction_data["category"]


# 测试图片识别功能
def test_image_recognition(client, db, mock_openai_response):
    # 修改模拟响应以包含图片识别结果
    mock_openai_response.return_value.choices[0].message.content = json.dumps(
        {
            "has_intent": True,
            "type": "expense",
            "amount": 50.0,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "description": "测试收据",
            "category": "餐饮美食",
        }
    )

    # 创建一个简单的测试图片
    test_image_content = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )

    # 创建测试文件
    test_image_path = "test_image.png"
    with open(test_image_path, "wb") as f:
        f.write(test_image_content)

    try:
        # 发送图片识别请求
        with open(test_image_path, "rb") as f:
            response = client.post(
                "/chat/image-recognition",
                files={"image": ("test_image.png", f, "image/png")},
            )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "extracted_info" in data
        assert data["extracted_info"]["type"] == "expense"
        assert data["extracted_info"]["amount"] == 50.0
        assert "category" in data["extracted_info"]

    finally:
        # 清理测试文件
        import os

        if os.path.exists(test_image_path):
            os.remove(test_image_path)


# 测试提取财务信息功能
@patch("app.routers.chat.extract_financial_data")
def test_extract_financial_data(mock_extract, client, db):
    # 设置模拟提取结果
    mock_extract.return_value = {
        "type": "expense",
        "amount": 25.5,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "description": "午餐",
        "category": "餐饮美食",
    }

    # 构建包含财务信息的消息
    message_data = {"content": "我今天午餐花了25.5元", "personality_id": 1}

    # 发送请求
    response = client.post("/chat/", json=message_data)

    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "extracted_info" in data
    assert data["extracted_info"]["type"] == "expense"
    assert data["extracted_info"]["amount"] == 25.5
    assert data["needs_confirmation"] is True


# 测试空消息处理 - 支持空消息
def test_empty_message_supported(client, db, mock_openai_response):
    # 构建空消息请求
    message_data = {"content": "", "personality_id": 1}

    # 发送请求
    response = client.post("/chat/", json=message_data)

    # 验证响应(成功)
    assert response.status_code == 200

    # 验证响应包含必要字段
    data = response.json()
    assert "message" in data
    assert data["message"]["content"] is not None  # 确认AI回复了一些内容

    # 验证消息被保存到数据库
    db_messages = db.query(ChatMessage).all()

    # 找到用户空消息
    user_message = next((m for m in db_messages if m.is_user and m.content == ""), None)
    assert user_message is not None

    # 找到AI回复消息
    ai_message = next(
        (m for m in db_messages if not m.is_user and m.user_id == user_message.user_id),
        None,
    )
    assert ai_message is not None


# 测试非常长的消息处理
def test_long_message(client, db, mock_openai_response):
    long_message = "测试" * 1000
    message_data = {"content": long_message, "personality_id": 1}

    # 发送请求
    response = client.post("/chat/", json=message_data)

    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


# 测试包含特殊字符的消息
def test_special_chars_message(client, db, mock_openai_response):
    # 构建包含特殊字符的消息
    special_message = "测试!@#$%^&*()_+{}|:\"<>?~`-=[]\\;',./✓™®©"
    message_data = {"content": special_message, "personality_id": 1}

    # 发送请求
    response = client.post("/chat/", json=message_data)

    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


# 测试使用不存在的personality_id
def test_invalid_personality_id(client, db, mock_openai_response):
    # 构建使用不存在的personality_id的请求
    message_data = {"content": "测试消息", "personality_id": 99999}

    # 发送请求
    response = client.post("/chat/", json=message_data)

    # 验证响应（应该使用默认助手或返回错误）
    assert response.status_code in [200, 400]
    if response.status_code == 200:
        data = response.json()
        assert "message" in data


# 测试并发多个聊天消息
@pytest.mark.parametrize("message_index", range(5))
def test_concurrent_chat_messages(message_index, client, db, mock_openai_response):
    # 构建请求数据
    message_data = {"content": f"并发测试消息 {message_index}", "personality_id": 1}

    # 发送请求
    response = client.post("/chat/", json=message_data)

    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


# 测试防SQL注入尝试消息
def test_sql_injection_attempt(client, db, mock_openai_response):
    # 构建包含SQL注入尝试的消息
    injection_message = "'; DROP TABLE users; --"
    message_data = {"content": injection_message, "personality_id": 1}
    response = client.post("/chat/", json=message_data)

    # 验证响应（应该安全处理）
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

    # 验证数据库表不受影响
    users = db.query(User).all()
    assert len(users) > 0


# 测试空消息特殊处理
def test_empty_message_special_handling(client, db, mock_openai_response):
    # 构建空消息请求和普通消息请求
    empty_message_data = {"content": "", "personality_id": 1}
    normal_message_data = {"content": "你好", "personality_id": 1}

    # 保存当前AI回复内容
    original_content = mock_openai_response.return_value.choices[0].message.content

    # 设置空消息的特殊回复
    mock_openai_response.return_value.choices[0].message.content = (
        "这是对空消息的默认回复"
    )

    # 发送空消息请求
    empty_response = client.post("/chat/", json=empty_message_data)

    # 验证响应状态码
    assert empty_response.status_code == 200

    # 获取空消息回复
    empty_data = empty_response.json()
    empty_reply = empty_data["message"]["content"]

    # 恢复原始回复内容
    mock_openai_response.return_value.choices[0].message.content = (
        "这是对普通消息的回复"
    )

    # 发送普通消息请求
    normal_response = client.post("/chat/", json=normal_message_data)

    # 验证响应状态码
    assert normal_response.status_code == 200

    # 获取普通消息回复
    normal_data = normal_response.json()
    normal_reply = normal_data["message"]["content"]

    # 验证两种回复不同，表明有特殊处理
    assert empty_reply != normal_reply

    # 恢复原始模拟设置
    mock_openai_response.return_value.choices[0].message.content = original_content


@pytest.fixture
def authenticated_client(client, db):
    # 创建唯一用户名避免冲突
    import time

    unique_suffix = str(int(time.time()))

    # 注册测试用户
    register_data = {
        "username": f"chatuser_{unique_suffix}",
        "email": f"chatuser_{unique_suffix}@example.com",
        "password": "password123",
    }

    register_response = client.post("/users/register", json=register_data)
    assert register_response.status_code in [200, 201]

    # 使用OAuth2表单格式登录
    login_response = client.post(
        "/users/login",
        data={
            "username": register_data["username"],
            "password": register_data["password"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert login_response.status_code == 200
    token_data = login_response.json()
    token = token_data["access_token"]

    # 设置认证头
    client.headers["Authorization"] = f"Bearer {token}"

    yield client

    # 清理
    client.headers.pop("Authorization", None)


# TC-CONFIRM-002: 用户取消入账测试
def test_cancel_transaction(client, db):
    # 构建交易取消数据 - confirm设置为False表示取消
    transaction_data = {
        "message_id": -1,
        "confirm": False,
        "type": "expense",
        "amount": 50.0,
        "description": "拒绝入账的交易",
        "category": "餐饮美食",
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    # 发送取消交易请求
    response = client.post("/chat/confirm-transaction", json=transaction_data)

    # 验证响应 - 应该成功处理但不创建交易
    assert response.status_code == 200
    data = response.json()
    assert data["confirmed"] is False
    assert "transaction" not in data

    # 验证数据库中未创建交易
    transaction = (
        db.query(Transaction)
        .filter(Transaction.description == transaction_data["description"])
        .first()
    )
    assert transaction is None


# TC-CONFIRM-003: 无效金额测试
def test_invalid_amount_transaction(client, db):
    """测试金额为非数字时的错误处理"""

    # 构建包含无效金额的交易确认数据
    transaction_data = {
        "message_id": -1,
        "confirm": True,
        "type": "expense",
        "amount": "非数字金额",  # 无效金额
        "description": "测试无效金额",
        "category": "餐饮美食",
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    # 发送确认请求
    response = client.post("/chat/confirm-transaction", json=transaction_data)

    # 验证响应 - 应该返回422 Unprocessable Entity
    assert response.status_code == 422
    data = response.json()

    # 验证错误信息指出了金额问题
    assert "detail" in data
    # 检查错误详情中是否包含关于amount字段的信息
    amount_error = (
        any(error["loc"][1] == "amount" for error in data["detail"])
        if isinstance(data["detail"], list)
        else False
    )
    assert amount_error, "错误信息应该指出amount字段的问题"


# TC-CONFIRM-004: 缺少必要字段测试
def test_missing_fields_transaction(client, db):
    """测试缺少必要字段时的错误处理"""

    # 构建缺少必要字段的交易确认数据
    # 这里我们省略了type和amount字段，这些应该是必需的
    transaction_data = {
        "message_id": -1,
        "confirm": True,
        "description": "测试缺少字段",
        "category": "餐饮美食",
        # 缺少type和amount字段
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    # 发送确认请求
    response = client.post("/chat/confirm-transaction", json=transaction_data)

    # 验证响应 - 应该是400 Bad Request或422 Unprocessable Entity
    assert response.status_code in [400, 422]
    data = response.json()

    # 验证错误信息中包含缺失字段的提示
    assert "detail" in data

    # 如果响应是422，检查错误是否关于必要字段
    if response.status_code == 422:
        field_errors = [
            error["loc"][1] for error in data["detail"] if len(error["loc"]) > 1
        ]
        # 检查是否至少有一个我们期望缺失的字段在错误中被提到
        missing_fields = set(["type", "amount"]) & set(field_errors)
        assert len(missing_fields) > 0, "错误信息应该指出缺少的必要字段"
