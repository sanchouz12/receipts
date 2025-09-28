from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models import User
from src.schemas.auth import UserRegisterData


class TestAuthRegister:
    def test_register_success(self, test_db: Session, client: TestClient, new_user_data: UserRegisterData):
        response = client.post("/auth/register", json=new_user_data.model_dump())
        new_user_in_db = test_db.execute(select(User).where(User.email == new_user_data.email)).scalar_one_or_none()

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {"message": "Successfully registered"}
        assert new_user_in_db is not None

    def test_register_duplicate_email(
        self, test_db: Session, client: TestClient, existing_user: User, new_user_data: UserRegisterData
    ):
        new_user_data.email = existing_user.email

        response = client.post("/auth/register", json=new_user_data.model_dump())
        users_in_transaction = test_db.execute(select(func.count(User.id))).scalar_one()

        assert response.status_code == status.HTTP_409_CONFLICT
        assert users_in_transaction == 1

    def test_register_invalid_email(self, client: TestClient, new_user_data: UserRegisterData):
        new_user_data.email = "invalid-email"

        response = client.post("/auth/register", json=new_user_data.model_dump())

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_register_missing_fields(self, client: TestClient):
        user_data = {"email": "test@example.com"}

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestAuthLogin:
    def test_login_success(self, client: TestClient, existing_user: User, existing_user_data: UserRegisterData):
        form_data = {"username": existing_user_data.email, "password": existing_user_data.password}

        response = client.post("/auth/token", data=form_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_email(self, client: TestClient, new_user_data: UserRegisterData):
        form_data = {"username": new_user_data.email, "password": new_user_data.password}

        response = client.post("/auth/token", data=form_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_invalid_password(
        self, client: TestClient, existing_user: User, existing_user_data: UserRegisterData
    ):
        form_data = {"username": existing_user_data.email, "password": "wrongpassword"}

        response = client.post("/auth/token", data=form_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_credentials(self, client: TestClient):
        response = client.post("/auth/token", data={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestAuthMe:
    def test_get_current_user_success(self, client: TestClient, existing_user: User, auth_headers: dict):
        response = client.get("/auth/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == existing_user.name
        assert data["email"] == existing_user.email

    def test_get_current_user_no_token(self, client: TestClient):
        response = client.get("/auth/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_invalid_token(self, client: TestClient):
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/auth/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_malformed_auth_header(self, client: TestClient):
        headers = {"Authorization": "InvalidFormat token"}
        response = client.get("/auth/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
