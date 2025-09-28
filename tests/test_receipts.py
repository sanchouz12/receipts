from decimal import Decimal

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import PaymentType, Receipt, User


class TestReceiptCreate:
    def test_create_receipt_success(
        self, test_db: Session, client: TestClient, existing_user: User, auth_headers: dict
    ):
        receipt_data = {
            "products": [
                {"name": "Test Product 1", "price": "10.50", "quantity": "2"},
                {"name": "Test Product 2", "price": "5.00", "quantity": "1"},
            ],
            "payment": {"type": PaymentType.CASH, "amount": "30.00"},
        }

        response = client.post("/receipts/create", json=receipt_data, headers=auth_headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert "id" in data
        assert data["total"] == "26.00"
        assert data["rest"] == "4.00"
        assert len(data["products"]) == 2
        assert data["products"][0]["total"] == "21.00"
        assert data["products"][1]["total"] == "5.00"

        receipt_in_db = test_db.execute(select(Receipt).where(Receipt.id == data["id"])).scalar_one_or_none()
        assert receipt_in_db is not None
        assert receipt_in_db.user_id == existing_user.id

    def test_create_receipt_insufficient_payment(self, client: TestClient, existing_user: User, auth_headers: dict):
        receipt_data = {
            "products": [{"name": "Expensive Item", "price": "100.00", "quantity": "1"}],
            "payment": {"type": PaymentType.CARD, "amount": "50.00"},
        }

        response = client.post("/receipts/create", json=receipt_data, headers=auth_headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Insufficient payment amount" in response.json()["detail"]

    def test_create_receipt_unauthorized(self, client: TestClient):
        receipt_data = {
            "products": [{"name": "Test Product", "price": "10.00", "quantity": "1"}],
            "payment": {"type": PaymentType.CASH, "amount": "15.00"},
        }

        response = client.post("/receipts/create", json=receipt_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_receipt_invalid_data(self, client: TestClient, existing_user: User, auth_headers: dict):
        receipt_data = {
            "products": [{"name": "Test Product", "price": "-10.00", "quantity": "1"}],
            "payment": {"type": PaymentType.CASH, "amount": "15.00"},
        }

        response = client.post("/receipts/create", json=receipt_data, headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_receipt_empty_products(self, client: TestClient, existing_user: User, auth_headers: dict):
        receipt_data = {"products": [], "payment": {"type": PaymentType.CASH, "amount": "15.00"}}

        response = client.post("/receipts/create", json=receipt_data, headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestReceiptList:
    def test_list_receipts_success(self, test_db: Session, client: TestClient, existing_user: User, auth_headers: dict):
        receipt1 = Receipt(
            user_id=existing_user.id,
            products={"items": [{"name": "Product 1", "price": "10.00", "quantity": "1", "total": "10.00"}]},
            total_cost=Decimal("10.00"),
            payment_type=PaymentType.CASH,
            payment_amount=Decimal("15.00"),
        )
        receipt2 = Receipt(
            user_id=existing_user.id,
            products={"items": [{"name": "Product 2", "price": "20.00", "quantity": "1", "total": "20.00"}]},
            total_cost=Decimal("20.00"),
            payment_type=PaymentType.CARD,
            payment_amount=Decimal("20.00"),
        )
        test_db.add_all([receipt1, receipt2])
        test_db.commit()

        response = client.post("/receipts/search", json={}, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total_count"] == 2
        assert len(data["receipts"]) == 2
        assert data["page"] == 1
        assert data["per_page"] == 10

    def test_list_receipts_pagination(
        self, test_db: Session, client: TestClient, existing_user: User, auth_headers: dict
    ):
        for i in range(15):
            receipt = Receipt(
                user_id=existing_user.id,
                products={"items": [{"name": f"Product {i}", "price": "10.00", "quantity": "1", "total": "10.00"}]},
                total_cost=Decimal("10.00"),
                payment_type=PaymentType.CASH,
                payment_amount=Decimal("15.00"),
            )
            test_db.add(receipt)
        test_db.flush()

        response = client.post("/receipts/search?page=2&per_page=5", json={}, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total_count"] == 15
        assert len(data["receipts"]) == 5
        assert data["page"] == 2
        assert data["per_page"] == 5

    def test_list_receipts_filter_by_payment_type(
        self, test_db: Session, client: TestClient, existing_user: User, auth_headers: dict
    ):
        receipt_cash = Receipt(
            user_id=existing_user.id,
            products={"items": [{"name": "Product 1", "price": "10.00", "quantity": "1", "total": "10.00"}]},
            total_cost=Decimal("10.00"),
            payment_type=PaymentType.CASH,
            payment_amount=Decimal("15.00"),
        )
        receipt_card = Receipt(
            user_id=existing_user.id,
            products={"items": [{"name": "Product 2", "price": "20.00", "quantity": "1", "total": "20.00"}]},
            total_cost=Decimal("20.00"),
            payment_type=PaymentType.CARD,
            payment_amount=Decimal("20.00"),
        )
        test_db.add_all([receipt_cash, receipt_card])
        test_db.flush()

        response = client.post("/receipts/search", json={"payment_type": PaymentType.CASH}, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total_count"] == 1
        assert data["receipts"][0]["payment_type"] == PaymentType.CASH

    def test_list_receipts_filter_by_amount(
        self, test_db: Session, client: TestClient, existing_user: User, auth_headers: dict
    ):
        receipt1 = Receipt(
            user_id=existing_user.id,
            products={"items": [{"name": "Product 1", "price": "10.00", "quantity": "1", "total": "10.00"}]},
            total_cost=Decimal("10.00"),
            payment_type=PaymentType.CASH,
            payment_amount=Decimal("15.00"),
        )
        receipt2 = Receipt(
            user_id=existing_user.id,
            products={"items": [{"name": "Product 2", "price": "50.00", "quantity": "1", "total": "50.00"}]},
            total_cost=Decimal("50.00"),
            payment_type=PaymentType.CARD,
            payment_amount=Decimal("50.00"),
        )
        test_db.add_all([receipt1, receipt2])
        test_db.commit()

        response = client.post("/receipts/search", json={"min_total": 30}, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total_count"] == 1
        assert float(data["receipts"][0]["total"]) >= 30

    def test_list_receipts_unauthorized(self, client: TestClient):
        response = client.post("/receipts/search", json={})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestReceiptDetail:
    def test_get_receipt_success(self, test_db: Session, client: TestClient, existing_user: User, auth_headers: dict):
        receipt = Receipt(
            user_id=existing_user.id,
            products={"items": [{"name": "Test Product", "price": "10.00", "quantity": "2", "total": "20.00"}]},
            total_cost=Decimal("20.00"),
            payment_type=PaymentType.CASH,
            payment_amount=Decimal("25.00"),
        )
        test_db.add(receipt)
        test_db.flush()

        response = client.get(f"/receipts/{receipt.id}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["id"] == receipt.id
        assert data["total"] == "20.00"
        assert data["rest"] == "5.00"
        assert len(data["products"]) == 1

    def test_get_receipt_not_found(self, client: TestClient, existing_user: User, auth_headers: dict):
        response = client.get("/receipts/999", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_receipt_unauthorized(self, test_db: Session, client: TestClient, existing_user: User):
        receipt = Receipt(
            user_id=existing_user.id,
            products={"items": [{"name": "Test Product", "price": "10.00", "quantity": "1", "total": "10.00"}]},
            total_cost=Decimal("10.00"),
            payment_type=PaymentType.CASH,
            payment_amount=Decimal("15.00"),
        )
        test_db.add(receipt)
        test_db.flush()

        response = client.get(f"/receipts/{receipt.id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPublicReceipt:
    def test_get_public_receipt_success(self, test_db: Session, client: TestClient, existing_user: User):
        receipt = Receipt(
            user_id=existing_user.id,
            products={
                "items": [
                    {"name": "Product 1", "price": "100.00", "quantity": "3.00", "total": "300.00"},
                    {"name": "Product 2", "price": "50.00", "quantity": "2.00", "total": "100.00"},
                ]
            },
            total_cost=Decimal("400.00"),
            payment_type=PaymentType.CARD,
            payment_amount=Decimal("400.00"),
        )
        test_db.add(receipt)
        test_db.flush()

        response = client.get(f"/receipts/{receipt.id}/public")

        assert response.status_code == status.HTTP_200_OK
        receipt_text = response.text

        assert "My Company" in receipt_text
        assert "Product 1" in receipt_text

    def test_get_public_receipt_custom_width(self, test_db: Session, client: TestClient, existing_user: User):
        receipt = Receipt(
            user_id=existing_user.id,
            products={"items": [{"name": "Test Product", "price": "10.00", "quantity": "1", "total": "10.00"}]},
            total_cost=Decimal("10.00"),
            payment_type=PaymentType.CASH,
            payment_amount=Decimal("15.00"),
        )
        test_db.add(receipt)
        test_db.flush()

        response = client.get(f"/receipts/{receipt.id}/public?line_width=50")

        assert response.status_code == status.HTTP_200_OK
        receipt_text = response.text

        assert "My Company" in receipt_text

    def test_get_public_receipt_not_found(self, client: TestClient):
        response = client.get("/receipts/999/public")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_public_receipt_no_auth_required(self, test_db: Session, client: TestClient, existing_user: User):
        receipt = Receipt(
            user_id=existing_user.id,
            products={"items": [{"name": "Test Product", "price": "10.00", "quantity": "1", "total": "10.00"}]},
            total_cost=Decimal("10.00"),
            payment_type=PaymentType.CASH,
            payment_amount=Decimal("15.00"),
        )
        test_db.add(receipt)
        test_db.flush()

        response = client.get(f"/receipts/{receipt.id}/public")

        assert response.status_code == status.HTTP_200_OK
