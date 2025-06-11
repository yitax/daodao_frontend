from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os

from ..models.database import get_db
from ..models.models import User, AIPersonality

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 token scheme
token_scheme = OAuth2PasswordBearer(tokenUrl="api/users/login")


# Pydantic models
class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserSettings(BaseModel):
    personality_id: Optional[int] = None


class PersonalityUpdate(BaseModel):
    personality_id: int


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str


class UserSettingsUpdate(BaseModel):
    email: Optional[str] = None


class AccountDelete(BaseModel):
    password: str


# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def get_current_user(db: Session = Depends(get_db), token: str = Depends(token_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user


# Endpoints
@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    print(f"\n======== 处理用户注册请求 ========")
    print(f"用户名: {user.username}")
    print(f"邮箱: {user.email}")
    print(f"密码长度: {len(user.password) if user.password else 0}")

    # 检查用户名是否已存在
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        error_msg = f"用户名 '{user.username}' 已被注册"
        print(f"错误: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)

    # 检查邮箱是否已存在
    db_email = db.query(User).filter(User.email == user.email).first()
    if db_email:
        error_msg = f"邮箱 '{user.email}' 已被注册"
        print(f"错误: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)

    # 检查密码长度
    if len(user.password) < 6:
        error_msg = "密码长度不能少于6个字符"
        print(f"错误: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)

    # 创建用户
    try:
        hashed_password = get_password_hash(user.password)
        new_user = User(
            username=user.username, email=user.email, hashed_password=hashed_password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"注册成功: 用户ID {new_user.id}")
        return new_user
    except Exception as e:
        db.rollback()
        error_msg = f"注册失败: {str(e)}"
        print(f"错误: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/login", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    password_update: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更改用户密码"""
    print(f"\n======== 处理密码修改请求 - 用户ID: {current_user.id} ========")
    print(f"用户名: {current_user.username}")
    print(
        f"收到新密码: {'*' * len(password_update.new_password) if password_update.new_password else '空'}"
    )

    # 验证当前密码是否正确
    is_valid = verify_password(
        password_update.current_password, current_user.hashed_password
    )
    print(f"当前密码验证结果: {'通过' if is_valid else '不正确'}")

    if not is_valid:
        print("返回错误: 当前密码不正确")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码不正确"
        )

    # 验证新密码长度
    if len(password_update.new_password) < 6:
        print("返回错误: 新密码长度不足")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="新密码长度不得少于6个字符"
        )

    # 更新密码
    try:
        hashed_password = get_password_hash(password_update.new_password)
        print("已生成新的密码哈希")

        current_user.hashed_password = hashed_password
        db.commit()
        print("密码已成功更新到数据库")

        return {"message": "密码已成功更新"}
    except Exception as e:
        db.rollback()
        print(f"密码更新失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码更新失败: {str(e)}",
        )


@router.put("/settings", response_model=Dict[str, Any])
def update_user_settings(
    settings: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新用户设置"""
    if settings.email is not None:
        # 检查邮箱是否已被其他用户使用
        existing_user = (
            db.query(User)
            .filter(User.email == settings.email, User.id != current_user.id)
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="该邮箱已被其他用户使用"
            )

        current_user.email = settings.email

    db.commit()
    return {"message": "用户设置已更新"}


@router.delete("/account", status_code=status.HTTP_200_OK)
def delete_user_account(
    account_delete: AccountDelete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除用户账户"""
    # 验证密码是否正确
    if not verify_password(account_delete.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="密码不正确"
        )

    # 禁用账户
    current_user.is_active = False
    db.commit()

    return {"message": "账户已删除"}


@router.get("/settings", response_model=UserSettings)
def get_user_settings(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """获取用户设置，包括当前选择的AI助手等"""
    default_personality = (
        db.query(AIPersonality).filter(AIPersonality.is_default == True).first()
    )
    personality_id = default_personality.id if default_personality else 1

    return {"personality_id": personality_id}


@router.post("/settings/personality", response_model=Dict[str, Any])
def update_user_personality(
    personality: PersonalityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新用户选择的AI助手"""
    # 验证提供的personality_id是否有效
    db_personality = (
        db.query(AIPersonality)
        .filter(AIPersonality.id == personality.personality_id)
        .first()
    )
    if not db_personality:
        raise HTTPException(status_code=404, detail="助手ID不存在")

    # 由于当前User模型中没有personality_id字段，返回未实现错误
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="服务器尚未实现此功能，需要添加personality_id字段到用户表",
    )
