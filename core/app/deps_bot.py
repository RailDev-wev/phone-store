from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from .db import get_db
from .config import settings
from .models import User, Role


def require_bot(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    if not x_api_key or x_api_key.strip() != settings.internal_api_key:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key")


def get_bot_user(
    db: Session = Depends(get_db),
    x_tg_userid: str | None = Header(default=None, alias="X-TG-UserId"),
    _bot=Depends(require_bot),
) -> User:
    if not x_tg_userid:
        raise HTTPException(status_code=401, detail="Missing X-TG-UserId")

    try:
        telegram_id = int(x_tg_userid)
    except Exception:
        raise HTTPException(status_code=400, detail="Bad X-TG-UserId")

    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(
            telegram_id=telegram_id,
            name="",
            role=Role.seller,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User not active")

    return user