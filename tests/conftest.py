from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from pydantic_settings import SettingsConfigDict
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, sessionmaker

from src.config import Config
from src.db import get_db
from src.main import app
from src.models import Base, User
from src.schemas.auth import UserRegisterData
from src.utils.auth import get_password_hash
from tests.utils.helpers import create_auth_headers


class TestConfig(Config):
    model_config = SettingsConfigDict(
        env_file=".env.test", env_ignore_empty=True, env_file_encoding="utf-8", extra="ignore"
    )


@pytest.fixture(scope="session")
def test_config() -> Config:
    return TestConfig()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db(test_config: Config) -> Generator[None]:
    engine = create_engine(test_config.database_url, echo=False)

    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
    with engine.connect() as conn:
        conn.execute(text("DROP TYPE IF EXISTS payment_types CASCADE"))
        conn.commit()

    engine.dispose()


@pytest.fixture
def test_db(test_config: Config) -> Generator[Session]:
    engine = create_engine(test_config.database_url, echo=False)
    test_session = sessionmaker(bind=engine)

    with test_session() as session:
        transaction = session.begin()
        try:
            yield session
        finally:
            if transaction.is_active:
                transaction.rollback()


@pytest.fixture
def client(test_db: Session) -> Generator[TestClient]:
    async def override_get_db() -> AsyncGenerator[AsyncMock]:
        mock_session = AsyncMock(spec=AsyncSession)

        mock_session.scalar = AsyncMock(side_effect=lambda query: test_db.scalar(query))
        mock_session.execute = AsyncMock(side_effect=lambda query: test_db.execute(query))
        mock_session.get = AsyncMock(side_effect=lambda model, id_: test_db.get(model, id_))
        mock_session.add = test_db.add
        mock_session.commit = AsyncMock(side_effect=lambda: test_db.flush())

        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def existing_user_data() -> UserRegisterData:
    return UserRegisterData(name="Test User 1", email="test_user_1@example.com", password="password123")


@pytest.fixture
def new_user_data() -> UserRegisterData:
    return UserRegisterData(name="Test User 2", email="test_user_2@example.com", password="password123")


@pytest.fixture
def existing_user(test_db: Session, existing_user_data: UserRegisterData) -> User:
    hashed_password = get_password_hash(existing_user_data.password)
    user = User(name=existing_user_data.name, email=existing_user_data.email, password=hashed_password)
    test_db.add(user)
    test_db.flush()

    return user


@pytest.fixture
def auth_headers(client: TestClient, existing_user_data: UserRegisterData) -> dict:
    response = client.post(
        "/auth/token", data={"username": existing_user_data.email, "password": existing_user_data.password}
    )
    token = response.json()["access_token"]

    return create_auth_headers(token)
