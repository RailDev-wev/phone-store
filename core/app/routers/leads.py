from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, Field

from ..db import get_db
from ..config import settings
from ..models import Lead, LeadStatus, InventoryItem

router = APIRouter(prefix="/leads", tags=["leads"])


def require_key(x_api_key: str | None):
    if not x_api_key or x_api_key.strip() != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key")


class LeadCreate(BaseModel):
    item_id: int
    full_name: str = Field(..., min_length=2, max_length=120)
    phone: str = Field(..., min_length=6, max_length=40)
    installment_months: int = Field(..., ge=1, le=36)
    comment: str = Field("", max_length=2000)


class LeadOut(BaseModel):
    id: int
    item_id: int
    item_title: str
    full_name: str
    phone: str
    installment_months: int
    comment: str
    status: LeadStatus
    assigned_to_telegram_id: int | None


@router.post("", response_model=LeadOut)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    item = db.query(InventoryItem).filter(InventoryItem.id == payload.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    lead = Lead(
        item_id=payload.item_id,
        item_title=item.title,
        full_name=payload.full_name.strip(),
        phone=payload.phone.strip(),
        installment_months=payload.installment_months,
        comment=payload.comment.strip(),
        status=LeadStatus.new,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    return LeadOut(
        id=lead.id,
        item_id=lead.item_id,
        item_title=lead.item_title,
        full_name=lead.full_name,
        phone=lead.phone,
        installment_months=lead.installment_months,
        comment=lead.comment,
        status=lead.status,
        assigned_to_telegram_id=lead.assigned_to_telegram_id,
    )


@router.get("/pending", response_model=list[LeadOut])
def pending_leads(
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    require_key(x_api_key)

    leads = (
        db.query(Lead)
        .filter(Lead.status == LeadStatus.new)
        .order_by(desc(Lead.id))
        .limit(50)
        .all()
    )

    return [
        LeadOut(
            id=l.id,
            item_id=l.item_id,
            item_title=l.item_title,
            full_name=l.full_name,
            phone=l.phone,
            installment_months=l.installment_months,
            comment=l.comment,
            status=l.status,
            assigned_to_telegram_id=l.assigned_to_telegram_id,
        )
        for l in leads
    ]


class LeadUpdate(BaseModel):
    status: LeadStatus
    assigned_to_telegram_id: int | None = None


@router.post("/{lead_id}/update", response_model=LeadOut)
def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    require_key(x_api_key)

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.status = payload.status
    lead.assigned_to_telegram_id = payload.assigned_to_telegram_id
    db.commit()
    db.refresh(lead)

    return LeadOut(
        id=lead.id,
        item_id=lead.item_id,
        item_title=lead.item_title,
        full_name=lead.full_name,
        phone=lead.phone,
        installment_months=lead.installment_months,
        comment=lead.comment,
        status=lead.status,
        assigned_to_telegram_id=lead.assigned_to_telegram_id,
    )