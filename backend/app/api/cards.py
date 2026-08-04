from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.schemas.card import (
    CardCreate,
    CardListResponse,
    CardResponse,
    CardUpdate,
)
from app.api.schemas.common import MessageResponse
from app.models import User
from app.services import audit_service, card_service
from app.services.exceptions import (
    CardNotFoundError,
    TemplateNotFoundError,
)


router = APIRouter(prefix="/cards", tags=["Cards"])


@router.post(
    "",
    response_model=CardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать визитную карточку",
)
def create_card(
    payload: CardCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CardResponse:
    try:
        card = card_service.create_card(
            db=db,
            user=user,
            payload=payload,
        )
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card template not found or inactive.",
        ) from exc

    audit_service.log(
        db=db,
        action="card.create",
        actor_user_id=user.id,
        entity_type="card",
        entity_id=card.id,
        request=request,
    )

    return CardResponse.model_validate(card)


@router.get(
    "",
    response_model=CardListResponse,
    summary="Список визитных карточек текущего пользователя",
)
def list_cards(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CardListResponse:
    cards, total = card_service.list_cards(
        db=db,
        user=user,
        limit=limit,
        offset=offset,
    )

    return CardListResponse(
        items=[CardResponse.model_validate(card) for card in cards],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{card_id}",
    response_model=CardResponse,
    summary="Получить визитную карточку",
)
def get_card(
    card_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CardResponse:
    try:
        card = card_service.get_card(
            db=db,
            user=user,
            card_id=card_id,
        )
    except CardNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found.",
        ) from exc

    return CardResponse.model_validate(card)


@router.patch(
    "/{card_id}",
    response_model=CardResponse,
    summary="Обновить визитную карточку",
)
def update_card(
    card_id: str,
    payload: CardUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CardResponse:
    try:
        card = card_service.update_card(
            db=db,
            user=user,
            card_id=card_id,
            payload=payload,
        )
    except CardNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found.",
        ) from exc
    except TemplateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card template not found or inactive.",
        ) from exc

    updated_fields = list(payload.model_dump(exclude_unset=True).keys())

    audit_service.log(
        db=db,
        action="card.update",
        actor_user_id=user.id,
        entity_type="card",
        entity_id=card.id,
        request=request,
        details={
            "fields": updated_fields,
        },
    )

    return CardResponse.model_validate(card)


@router.delete(
    "/{card_id}",
    response_model=MessageResponse,
    summary="Удалить визитную карточку",
)
def delete_card(
    card_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MessageResponse:
    try:
        card_service.soft_delete_card(
            db=db,
            user=user,
            card_id=card_id,
        )
    except CardNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found.",
        ) from exc

    audit_service.log(
        db=db,
        action="card.delete",
        actor_user_id=user.id,
        entity_type="card",
        entity_id=card_id,
        request=request,
    )

    return MessageResponse(detail="Card deleted.")


@router.post(
    "/{card_id}/regenerate-slug",
    response_model=CardResponse,
    summary="Перегенерировать публичную ссылку визитки",
)
def regenerate_slug(
    card_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CardResponse:
    try:
        card = card_service.regenerate_card_slug(
            db=db,
            user=user,
            card_id=card_id,
        )
    except CardNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found.",
        ) from exc

    audit_service.log(
        db=db,
        action="card.regenerate_slug",
        actor_user_id=user.id,
        entity_type="card",
        entity_id=card.id,
        request=request,
    )

    return CardResponse.model_validate(card)