import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..db import get_db
from ..models import User, Role
from ..security import TelegramAuthPayload, verify_telegram_init_data, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/telegram", response_model=AuthResponse)
def auth_telegram(payload: TelegramAuthPayload, db: Session = Depends(get_db)):
    try:
        parsed = verify_telegram_init_data(payload.initData)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user_json = parsed.get("user")
    if not user_json:
        raise HTTPException(status_code=401, detail="No user in initData")

    try:
        user_obj = json.loads(user_json)
        telegram_id = int(user_obj["id"])
        name = (user_obj.get("first_name") or "") + " " + (user_obj.get("last_name") or "")
        name = name.strip()
    except Exception:
        raise HTTPException(status_code=401, detail="Bad user format")

    # MVP: auto-create user. Later: invite/whitelist.
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, name=name, role=Role.seller, is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(sub=str(user.telegram_id))
    return AuthResponse(access_token=token)