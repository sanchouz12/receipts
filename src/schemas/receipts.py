from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.models import PaymentType


class ProductItem(BaseModel):
    name: str = Field(description="Product name")
    price: Decimal = Field(description="Price per unit", gt=0)
    quantity: Decimal = Field(description="Quantity or weight", gt=0)


class ProductResponse(ProductItem):
    total: Decimal = Field(description="Total cost for this product")


class PaymentInfo(BaseModel):
    type: PaymentType = Field(description="Payment type: cash or card")
    amount: Decimal = Field(description="Payment amount", gt=0)


class ReceiptCreateRequest(BaseModel):
    products: list[ProductItem] = Field(description="List of products in receipt", min_length=1)
    payment: PaymentInfo = Field(description="Payment information")


class ReceiptResponse(BaseModel):
    id: int = Field(description="Receipt ID")
    products: list[ProductResponse] = Field(description="List of products with totals")
    payment: PaymentInfo = Field(description="Payment information")
    total: Decimal = Field(description="Total receipt amount")
    rest: Decimal = Field(description="Change amount")
    created_at: datetime = Field(description="Receipt creation timestamp")


class ReceiptListItem(BaseModel):
    id: int = Field(description="Receipt ID")
    total: Decimal = Field(description="Total receipt amount")
    payment_type: PaymentType = Field(description="Payment type")
    created_at: datetime = Field(description="Receipt creation timestamp")


class ReceiptListResponse(BaseModel):
    receipts: list[ReceiptListItem] = Field(description="List of receipts")
    total_count: int = Field(description="Total number of receipts")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")


class ReceiptFilters(BaseModel):
    date_from: datetime | None = Field(None, description="Filter receipts created after this date")
    date_to: datetime | None = Field(None, description="Filter receipts created before this date")
    min_total: Decimal | None = Field(None, description="Filter receipts with total >= this amount", ge=0)
    max_total: Decimal | None = Field(None, description="Filter receipts with total <= this amount", ge=0)
    payment_type: PaymentType | None = Field(None, description="Filter by payment type")
