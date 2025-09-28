from src.services.auth import login_user


def create_auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def get_access_token(async_client, email: str, password: str) -> str:
    response = await login_user(async_client, email, password)
    return response.access_token
