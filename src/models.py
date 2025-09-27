from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Identity, Numeric, String, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class PaymentType(StrEnum):
    CASH = "cash"
    CARD = "card"


PaymentTypeEnum = Enum(PaymentType, name="payment_types", values_callable=lambda t: [item.value for item in t])


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("name", "email", name="name_and_email_uc"),)

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100))
    password: Mapped[str] = mapped_column(String)

    receipts: Mapped[list["Receipt"]] = relationship(back_populates="user")

    def __init__(self, name: str, email: str, password: str):
        super().__init__()
        self.name = name
        self.email = email
        self.password = password


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    products: Mapped[dict] = mapped_column(JSON)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    payment_type: Mapped[PaymentType] = mapped_column(PaymentTypeEnum)
    payment_amount: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    user: Mapped["User"] = relationship(back_populates="receipts", cascade="all, delete-orphan")

    def __init__(
        self,
        user_id: int,
        products: dict,
        total_cost: Decimal,
        payment_type: PaymentType,
        payment_amount: Decimal,
        created_at: datetime | None = None,
    ) -> None:
        super().__init__()
        self.user_id = user_id
        self.products = products
        self.total_cost = total_cost
        self.payment_type = payment_type
        self.payment_amount = payment_amount
        if created_at:
            self.created_at = created_at
