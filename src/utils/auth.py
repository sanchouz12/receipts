import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt

from src.config import config
from src.schemas.auth import TokenData


def get_data_from_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        email = payload.get("sub")
        user_id = payload.get("user_id")

        if not isinstance(email, str) or not isinstance(user_id, int):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token data")

        return TokenData(email=email, user_id=user_id)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
