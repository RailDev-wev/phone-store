from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..deps import get_current_user
from ..models import User, Role

router = APIRouter(tags=["me"])

class MeResponse(BaseModel):
    telegram_id: int
    name: str
    role: Role

@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)):
    return MeResponse(telegram_id=user.telegram_id, name=user.name, role=user.role)