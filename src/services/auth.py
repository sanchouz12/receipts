from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User
from src.schemas.auth import TokenResponse, UserRegisterData
from src.utils.auth import get_password_hash, verify_password
from src.utils.tokens import create_access_token


async def register_user(db: AsyncSession, user_data: UserRegisterData) -> None:
    existing_user = await db.scalar(select(User).where(User.email == user_data.email))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")

    hashed_password = get_password_hash(user_data.password)

    new_user = User(name=user_data.name, email=user_data.email, password=hashed_password)
    db.add(new_user)
    await db.commit()


async def login_user(db: AsyncSession, login: str, password: str) -> TokenResponse:
    user = await _authenticate_user(db, login, password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong email or password")

    access_token = create_access_token(user.email, user.id)
    return TokenResponse(access_token=access_token)


async def _authenticate_user(db: AsyncSession, login: str, password: str) -> User | None:
    query = select(User).where(User.email == login)
    user = await db.scalar(query)

    if not user or not verify_password(password, user.password):
        return None
    return user
