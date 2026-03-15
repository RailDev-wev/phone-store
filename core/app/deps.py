from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from .db import get_db
from .security import decode_token
from .models import User

bearer = HTTPBearer(auto_error=False)

def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not creds:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        data = decode_token(creds.credentials)
        sub = data.get("sub")
        if not sub:
            raise ValueError("no sub")
        telegram_id = int(sub)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.telegram_id == telegram_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=403, detail="User not allowed")
    return user