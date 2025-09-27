from datetime import datetime, timedelta, timezone

from jose import jwt

from src.config import config
from src.schemas.auth import JWTPayload


def create_access_token(sub: str, user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=config.JWT_ACCESS_TOKEN_EXPIRE_HOURS)
    payload = JWTPayload(sub=sub, user_id=user_id, exp=expire)
    return jwt.encode(payload.model_dump(), config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
