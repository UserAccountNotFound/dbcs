from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.schemas.card import (
    CardCreate,
    CardImportResult,
    CardListResponse,
    CardResponse,
    CardUpdate,
)
from app.api.schemas.common import MessageResponse
from app.api.schemas.stats import CardStatsResponse
from app.core.urls import get_public_card_url
from app.models import User
from app.services import (
    audit_service,
    card_service,
    card_transfer_service,
    qr_service,
    stats_service,
    vcard_service,
)
from app.services.exceptions import (
    CardImportError,
    CardNotFoundError,
    InvalidFileError,
    SlugGenerationError,
    TemplateNotFoundError,
)


router = APIRouter(prefix="/cards", tags=["Cards"])


def _map_card_write_errors(exc: Exception) -> HTTPException:
    if isinstance(exc, TemplateNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card template not found or inactive.",
        )
    if isinstance(exc, InvalidFileError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    if isinstance(exc, SlugGenerationError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to generate unique card slug. Please try again.",
        )
    raise exc


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
    except (TemplateNotFoundError, InvalidFileError, SlugGenerationError) as exc:
        raise _map_card_write_errors(exc) from exc

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
    "/export",
    response_class=Response,
    summary="Экспорт визиток текущего пользователя (JSON или CSV)",
)
def export_cards(
    request: Request,
    format: str = Query(default="json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    fmt = format.lower()  # type: ignore[assignment]
    if fmt == "csv":
        content = card_transfer_service.export_cards_csv(db, user)
        media_type = "text/csv; charset=utf-8"
        filename = "dbcs-cards.csv"
    else:
        content = card_transfer_service.export_cards_json(db, user)
        media_type = "application/json; charset=utf-8"
        filename = "dbcs-cards.json"

    audit_service.log(
        db=db,
        action="card.export",
        actor_user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        request=request,
        details={"format": fmt},
    )

    return Response(
        content=content.encode("utf-8"),
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@router.post(
    "/import",
    response_model=CardImportResult,
    summary="Импорт визиток текущего пользователя (JSON или CSV)",
)
async def import_cards(
    request: Request,
    format: str = Query(default="json", pattern="^(json|csv)$"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CardImportResult:
    fmt = format.lower()
    raw = await file.read()
    if len(raw) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large (max 2 MB).",
        )

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded.",
        ) from exc

    try:
        result = card_transfer_service.import_cards(
            db=db,
            user=user,
            content=text,
            fmt=fmt,  # type: ignore[arg-type]
        )
    except CardImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    audit_service.log(
        db=db,
        action="card.import",
        actor_user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        request=request,
        details={
            "format": fmt,
            "created": result["created"],
            "failed": result["failed"],
        },
    )

    return CardImportResult.model_validate(result)


@router.get(
    "/{card_id}/stats",
    response_model=CardStatsResponse,
    summary="Статистика визитной карточки",
)
def get_card_stats(
    card_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CardStatsResponse:
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

    return stats_service.get_card_stats(db, card)


@router.get(
    "/{card_id}/vcard.vcf",
    response_class=Response,
    summary="Экспорт vCard визитной карточки",
)
def export_card_vcard(
    card_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
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

    audit_service.log(
        db=db,
        action="card.export_vcard",
        actor_user_id=user.id,
        entity_type="card",
        entity_id=card.id,
        request=request,
    )

    content = vcard_service.build_vcard(card)

    return Response(
        content=content,
        media_type="text/vcard; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{card.slug}.vcf"',
            "Cache-Control": "no-store",
        },
    )


@router.get(
    "/{card_id}/qrcode.svg",
    response_class=Response,
    summary="QR-код визитной карточки",
)
def get_card_qrcode(
    card_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
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

    public_url = get_public_card_url(card.slug)
    svg_content = qr_service.generate_qr_svg(public_url)

    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "no-store",
        },
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
    except (TemplateNotFoundError, InvalidFileError, SlugGenerationError) as exc:
        raise _map_card_write_errors(exc) from exc

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
    except SlugGenerationError as exc:
        raise _map_card_write_errors(exc) from exc

    audit_service.log(
        db=db,
        action="card.regenerate_slug",
        actor_user_id=user.id,
        entity_type="card",
        entity_id=card.id,
        request=request,
    )

    return CardResponse.model_validate(card)