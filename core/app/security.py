import hmac
import hashlib
import time
from urllib.parse import parse_qsl
from jose import jwt
from pydantic import BaseModel
from .config import settings

class TelegramAuthPayload(BaseModel):
    initData: str

def _telegram_secret_key() -> bytes:
    return hashlib.sha256(settings.telegram_bot_token.encode("utf-8")).digest()

def verify_telegram_init_data(init_data: str, max_age_seconds: int = 24 * 60 * 60) -> dict:
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.get("hash")
    if not received_hash:
        raise ValueError("Missing hash")

    auth_date = pairs.get("auth_date")
    if auth_date:
        try:
            auth_ts = int(auth_date)
            if int(time.time()) - auth_ts > max_age_seconds:
                raise ValueError("initData expired")
        except ValueError:
            raise ValueError("Invalid auth_date")

    data_check_items = []
    for k in sorted(pairs.keys()):
        if k == "hash":
            continue
        data_check_items.append(f"{k}={pairs[k]}")
    data_check_string = "\n".join(data_check_items).encode("utf-8")

    calculated_hash = hmac.new(_telegram_secret_key(), data_check_string, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Bad hash")

    return pairs

def create_access_token(sub: str) -> str:
    now = int(time.time())
    exp = now + settings.jwt_expires_minutes * 60
    payload = {"sub": sub, "iat": now, "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])