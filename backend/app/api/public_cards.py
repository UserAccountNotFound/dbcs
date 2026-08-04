from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas.public_card import (
    PublicCardResponse,
    build_public_card_response,
)
from app.core.urls import get_public_card_url
from app.services import public_card_service, qr_service, vcard_service
from app.services.exceptions import CardNotFoundError


router = APIRouter(prefix="/public/cards", tags=["Public Cards"])


@router.get(
    "/{slug}",
    response_model=PublicCardResponse,
    summary="Публичная визитная карточка",
)
def get_public_card(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> PublicCardResponse:
    try:
        card = public_card_service.get_active_public_card(db, slug)
    except CardNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found.",
        ) from exc

    public_card_service.record_visit(
        db=db,
        card=card,
        request=request,
        source=public_card_service.SOURCE_CARD_VIEW,
    )

    return build_public_card_response(card)


@router.get(
    "/{slug}/vcard.vcf",
    response_class=Response,
    summary="Скачать vCard публичной визитки",
)
def get_public_card_vcard(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    try:
        card = public_card_service.get_active_public_card(db, slug)
    except CardNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found.",
        ) from exc

    public_card_service.record_visit(
        db=db,
        card=card,
        request=request,
        source=public_card_service.SOURCE_VCARD_DOWNLOAD,
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
    "/{slug}/qrcode.svg",
    response_class=Response,
    summary="QR-код публичной визитки",
)
def get_public_card_qrcode(
    slug: str,
    db: Session = Depends(get_db),
) -> Response:
    try:
        card = public_card_service.get_active_public_card(db, slug)
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