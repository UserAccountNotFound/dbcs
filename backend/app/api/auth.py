from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.schemas.auth import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    UserResponse,
)
from app.core.config import settings
from app.core.security import hash_pii
from app.core.tokens import create_access_token
from app.core.utils import get_client_ip, get_user_agent
from app.db.base import utcnow
from app.models import User
from app.services import audit_service, auth_service, user_service
from app.services.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)


router = APIRouter(prefix="/auth", tags=["Auth"])


def _auth_cookie_path() -> str:
    return f"{settings.api_v1_prefix}/auth"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    max_age = settings.refresh_token_ttl_days * 24 * 60 * 60

    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        max_age=max_age,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path=_auth_cookie_path(),
    )


def _delete_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path=_auth_cookie_path(),
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
    )


def _build_auth_response(user: User, access_token: str) -> AuthResponse:
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_ttl_minutes * 60,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
)
def register(
    payload: RegisterRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
) -> AuthResponse:
    if not settings.self_registration_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-registration is disabled.",
        )

    try:
        user = user_service.create_user(
            db=db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
        )
    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        ) from exc

    access_token = create_access_token(user.id, user.role)

    refresh_token, _ = auth_service.create_refresh_session(
        db=db,
        user=user,
        user_agent_hash=hash_pii(get_user_agent(request)),
        ip_hash=hash_pii(get_client_ip(request)),
    )

    user.last_login_at = utcnow()
    db.commit()

    audit_service.log(
        db=db,
        action="auth.register",
        actor_user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        request=request,
    )

    _set_refresh_cookie(response, refresh_token)

    return _build_auth_response(user, access_token)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Вход пользователя",
)
def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
) -> AuthResponse:
    try:
        user = auth_service.authenticate_user(
            db=db,
            email=payload.email,
            password=payload.password,
        )
    except InvalidCredentialsError as exc:
        audit_service.log(
            db=db,
            action="auth.login_failed",
            request=request,
            details={
                "email_hash": hash_pii(payload.email),
            },
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        ) from exc

    access_token = create_access_token(user.id, user.role)

    refresh_token, _ = auth_service.create_refresh_session(
        db=db,
        user=user,
        user_agent_hash=hash_pii(get_user_agent(request)),
        ip_hash=hash_pii(get_client_ip(request)),
    )

    user.last_login_at = utcnow()
    db.commit()

    audit_service.log(
        db=db,
        action="auth.login",
        actor_user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        request=request,
    )

    _set_refresh_cookie(response, refresh_token)

    return _build_auth_response(user, access_token)


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Обновление access token по refresh cookie",
)
def refresh_tokens(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
) -> AuthResponse:
    refresh_token = request.cookies.get(settings.refresh_cookie_name)

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found.",
        )

    try:
        session, _ = auth_service.get_active_session_by_token(
            db=db,
            refresh_token=refresh_token,
        )
    except InvalidRefreshTokenError as exc:
        _delete_refresh_cookie(response)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        ) from exc

    user = db.get(User, session.user_id)

    if user is None or not user.is_active:
        auth_service.revoke_session(db, session)
        _delete_refresh_cookie(response)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is unavailable.",
        )

    auth_service.revoke_session(db, session)

    access_token = create_access_token(user.id, user.role)

    new_refresh_token, _ = auth_service.create_refresh_session(
        db=db,
        user=user,
        user_agent_hash=hash_pii(get_user_agent(request)),
        ip_hash=hash_pii(get_client_ip(request)),
    )

    audit_service.log(
        db=db,
        action="auth.refresh",
        actor_user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        request=request,
    )

    _set_refresh_cookie(response, new_refresh_token)

    return _build_auth_response(user, access_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Выход пользователя",
)
def logout(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
) -> MessageResponse:
    refresh_token = request.cookies.get(settings.refresh_cookie_name)

    if refresh_token:
        try:
            session, _ = auth_service.get_active_session_by_token(
                db=db,
                refresh_token=refresh_token,
            )

            auth_service.revoke_session(db, session)

            audit_service.log(
                db=db,
                action="auth.logout",
                actor_user_id=session.user_id,
                entity_type="user",
                entity_id=session.user_id,
                request=request,
            )
        except InvalidRefreshTokenError:
            pass

    _delete_refresh_cookie(response)

    return MessageResponse(detail="Logged out.")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Текущий пользователь",
)
def me(
    user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(user)