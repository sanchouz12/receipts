from datetime import datetime

from pydantic import BaseModel, Field


class JWTPayload(BaseModel):
    sub: str = Field(description="Subject (email)")
    user_id: int = Field(description="User ID")
    exp: datetime = Field(description="Expiration time")


class TokenResponse(BaseModel):
    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")  # noqa: S105


class TokenData(BaseModel):
    email: str = Field(description="User email from token")
    user_id: int = Field(description="User ID from token")
