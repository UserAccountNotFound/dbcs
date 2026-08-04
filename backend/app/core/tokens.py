import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt

from app.core.config import settings
from app.models.enums import UserRole


ALGORITHM = "HS256"

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


class InvalidTokenError(Exception):
    pass


def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid4()),
        "type": token_type,
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def create_access_token(user_id: str, role: UserRole) -> str:
    return _create_token(
        subject=user_id,
        token_type=ACCESS_TOKEN_TYPE,
        expires_delta=timedelta(minutes=settings.access_token_ttl_minutes),
        extra_claims={
            "role": role.value,
        },
    )


def create_refresh_token(user_id: str, session_id: str) -> str:
    return _create_token(
        subject=user_id,
        token_type=REFRESH_TOKEN_TYPE,
        expires_delta=timedelta(days=settings.refresh_token_ttl_days),
        extra_claims={
            "sid": session_id,
        },
    )


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Invalid token.") from exc

    token_type = payload.get("type")

    if token_type != expected_type:
        raise InvalidTokenError("Invalid token type.")

    return payload


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()