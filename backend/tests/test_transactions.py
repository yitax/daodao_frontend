import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.database import Base, get_db
from app.models.models import User, Transaction, TransactionType
from app.main import app
from datetime import datetime, timedelta
import json

# 创建内存测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 测试用户凭证
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
}


# 设置和清理数据库
@pytest.fixture(scope="module")
def db():
    # 创建测试表
    Base.metadata.create_all(bind=engine)

    # 创建会话
    db = TestingSessionLocal()

    # 创建测试用户
    hashed_password = "hashed_" + TEST_USER["password"]  # 简化版哈希
    test_user = User(
        username=TEST_USER["username"],
        email=TEST_USER["email"],
        hashed_password=hashed_password,
    )
    db.add(test_user)
    db.commit()

    # 创建一些测试交易记录
    user = db.query(User).filter(User.username == TEST_USER["username"]).first()

    # 添加收入交易
    income_transaction = Transaction(
        user_id=user.id,
        type=TransactionType.INCOME,
        amount=1000.0,
        description="测试工资收入",
        category="工资薪酬",
        transaction_date=datetime.now() - timedelta(days=5),
    )
    db.add(income_transaction)

    # 添加支出交易
    expense_transaction = Transaction(
        user_id=user.id,
        type=TransactionType.EXPENSE,
        amount=150.0,
        description="测试餐饮支出",
        category="餐饮美食",
        transaction_date=datetime.now() - timedelta(days=2),
    )
    db.add(expense_transaction)

    db.commit()

    yield db

    # 清理测试表
    db.close()
    Base.metadata.drop_all(bind=engine)


# 创建测试客户端，并覆盖依赖项以使用测试数据库
@pytest.fixture(scope="module")
def client(db):
    # 覆盖依赖项
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # 覆盖用户认证依赖项
    async def override_get_current_user():
        return db.query(User).filter(User.username == TEST_USER["username"]).first()

    from app.routers.users import get_current_user

    app.dependency_overrides[get_current_user] = override_get_current_user

    # 返回测试客户端
    with TestClient(app) as c:
        yield c


# 测试创建新交易
def test_create_transaction(client, db):
    # 构建交易数据
    transaction_data = {
        "type": "expense",
        "amount": 75.5,
        "description": "测试新交易",
        "category": "日用百货",
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    # 发送创建交易请求
    response = client.post("/transactions/", json=transaction_data)

    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == transaction_data["type"]
    assert data["amount"] == transaction_data["amount"]
    assert data["description"] == transaction_data["description"]
    assert data["category"] == transaction_data["category"]

    # 验证交易已添加到数据库
    created_transaction = (
        db.query(Transaction)
        .filter(Transaction.description == transaction_data["description"])
        .first()
    )
    assert created_transaction is not None
    assert created_transaction.amount == transaction_data["amount"]


# 测试获取交易列表
def test_get_transactions(client, db):
    # 发送获取交易列表请求
    response = client.get("/transactions/")

    # 验证响应
    assert response.status_code == 200
    transactions = response.json()
    assert isinstance(transactions, list)
    assert len(transactions) >= 3  # 两个初始测试交易和一个新创建的交易

    # 验证分页头部
    total_count = response.headers.get("X-Total-Count")
    assert total_count is not None
    assert int(total_count) >= 3


# 测试按类型筛选交易
def test_filter_transactions_by_type(client, db):
    # 发送按收入类型筛选的请求
    response = client.get("/transactions/?type=income")

    # 验证响应
    assert response.status_code == 200
    transactions = response.json()
    assert isinstance(transactions, list)
    assert len(transactions) >= 1

    # 验证所有返回的交易都是收入类型
    for transaction in transactions:
        assert transaction["type"] == "income"

    # 发送按支出类型筛选的请求
    response = client.get("/transactions/?type=expense")

    # 验证响应
    assert response.status_code == 200
    transactions = response.json()
    assert isinstance(transactions, list)
    assert len(transactions) >= 2  # 一个初始测试支出和一个新创建的支出

    # 验证所有返回的交易都是支出类型
    for transaction in transactions:
        assert transaction["type"] == "expense"


# 测试按日期范围筛选交易
def test_filter_transactions_by_date_range(client, db):
    # 获取当前日期
    today = datetime.now().date()
    # 一周前的日期
    week_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    # 明天的日期
    tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")

    # 发送按日期范围筛选的请求
    response = client.get(f"/transactions/?start_date={week_ago}&end_date={tomorrow}")

    # 验证响应
    assert response.status_code == 200
    transactions = response.json()
    assert isinstance(transactions, list)
    assert len(transactions) >= 3  # 所有测试交易都应在该日期范围内


# 测试获取单个交易详情
def test_get_transaction(client, db):
    # 首先获取所有交易
    response = client.get("/transactions/")
    assert response.status_code == 200
    transactions = response.json()

    # 选择第一个交易的ID
    transaction_id = transactions[0]["id"]

    # 发送获取单个交易详情的请求
    response = client.get(f"/transactions/{transaction_id}")

    # 验证响应
    assert response.status_code == 200
    transaction = response.json()
    assert transaction["id"] == transaction_id
    assert "type" in transaction
    assert "amount" in transaction
    assert "description" in transaction
    assert "category" in transaction


# 测试更新交易
def test_update_transaction(client, db):
    # 首先获取所有交易
    response = client.get("/transactions/")
    assert response.status_code == 200
    transactions = response.json()

    # 选择第一个交易的ID
    transaction_id = transactions[0]["id"]
    original_transaction = transactions[0]

    # 准备更新数据
    update_data = {
        "description": "已更新的交易描述",
        "amount": original_transaction["amount"] + 50.0,
        "category": "已更新的分类",
    }

    # 发送更新交易请求
    response = client.put(f"/transactions/{transaction_id}", json=update_data)

    # 验证响应
    assert response.status_code == 200
    updated_transaction = response.json()
    assert updated_transaction["id"] == transaction_id
    assert updated_transaction["description"] == update_data["description"]
    assert updated_transaction["amount"] == update_data["amount"]
    assert updated_transaction["category"] == update_data["category"]

    # 验证数据库中的交易已更新
    db_transaction = (
        db.query(Transaction).filter(Transaction.id == transaction_id).first()
    )
    assert db_transaction.description == update_data["description"]
    assert db_transaction.amount == update_data["amount"]
    assert db_transaction.category == update_data["category"]


# 测试删除交易
def test_delete_transaction(client, db):
    # 首先获取所有交易
    response = client.get("/transactions/")
    assert response.status_code == 200
    transactions = response.json()

    # 选择第一个交易的ID
    transaction_id = transactions[0]["id"]

    # 发送删除交易请求
    response = client.delete(f"/transactions/{transaction_id}")

    # 验证响应
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True

    # 验证交易已在数据库中标记为已删除
    db_transaction = (
        db.query(Transaction).filter(Transaction.id == transaction_id).first()
    )
    assert db_transaction.is_deleted is True

    # 验证获取交易列表时已删除的交易不会被返回
    response = client.get("/transactions/")
    updated_transactions = response.json()
    deleted_transaction = next(
        (t for t in updated_transactions if t["id"] == transaction_id), None
    )
    assert deleted_transaction is None


# 测试交易统计功能
def test_transaction_statistics(client, db):
    # 发送获取交易统计的请求
    response = client.get("/reports/summary")

    # 验证响应
    assert response.status_code == 200
    stats = response.json()

    # 验证统计结果包含关键字段
    assert "total_income" in stats
    assert "total_expense" in stats
    assert "net_balance" in stats
    assert stats["total_income"] >= 1000.0  # 初始测试收入是1000.0
    assert stats["total_expense"] >= 225.5  # 初始测试支出150.0 + 新增支出75.5
    assert stats["net_balance"] == stats["total_income"] - stats["total_expense"]
