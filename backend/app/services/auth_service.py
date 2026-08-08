from datetime import timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password
from app.core.tokens import (
    REFRESH_TOKEN_TYPE,
    InvalidTokenError,
    create_refresh_token,
    decode_token,
    hash_token,
)
from app.db.base import utcnow
from app.models import AuthSession, User
from app.services import user_service
from app.services.exceptions import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User:
    user = user_service.get_by_email(db, email)

    if user is None:
        raise InvalidCredentialsError("Invalid email or password.")

    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("Invalid email or password.")

    if not user.is_active:
        raise InvalidCredentialsError("Invalid email or password.")

    return user


def create_refresh_session(
    db: Session,
    user: User,
    user_agent_hash: str | None,
    ip_hash: str | None,
) -> tuple[str, AuthSession]:
    session_id = str(uuid4())

    refresh_token = create_refresh_token(
        user_id=user.id,
        session_id=session_id,
    )

    expires_at = utcnow() + timedelta(days=settings.refresh_token_ttl_days)

    session = AuthSession(
        id=session_id,
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        user_agent_hash=user_agent_hash,
        ip_hash=ip_hash,
        expires_at=expires_at,
    )

    db.add(session)
    db.commit()

    return refresh_token, session


def get_active_session_by_token(
    db: Session,
    refresh_token: str,
) -> tuple[AuthSession, dict]:
    try:
        payload = decode_token(refresh_token, REFRESH_TOKEN_TYPE)
    except InvalidTokenError as exc:
        raise InvalidRefreshTokenError("Invalid refresh token.") from exc

    session_id = payload.get("sid")
    user_id = payload.get("sub")

    if not session_id or not user_id:
        raise InvalidRefreshTokenError("Invalid refresh token payload.")

    session = db.get(AuthSession, session_id)

    if session is None:
        raise InvalidRefreshTokenError("Session not found.")

    if session.user_id != user_id:
        raise InvalidRefreshTokenError("Session does not belong to token subject.")

    if session.revoked_at is not None:
        raise InvalidRefreshTokenError("Session revoked.")

    if session.expires_at < utcnow():
        raise InvalidRefreshTokenError("Session expired.")

    if session.refresh_token_hash != hash_token(refresh_token):
        raise InvalidRefreshTokenError("Refresh token hash mismatch.")

    return session, payload


def revoke_session(db: Session, session: AuthSession) -> None:
    if session.revoked_at is None:
        session.revoked_at = utcnow()
        db.commit()