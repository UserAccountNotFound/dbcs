from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.schemas.template import (
    TemplateListResponse,
    TemplateResponse,
    TemplateSchema,
)
from app.models import User
from app.services import template_service
from app.services.exceptions import TemplateError


router = APIRouter(prefix="/templates", tags=["Templates"])


def _template_to_response(template) -> TemplateResponse:
    """Преобразуем ORM-объект в response-схему."""
    schema_data = None
    if template.schema_json:
        try:
            schema_data = TemplateSchema.model_validate(template.schema_json)
        except Exception:
            schema_data = TemplateSchema()

    return TemplateResponse(
        id=template.id,
        code=template.code,
        name=template.name,
        description=template.description,
        preview_image=template.preview_image,
        is_active=template.is_active,
        created_at=template.created_at,
        schema_data=schema_data,
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
        items=[_template_to_response(t) for t in templates],
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

    return _template_to_response(template)