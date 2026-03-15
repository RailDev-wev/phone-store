from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

from ..db import get_db
from ..config import settings
from ..models import SaleEvent, InventoryItem, InventoryStatus

router = APIRouter(prefix="/reports", tags=["reports"])


def require_key(x_api_key: str | None):
    if not x_api_key or x_api_key.strip() != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key")


@router.get("/today")
def today(
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    require_key(x_api_key)

    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    sold_count = db.query(func.count(SaleEvent.id)).filter(SaleEvent.created_at >= start).scalar() or 0
    sold_sum_uzs = db.query(func.coalesce(func.sum(SaleEvent.sell_price_uzs), 0)).filter(
        SaleEvent.created_at >= start
    ).scalar() or 0
    in_stock = db.query(func.count(InventoryItem.id)).filter(
        InventoryItem.status == InventoryStatus.in_stock
    ).scalar() or 0

    return {
        "date_utc": start.isoformat(),
        "sold_count": int(sold_count),
        "sold_sum_uzs": int(sold_sum_uzs),
        "in_stock": int(in_stock),
    }


class AvgReport(BaseModel):
    days: int
    avg_sales_per_day: float
    avg_revenue_uzs_per_day: float
    total_sales: int
    total_revenue_uzs: int


@router.get("/averages", response_model=list[AvgReport])
def averages(
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    require_key(x_api_key)

    now = datetime.now(timezone.utc)
    out: list[AvgReport] = []

    for days in (7, 14, 30):
        start = now - timedelta(days=days)
        total_sales = db.query(func.count(SaleEvent.id)).filter(SaleEvent.created_at >= start).scalar() or 0
        total_uzs = db.query(func.coalesce(func.sum(SaleEvent.sell_price_uzs), 0)).filter(
            SaleEvent.created_at >= start
        ).scalar() or 0

        out.append(
            AvgReport(
                days=days,
                avg_sales_per_day=round(int(total_sales) / days, 2),
                avg_revenue_uzs_per_day=round(int(total_uzs) / days, 2),
                total_sales=int(total_sales),
                total_revenue_uzs=int(total_uzs),
            )
        )

    return out


class Forecast30(BaseModel):
    expected_sales_30d: float
    expected_revenue_uzs_30d: float
    basis_days: int
    avg_sales_per_day: float
    avg_revenue_uzs_per_day: float


@router.get("/forecast/30d", response_model=Forecast30)
def forecast_30d(
    basis_days: int = 30,
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    require_key(x_api_key)

    basis_days = max(1, min(90, int(basis_days)))
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=basis_days)

    total_sales = db.query(func.count(SaleEvent.id)).filter(SaleEvent.created_at >= start).scalar() or 0
    total_uzs = db.query(func.coalesce(func.sum(SaleEvent.sell_price_uzs), 0)).filter(
        SaleEvent.created_at >= start
    ).scalar() or 0

    avg_sales = int(total_sales) / basis_days
    avg_rev = int(total_uzs) / basis_days

    return Forecast30(
        expected_sales_30d=round(avg_sales * 30, 2),
        expected_revenue_uzs_30d=round(avg_rev * 30, 2),
        basis_days=basis_days,
        avg_sales_per_day=round(avg_sales, 2),
        avg_revenue_uzs_per_day=round(avg_rev, 2),
    )