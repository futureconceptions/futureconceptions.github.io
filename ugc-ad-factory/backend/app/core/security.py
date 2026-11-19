"""Password hashing, JWT access tokens, HMAC-signed URLs and webhook tokens."""
from __future__ import annotations

import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def _key() -> bytes:
    return get_settings().secret_key.get_secret_value().encode()


def create_access_token(user_id: str, role: str) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    payload = {"sub": user_id, "role": role, "iat": now,
               "exp": now + timedelta(minutes=s.access_token_ttl_minutes)}
    return jwt.encode(payload, _key(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, _key(), algorithms=[ALGORITHM])


def _hmac(msg: str) -> str:
    return hmac.new(_key(), msg.encode(), hashlib.sha256).hexdigest()


def sign_path(key: str, ttl: int | None = None) -> tuple[int, str]:
    exp = int(time.time()) + (ttl or get_settings().signed_url_ttl_seconds)
    return exp, _hmac(f"file:{key}:{exp}")


def verify_signed_path(key: str, exp: int, sig: str) -> bool:
    if exp < time.time():
        return False
    return hmac.compare_digest(_hmac(f"file:{key}:{exp}"), sig)


def webhook_token(job_id: str) -> str:
    """Per-job secret embedded in the webhook URL. LetzAI documents no webhook
    signature, so the URL token authenticates the caller and the payload is
    never trusted: we always re-fetch job state from the API."""
    return _hmac(f"webhook:{job_id}")[:40]


def verify_webhook_token(job_id: str, token: str) -> bool:
    return hmac.compare_digest(webhook_token(job_id), token or "")
