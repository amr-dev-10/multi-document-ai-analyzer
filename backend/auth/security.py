import base64
import hashlib
import hmac
import json
import os
import time
from datetime import timedelta

from backend.core.config import settings


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or base64.urlsafe_b64encode(os.urandom(16)).decode()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return f"{salt}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
    salt, expected = password_hash.split("$", 1)
    return hmac.compare_digest(hash_password(password, salt), f"{salt}${expected}")


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    expiry = int(time.time() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes)).total_seconds())
    payload = {"sub": subject, "exp": expiry}
    signing_input = f"{_b64(json.dumps(header).encode())}.{_b64(json.dumps(payload).encode())}"
    signature = hmac.new(settings.secret_key.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64(signature)}"


def decode_access_token(token: str) -> dict:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}"
        expected = hmac.new(settings.secret_key.encode(), signing_input.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64(expected), signature_b64):
            raise ValueError("invalid signature")
        payload = json.loads(_unb64(payload_b64))
        if payload["exp"] < int(time.time()):
            raise ValueError("expired token")
        return payload
    except Exception as exc:
        raise ValueError("invalid token") from exc

