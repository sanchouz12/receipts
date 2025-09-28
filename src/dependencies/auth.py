"""FastAPI authentication and platform dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.db import get_db
from src.models import User
from src.schemas.auth import TokenData
from src.utils.auth import get_data_from_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_token_data(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenData:
    return get_data_from_token(token)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)], token_data: Annotated[TokenData, Depends(get_token_data)]
) -> User:
    user = await db.get(User, token_data.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
