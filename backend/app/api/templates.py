from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.schemas.template import (
    TemplateListResponse,
    TemplateMeta,
    TemplateResponse,
)
from app.models import User
from app.services import css_template_service, template_service
from app.services.exceptions import TemplateError


router = APIRouter(prefix="/templates", tags=["Templates"])


def _parse_meta(template) -> TemplateMeta:
    try:
        return TemplateMeta.model_validate(template.schema_json or {})
    except Exception:
        return TemplateMeta()


def template_to_response(template) -> TemplateResponse:
    """Преобразуем ORM-объект в response-схему."""
    meta = _parse_meta(template)
    has_css = css_template_service.template_css_exists(template.code)
    css_url = css_template_service.css_url_for_code(template.code) if has_css else None

    return TemplateResponse(
        id=template.id,
        code=template.code,
        name=template.name,
        description=template.description,
        preview_image=template.preview_image,
        is_active=template.is_active,
        created_at=template.created_at,
        css_url=css_url,
        has_css=has_css,
        meta=meta,
        schema_data=meta,
    )


@router.get(
    "/{code}/css",
    summary="CSS шаблона (публичный)",
    response_class=Response,
)
def get_template_css(code: str, db: Session = Depends(get_db)) -> Response:
    """Отдаёт CSS без авторизации — нужно для публичных визиток."""
    try:
        template = template_service.get_template_by_code(db, code)
    except TemplateError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if not template.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон неактивен.",
        )

    try:
        css = css_template_service.read_template_css(template.code)
    except TemplateError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return Response(
        content=css,
        media_type="text/css; charset=utf-8",
        headers={"Cache-Control": "public, max-age=300"},
    )


@router.get(
    "",
    response_model=TemplateListResponse,
    summary="Список доступных шаблонов",
)
def list_templates(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TemplateListResponse:
    templates = template_service.get_active_templates(db)

    return TemplateListResponse(
        items=[template_to_response(t) for t in templates],
        total=len(templates),
    )


@router.get(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Получить шаблон по ID",
)
def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TemplateResponse:
    try:
        template = template_service.get_template(db, template_id)
    except TemplateError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    if not template.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Шаблон неактивен.",
        )

    return template_to_response(template)
