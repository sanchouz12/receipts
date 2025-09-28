from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db
from src.dependencies.auth import get_current_user
from src.models import User
from src.schemas.auth import TokenResponse, UserInfo, UserRegisterData
from src.services.auth import login_user, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=201)
async def register(db: Annotated[AsyncSession, Depends(get_db)], user_data: UserRegisterData) -> dict[str, str]:
    await register_user(db, user_data)
    return {"message": "Successfully registered"}


@router.post("/token")
async def login(
    db: Annotated[AsyncSession, Depends(get_db)], form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> TokenResponse:
    return await login_user(db, form_data.username, form_data.password)


@router.get("/me")
async def get_current_user_info(current_user: Annotated[User, Depends(get_current_user)]) -> UserInfo:
    return UserInfo(name=current_user.name, email=current_user.email)
