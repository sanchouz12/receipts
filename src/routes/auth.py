from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db
from src.schemas.auth import TokenResponse
from src.services.auth import login_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token")
async def login(
    db: Annotated[AsyncSession, Depends(get_db)], form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> TokenResponse:
    return await login_user(db, form_data.username, form_data.password)
