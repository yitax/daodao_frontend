from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date, timedelta
import time
from fastapi.responses import JSONResponse

from ..models.database import get_db
from ..models.models import Transaction, User, TransactionType
from .users import get_current_user

router = APIRouter()


# Pydantic models
class TransactionBase(BaseModel):
    type: TransactionType
    amount: float
    description: str
    category: str
    transaction_date: date
    transaction_time: Optional[datetime] = None
    currency: str = "CNY"


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    type: Optional[TransactionType] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    category: Optional[str] = None
    transaction_date: Optional[date] = None
    transaction_time: Optional[datetime] = None
    currency: Optional[str] = None


class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False

    class Config:
        orm_mode = True


# Endpoints
@router.post(
    "/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED
)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_transaction = Transaction(
        user_id=current_user.id,
        type=transaction.type,
        amount=transaction.amount,
        description=transaction.description,
        category=transaction.category,
        transaction_date=transaction.transaction_date,
        transaction_time=transaction.transaction_time,
        currency=transaction.currency,
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@router.get("/")
def read_transactions(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    transaction_type: Optional[TransactionType] = None,
    category: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    search: Optional[str] = None,
    count_only: bool = False,  # 仅返回计数
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Transaction).filter(
        Transaction.user_id == current_user.id, Transaction.is_deleted == False
    )

    # Apply filters with debugging logs
    if start_date:
        print(f"Filtering with start_date: {start_date}")
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        # 修复：确保包含end_date当天的全部记录
        print(f"Filtering with end_date: {end_date}")

        # 由于transaction_date是DateTime类型，处理日期范围时需要特别注意
        from datetime import datetime, timedelta

        # 将end_date转换为第二天的0点，以包含当天的所有记录
        # 例如：如果end_date是2025-06-06，需要查询到2025-06-06 23:59:59
        next_day = end_date + timedelta(days=1)
        print(f"Adjusted end_date: using < {next_day} instead of <= {end_date}")

        # 使用 < next_day，而不是 <= end_date，确保包含end_date当天的全部记录
        query = query.filter(Transaction.transaction_date < next_day)

    if transaction_type:
        query = query.filter(Transaction.type == transaction_type)
    if category:
        query = query.filter(Transaction.category == category)
    if min_amount:
        query = query.filter(Transaction.amount >= min_amount)
    if max_amount:
        query = query.filter(Transaction.amount <= max_amount)
    if search:
        query = query.filter(Transaction.description.ilike(f"%{search}%"))

    # 获取总数
    total = query.count()
    print(f"Total records after filtering: {total}")

    # 如果仅需要计数，返回计数结果
    if count_only:
        return {"total": total}

    # Order by date descending, then by creation time descending
    query = query.order_by(
        Transaction.transaction_date.desc(), Transaction.created_at.desc()
    )

    # Apply pagination
    transactions = query.offset(skip).limit(limit).all()
    print(f"Returning {len(transactions)} records after pagination")

    # 打印返回的交易记录日期，用于调试
    for tx in transactions:
        print(
            f"Transaction ID: {tx.id}, Date: {tx.transaction_date}, Type: {tx.type}, Amount: {tx.amount}"
        )

    # 创建响应并添加X-Total-Count头
    response = JSONResponse(
        content=[
            {
                "id": tx.id,
                "user_id": tx.user_id,
                "type": tx.type,
                "amount": tx.amount,
                "description": tx.description,
                "category": tx.category,
                "transaction_date": tx.transaction_date.isoformat(),
                "transaction_time": (
                    tx.transaction_time.isoformat() if tx.transaction_time else None
                ),
                "currency": tx.currency,
                "created_at": tx.created_at.isoformat(),
                "updated_at": tx.updated_at.isoformat(),
                "is_deleted": tx.is_deleted,
            }
            for tx in transactions
        ]
    )
    response.headers["X-Total-Count"] = str(total)

    return response


@router.get("/{transaction_id}", response_model=TransactionResponse)
def read_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,
            Transaction.is_deleted == False,
        )
        .first()
    )

    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,
            Transaction.is_deleted == False,
        )
        .first()
    )

    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Update fields if provided
    update_data = transaction_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_transaction, key, value)

    db_transaction.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,
            Transaction.is_deleted == False,
        )
        .first()
    )

    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Soft delete
    db_transaction.is_deleted = True
    db_transaction.updated_at = datetime.utcnow()
    db.commit()

    return None
