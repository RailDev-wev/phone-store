from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, Field

from ..db import get_db
from ..models import InventoryItem, InventoryStatus, User, SaleEvent
from ..deps_bot import get_bot_user

router = APIRouter(prefix="/inventory", tags=["inventory"])


class UsedCreate(BaseModel):
    title: str = Field(..., examples=["iPhone 13 128 Blue"])
    condition_grade: str = Field(..., examples=["A"])
    battery_health: int | None = Field(None, ge=0, le=100)
    imei: str
    sell_price_uzs: int = Field(..., ge=0)
    purchase_price_uzs: int | None = Field(None, ge=0)
    notes: str = ""
    telegram_photo_file_id: str | None = None


class InventoryOut(BaseModel):
    id: int
    title: str
    is_used: bool
    condition_grade: str
    battery_health: int | None
    imei: str | None
    sell_price_uzs: int
    status: InventoryStatus
    photo_file_id: str | None = None


@router.get("/bot/search", response_model=list[InventoryOut])
def bot_search(
    q: str | None = None,
    imei: str | None = None,
    status: InventoryStatus | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_bot_user),
):
    qs = db.query(InventoryItem)

    if imei:
        qs = qs.filter(InventoryItem.imei == imei)
    if q:
        qs = qs.filter(InventoryItem.title.ilike(f"%{q}%"))
    if status:
        qs = qs.filter(InventoryItem.status == status)

    items = qs.order_by(desc(InventoryItem.id)).limit(50).all()

    return [
        InventoryOut(
            id=i.id,
            title=i.title,
            is_used=i.is_used,
            condition_grade=i.condition_grade,
            battery_health=i.battery_health,
            imei=i.imei,
            sell_price_uzs=i.sell_price_uzs,
            status=i.status,
            photo_file_id=i.telegram_photo_file_id,
        )
        for i in items
    ]


@router.post("/bot/used", response_model=InventoryOut)
def bot_add_used(
    payload: UsedCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_bot_user),
):
    exists = db.query(InventoryItem).filter(InventoryItem.imei == payload.imei).first()
    if exists:
        raise HTTPException(status_code=409, detail="IMEI already exists")

    item = InventoryItem(
        title=payload.title,
        is_used=True,
        condition_grade=payload.condition_grade,
        battery_health=payload.battery_health,
        imei=payload.imei,
        sell_price_uzs=payload.sell_price_uzs,
        purchase_price_uzs=payload.purchase_price_uzs,
        status=InventoryStatus.in_stock,
        notes=payload.notes,
        telegram_photo_file_id=payload.telegram_photo_file_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return InventoryOut(
        id=item.id,
        title=item.title,
        is_used=item.is_used,
        condition_grade=item.condition_grade,
        battery_health=item.battery_health,
        imei=item.imei,
        sell_price_uzs=item.sell_price_uzs,
        status=item.status,
        photo_file_id=item.telegram_photo_file_id,
    )


class SellPayload(BaseModel):
    imei: str
    sell_price_uzs: int = Field(..., ge=0)
    channel: str = "shop"
    payment_type: str = "cash"


@router.post("/bot/sell")
def bot_sell(
    payload: SellPayload,
    db: Session = Depends(get_db),
    user: User = Depends(get_bot_user),
):
    item = db.query(InventoryItem).filter(InventoryItem.imei == payload.imei).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found by IMEI")

    if item.status == InventoryStatus.sold:
        raise HTTPException(status_code=409, detail="Already sold")

    item.status = InventoryStatus.sold
    item.sell_price_uzs = payload.sell_price_uzs

    ev = SaleEvent(
        item_id=item.id,
        telegram_id=user.telegram_id,
        sell_price_uzs=payload.sell_price_uzs,
        channel=payload.channel,
        payment_type=payload.payment_type,
    )
    db.add(ev)
    db.commit()

    return {"ok": True, "item_id": item.id}