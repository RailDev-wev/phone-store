from enum import Enum
from sqlalchemy import Integer, String, Boolean, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class Role(str, Enum):
    admin = "admin"
    seller = "seller"
    viewer = "viewer"


class InventoryStatus(str, Enum):
    in_stock = "in_stock"
    reserved = "reserved"
    sold = "sold"


class LeadStatus(str, Enum):
    new = "new"
    in_progress = "in_progress"
    closed = "closed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    role: Mapped[Role] = mapped_column(String(20), default=Role.seller)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    title: Mapped[str] = mapped_column(String(200))
    is_used: Mapped[bool] = mapped_column(Boolean, default=True)

    condition_grade: Mapped[str] = mapped_column(String(10), default="A")
    battery_health: Mapped[int | None] = mapped_column(Integer, nullable=True)

    imei: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)

    sell_price_uzs: Mapped[int] = mapped_column(Integer, default=0)
    purchase_price_uzs: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[InventoryStatus] = mapped_column(String(20), default=InventoryStatus.in_stock)
    notes: Mapped[str] = mapped_column(String(1000), default="")
    telegram_photo_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SaleEvent(Base):
    __tablename__ = "sale_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(Integer, index=True)
    telegram_id: Mapped[int] = mapped_column(Integer, index=True)

    sell_price_uzs: Mapped[int] = mapped_column(Integer, default=0)
    channel: Mapped[str] = mapped_column(String(30), default="shop")
    payment_type: Mapped[str] = mapped_column(String(30), default="cash")

    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    item_id: Mapped[int] = mapped_column(Integer, index=True)
    item_title: Mapped[str] = mapped_column(String(200), default="")

    full_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(40))
    installment_months: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(Text, default="")

    status: Mapped[LeadStatus] = mapped_column(String(20), default=LeadStatus.new)
    assigned_to_telegram_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )