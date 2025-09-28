from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db
from src.dependencies.auth import get_current_user
from src.models import Receipt, User
from src.schemas.receipts import (
    PaymentInfo,
    ProductResponse,
    ReceiptCreateRequest,
    ReceiptFilters,
    ReceiptListItem,
    ReceiptListResponse,
    ReceiptResponse,
)

router = APIRouter(prefix="/receipts", tags=["Receipts"])


@router.post("/create", status_code=201)
async def create_receipt(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    receipt_data: ReceiptCreateRequest,
) -> ReceiptResponse:
    products_with_totals = []
    total_cost = Decimal("0")

    for product in receipt_data.products:
        product_total = product.price * product.quantity
        products_with_totals.append(
            ProductResponse(name=product.name, price=product.price, quantity=product.quantity, total=product_total)
        )
        total_cost += product_total

    rest = receipt_data.payment.amount - total_cost
    if rest < 0:
        raise HTTPException(status_code=400, detail="Insufficient payment amount")

    receipt = Receipt(
        user_id=current_user.id,
        products={
            "items": [
                {"name": p.name, "price": str(p.price), "quantity": str(p.quantity), "total": str(p.total)}
                for p in products_with_totals
            ]
        },
        total_cost=total_cost,
        payment_type=receipt_data.payment.type,
        payment_amount=receipt_data.payment.amount,
    )

    db.add(receipt)
    await db.commit()
    await db.refresh(receipt)

    return ReceiptResponse(
        id=receipt.id,
        products=products_with_totals,
        payment=receipt_data.payment,
        total=total_cost,
        rest=rest,
        created_at=receipt.created_at,
    )


@router.post("/search")
async def list_receipts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 10,
    filters: ReceiptFilters | None = None,
) -> ReceiptListResponse:
    query = select(Receipt).where(Receipt.user_id == current_user.id).order_by(Receipt.created_at.desc())

    if filters:
        filter_conditions = []
        if filters.date_from:
            filter_conditions.append(Receipt.created_at >= filters.date_from)
        if filters.date_to:
            filter_conditions.append(Receipt.created_at <= filters.date_to)
        if filters.min_total is not None:
            filter_conditions.append(Receipt.total_cost >= filters.min_total)
        if filters.max_total is not None:
            filter_conditions.append(Receipt.total_cost <= filters.max_total)
        if filters.payment_type:
            filter_conditions.append(Receipt.payment_type == filters.payment_type)

        if filter_conditions:
            query = query.where(and_(*filter_conditions))

    count_result = await db.scalar(query.with_only_columns(func.count(Receipt.id.distinct())).order_by(None))
    total_count = count_result or 0
    total_pages = (total_count + per_page - 1) // per_page
    current_page = min(page, total_pages)

    offset = max((current_page - 1), 0) * per_page
    receipts = await db.scalars(query.offset(offset).limit(per_page))
    receipts_list = list(receipts)

    receipt_items = [
        ReceiptListItem(
            id=receipt.id, total=receipt.total_cost, payment_type=receipt.payment_type, created_at=receipt.created_at
        )
        for receipt in receipts_list
    ]

    return ReceiptListResponse(receipts=receipt_items, total_count=total_count, page=current_page, per_page=per_page)


@router.get("/{receipt_id}")
async def get_receipt(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    receipt_id: int,
) -> ReceiptResponse:
    query = select(Receipt).where(Receipt.id == receipt_id, Receipt.user_id == current_user.id)
    receipt = await db.scalar(query)

    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    products = [
        ProductResponse(
            name=item["name"],
            price=Decimal(item["price"]),
            quantity=Decimal(item["quantity"]),
            total=Decimal(item["total"]),
        )
        for item in receipt.products["items"]
    ]

    rest = receipt.payment_amount - receipt.total_cost

    return ReceiptResponse(
        id=receipt.id,
        products=products,
        payment=PaymentInfo(type=receipt.payment_type, amount=receipt.payment_amount),
        total=receipt.total_cost,
        rest=rest,
        created_at=receipt.created_at,
    )


@router.get("/{receipt_id}/public", response_class=PlainTextResponse)
async def get_public_receipt(
    db: Annotated[AsyncSession, Depends(get_db)], receipt_id: int, line_width: Annotated[int, Query(ge=20, le=80)] = 32
) -> str:
    query = select(Receipt).where(Receipt.id == receipt_id)
    receipt = await db.scalar(query)

    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    def format_line(text: str, width: int) -> str:
        if len(text) <= width:
            return text
        return text[: width - 3] + "..."

    def center_text(text: str, width: int) -> str:
        return text.center(width)

    lines = []
    lines.append(center_text("My Company", line_width))
    lines.append("=" * line_width)

    price_width = min(10, max(8, line_width // 4))
    label_width = line_width - price_width - 1

    for item in receipt.products["items"]:
        quantity = Decimal(item["quantity"])
        price = Decimal(item["price"])
        total = Decimal(item["total"])
        name = item["name"]

        price_line = f"{quantity} x {price:,.2f}"
        lines.append(price_line)

        name_total_line = f"{format_line(name, label_width):<{label_width}} {total:>{price_width},.2f}"
        lines.append(name_total_line)

    lines.append("-" * line_width)
    lines.append(f"{format_line('Загальна сума', label_width):<{label_width}} {receipt.total_cost:>{price_width},.2f}")

    payment_type_display = "Готівка" if receipt.payment_type == "cash" else "Карта"
    lines.append(
        f"{format_line(payment_type_display, label_width):<{label_width}} {receipt.payment_amount:>{price_width},.2f}"
    )

    rest = receipt.payment_amount - receipt.total_cost
    lines.append(f"{format_line('Решта', label_width):<{label_width}} {rest:>{price_width},.2f}")

    lines.append("=" * line_width)
    lines.append(center_text(receipt.created_at.strftime("%d.%m.%Y %H:%M"), line_width))

    return "\n".join(lines)
