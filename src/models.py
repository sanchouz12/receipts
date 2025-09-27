from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Identity, Numeric, String, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PaymentType(StrEnum):
    CASH = "cash"
    CARD = "card"


PaymentTypeEnum = Enum(PaymentType, name="payment_types", values_callable=lambda t: [item.value for item in t])


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String)


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    products: Mapped[dict] = mapped_column(JSON)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    payment_type: Mapped[PaymentType] = mapped_column(PaymentTypeEnum)
    payment_amount: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
