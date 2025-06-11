from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base
import datetime


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    # 添加用户选择的AI助手ID
    personality_id = Column(Integer, ForeignKey("ai_personalities.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    # Relationships
    transactions = relationship("Transaction", back_populates="user")
    chat_messages = relationship("ChatMessage", back_populates="user")
    # 关联到选择的AI助手
    personality = relationship("AIPersonality")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(Enum(TransactionType))
    amount = Column(Float)
    currency = Column(String, default="CNY")
    description = Column(String)
    category = Column(String)
    transaction_date = Column(DateTime)
    transaction_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
    is_deleted = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="transactions")


class AIPersonality(Base):
    __tablename__ = "ai_personalities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String)
    system_prompt = Column(Text)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    is_user = Column(
        Boolean, default=True
    )  # True if message is from user, False if from AI
    personality_id = Column(Integer, ForeignKey("ai_personalities.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="chat_messages")
    personality = relationship("AIPersonality")
