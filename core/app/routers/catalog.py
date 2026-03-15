from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
import httpx

from ..db import get_db
from ..models import InventoryItem, InventoryStatus
from ..config import settings

router = APIRouter(prefix="/catalog", tags=["catalog"])


class CatalogItem(BaseModel):
    id: int
    title: str
    is_used: bool
    condition_grade: str
    battery_health: int | None
    sell_price_uzs: int
    status: InventoryStatus
    photo_file_id: str | None


class CatalogItemDetail(CatalogItem):
    imei: str | None
    notes: str


@router.get("", response_model=list[CatalogItem])
def list_catalog(
    q: str | None = None,
    is_used: bool | None = None,
    grade: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    db: Session = Depends(get_db),
):
    qs = db.query(InventoryItem).filter(
        InventoryItem.status == InventoryStatus.in_stock
    )

    if q:
        qs = qs.filter(InventoryItem.title.ilike(f"%{q}%"))

    if is_used is not None:
        qs = qs.filter(InventoryItem.is_used == is_used)

    if grade:
        qs = qs.filter(InventoryItem.condition_grade == grade)

    if price_min is not None:
        qs = qs.filter(InventoryItem.sell_price_uzs >= price_min)

    if price_max is not None:
        qs = qs.filter(InventoryItem.sell_price_uzs <= price_max)

    items = qs.order_by(desc(InventoryItem.id)).limit(200).all()

    return [
        CatalogItem(
            id=i.id,
            title=i.title,
            is_used=i.is_used,
            condition_grade=i.condition_grade,
            battery_health=i.battery_health,
            sell_price_uzs=i.sell_price_uzs,
            status=i.status,
            photo_file_id=i.telegram_photo_file_id,
        )
        for i in items
    ]


@router.get("/{item_id}", response_model=CatalogItemDetail)
def get_item(item_id: int, db: Session = Depends(get_db)):
    i = db.query(InventoryItem).filter(
        InventoryItem.id == item_id
    ).first()

    if not i:
        raise HTTPException(status_code=404, detail="Not found")

    return CatalogItemDetail(
        id=i.id,
        title=i.title,
        is_used=i.is_used,
        condition_grade=i.condition_grade,
        battery_health=i.battery_health,
        sell_price_uzs=i.sell_price_uzs,
        status=i.status,
        photo_file_id=i.telegram_photo_file_id,
        imei=i.imei,
        notes=i.notes,
    )


@router.get("/photo/{item_id}")
async def get_photo(item_id: int, db: Session = Depends(get_db)):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()

    if not item or not item.telegram_photo_file_id:
        raise HTTPException(status_code=404, detail="No photo")

    file_id = item.telegram_photo_file_id

    async with httpx.AsyncClient(timeout=20) as client:
        tg_file_resp = await client.get(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/getFile",
            params={"file_id": file_id},
        )

        tg_file_data = tg_file_resp.json()

        if not tg_file_data.get("ok"):
            raise HTTPException(status_code=500, detail="Telegram getFile failed")

        file_path = tg_file_data["result"]["file_path"]
        file_url = f"https://api.telegram.org/file/bot{settings.telegram_bot_token}/{file_path}"

        img_resp = await client.get(file_url)

        if img_resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Telegram file download failed")

    return StreamingResponse(
        iter([img_resp.content]),
        media_type="image/jpeg",
    )