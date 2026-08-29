from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_superadmin, get_db
from app.api.schemas.admin import (
    AdminCardListResponse,
    AdminCardResponse,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserCreate,
    AdminUserUpdate,
    AuditLogListResponse,
    AuditLogResponse,
    BackupFileResponse,
    BackupListResponse,
    BackupRestoreRequest,
    BackupRestoreResponse,
    BackupRunResponse,
    BackupSettingsResponse,
    BackupSettingsUpdate,
    OverviewStatsResponse,
)
from app.models import User
from app.services import admin_service, audit_service, analytics_service, css_template_service
from app.services import backup_service
from app.services.admin_service import AdminError
from app.services.backup_service import BackupError
from app.api.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
)
from app.api.templates import template_to_response
from app.services import template_service
from app.services.exceptions import TemplateError
from app.services.css_template_service import MAX_CSS_BYTES

from typing import Literal

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=AdminUserListResponse, summary="Список пользователей")
def list_users(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> AdminUserListResponse:
    users, total = admin_service.get_users(db, limit, offset, search)
    
    return AdminUserListResponse(
        items=[AdminUserResponse.model_validate(u) for u in users],
        total=total,
        limit=limit,
        offset=offset,
    )

@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED, summary="Создать пользователя")
def create_user(
    payload: AdminUserCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> AdminUserResponse:
    try:
        user = admin_service.create_user(db, admin, payload)
    except AdminError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    audit_service.log(
        db=db,
        action="admin.user_create",
        actor_user_id=admin.id,
        entity_type="user",
        entity_id=user.id,
        request=request,
    )

    return AdminUserResponse.model_validate(user)


@router.delete("/users/{user_id}", summary="Удалить пользователя")
def delete_user(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
) -> dict:
    try:
        admin_service.delete_user(db, admin, user_id)
    except AdminError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    audit_service.log(
        db=db,
        action="admin.user_delete",
        actor_user_id=admin.id,
        entity_type="user",
        entity_id=user_id,
        request=request,
    )

    return {"detail": "Пользователь удален."}

@router.patch("/users/{user_id}", response_model=AdminUserResponse, summary="Обновить пользователя")
def update_user(
    user_id: str,
    payload: AdminUserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> AdminUserResponse:
    try:
        user = admin_service.update_user(db, admin, user_id, payload)
    except AdminError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    audit_details = payload.model_dump(exclude_unset=True)
    if "password" in audit_details:
        audit_details["password"] = "***"

    audit_service.log(
        db=db,
        action="admin.user_update",
        actor_user_id=admin.id,
        entity_type="user",
        entity_id=user_id,
        request=request,
        details=audit_details,
    )

    return AdminUserResponse.model_validate(user)


@router.get("/cards", response_model=AdminCardListResponse, summary="Все визитки")
def list_cards(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> AdminCardListResponse:
    cards_data, total = admin_service.get_cards(db, limit, offset, search)
    
    items = []
    for data in cards_data:
        card = data["card"]
        items.append(AdminCardResponse(
            id=card.id,
            slug=card.slug,
            title=card.title,
            full_name=card.full_name,
            is_active=card.is_active,
            created_at=card.created_at,
            user_email=data["user_email"],
            visits_count=data["visits_count"],
        ))

    return AdminCardListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/cards/{card_id}/deactivate", summary="Отключить визитку")
def deactivate_card(
    card_id: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> dict:
    try:
        card = admin_service.deactivate_card(db, card_id)
    except AdminError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    audit_service.log(
        db=db,
        action="admin.card_deactivate",
        actor_user_id=admin.id,
        entity_type="card",
        entity_id=card_id,
        request=request,
    )

    return {"detail": "Визитка отключена.", "is_active": card.is_active}

@router.get("/templates", summary="Список всех шаблонов (админ)")
def list_admin_templates(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    results, total = template_service.get_admin_templates(db, limit, offset, search)

    items = []
    for template, cards_count in results:
        base = template_to_response(template).model_dump()
        base["updated_at"] = template.updated_at
        base["cards_count"] = cards_count
        items.append(base)

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post(
    "/templates/{template_id}/css",
    summary="Загрузить CSS шаблона (админ)",
)
async def upload_admin_template_css(
    template_id: str,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    try:
        template = template_service.get_template(db, template_id)
    except TemplateError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    raw = await file.read(MAX_CSS_BYTES + 1)
    if len(raw) > MAX_CSS_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSS файл слишком большой.",
        )

    try:
        css_text = raw.decode("utf-8")
        css_template_service.write_template_css(template.code, css_text)
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSS должен быть в кодировке UTF-8.",
        ) from exc
    except TemplateError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    audit_service.log(
        db=db,
        action="admin.template_css_upload",
        actor_user_id=admin.id,
        entity_type="template",
        entity_id=template_id,
        request=request,
        details={"code": template.code, "bytes": len(raw)},
    )

    return template_to_response(template)


@router.post("/templates", status_code=status.HTTP_201_CREATED, summary="Создать шаблон (админ)")
def create_admin_template(
    payload: TemplateCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    try:
        template = template_service.create_template(db, payload)
    except TemplateError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    audit_service.log(
        db=db,
        action="admin.template_create",
        actor_user_id=admin.id,
        entity_type="template",
        entity_id=template.id,
        request=request,
    )

    return {
        "id": template.id,
        "code": template.code,
        "name": template.name,
        "is_active": template.is_active,
    }


@router.patch("/templates/{template_id}", summary="Обновить шаблон (админ)")
def update_admin_template(
    template_id: str,
    payload: TemplateUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    try:
        template = template_service.update_template(db, template_id, payload)
    except TemplateError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    audit_service.log(
        db=db,
        action="admin.template_update",
        actor_user_id=admin.id,
        entity_type="template",
        entity_id=template_id,
        request=request,
        details=payload.model_dump(exclude_unset=True),
    )

    return {
        "id": template.id,
        "code": template.code,
        "name": template.name,
        "is_active": template.is_active,
    }


@router.post("/templates/{template_id}/toggle-active", summary="Активировать/деактивировать шаблон (админ)")
def toggle_admin_template(
    template_id: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    try:
        template = template_service.toggle_template_active(db, template_id)
    except TemplateError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    audit_service.log(
        db=db,
        action="admin.template_toggle",
        actor_user_id=admin.id,
        entity_type="template",
        entity_id=template_id,
        request=request,
        details={"is_active": template.is_active},
    )

    return {
        "id": template.id,
        "is_active": template.is_active,
    }


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить шаблон (админ)")
def delete_admin_template(
    template_id: str,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    try:
        template_service.delete_template(db, template_id)
    except TemplateError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    audit_service.log(
        db=db,
        action="admin.template_delete",
        actor_user_id=admin.id,
        entity_type="template",
        entity_id=template_id,
        request=request,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/audit", response_model=AuditLogListResponse, summary="Журнал аудита")
def list_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    action: str | None = Query(default=None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> AuditLogListResponse:
    logs_data, total = admin_service.get_audit_logs(db, limit, offset, action)
    
    items = []
    for data in logs_data:
        log = data["log"]
        items.append(AuditLogResponse(
            id=log.id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            created_at=log.created_at,
            actor_email=data["actor_email"],
            details=log.details_json,
        ))

    return AuditLogListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )

@router.get(
    "/analytics/extended",
    summary="Расширенная аналитика системы",
)
def get_extended_analytics(
    period: Literal["7d", "30d", "90d"] = "30d",
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    return analytics_service.get_extended_analytics(db, period)
    
@router.get("/stats/overview", response_model=OverviewStatsResponse, summary="Общая статистика")
def get_overview_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
) -> OverviewStatsResponse:
    stats = admin_service.get_overview_stats(db)
    return OverviewStatsResponse(**stats)


@router.get(
    "/settings/backup",
    response_model=BackupSettingsResponse,
    summary="Настройки резервного копирования",
)
def get_backup_settings(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
) -> BackupSettingsResponse:
    row = backup_service.get_or_create_settings(db)
    return BackupSettingsResponse.model_validate(row)


@router.patch(
    "/settings/backup",
    response_model=BackupSettingsResponse,
    summary="Обновить настройки резервного копирования",
)
def patch_backup_settings(
    payload: BackupSettingsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
) -> BackupSettingsResponse:
    try:
        row = backup_service.update_settings(
            db,
            **payload.model_dump(exclude_unset=True),
        )
    except BackupError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    audit_service.log(
        db=db,
        action="admin.backup_settings_update",
        actor_user_id=admin.id,
        entity_type="backup_settings",
        entity_id="1",
        request=request,
        details=payload.model_dump(exclude_unset=True),
    )
    return BackupSettingsResponse.model_validate(row)


@router.get(
    "/settings/backup/files",
    response_model=BackupListResponse,
    summary="Список файлов резервных копий",
)
def list_backup_files(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
) -> BackupListResponse:
    try:
        items = backup_service.list_backups(db)
    except BackupError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return BackupListResponse(
        items=[BackupFileResponse.model_validate(i.__dict__) for i in items]
    )


@router.post(
    "/settings/backup/run",
    response_model=BackupRunResponse,
    summary="Принудительно создать резервную копию",
)
def run_backup_now(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
) -> BackupRunResponse:
    try:
        info = backup_service.create_backup(db)
    except BackupError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    audit_service.log(
        db=db,
        action="admin.backup_run",
        actor_user_id=admin.id,
        entity_type="backup",
        entity_id=info.filename,
        request=request,
        details={"size_bytes": info.size_bytes},
    )
    return BackupRunResponse(
        filename=info.filename,
        size_bytes=info.size_bytes,
        created_at=info.created_at,
    )


@router.post(
    "/settings/backup/restore",
    response_model=BackupRestoreResponse,
    summary="Восстановить из резервной копии",
)
def restore_backup_now(
    payload: BackupRestoreRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_superadmin),
) -> BackupRestoreResponse:
    actor_id = admin.id
    try:
        detail = backup_service.restore_backup(db, payload.filename)
    except BackupError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # После restore исходная ORM-сессия и пользовательские сессии недействительны.
    try:
        from app.db.session import SessionLocal

        audit_db = SessionLocal()
        try:
            audit_service.log(
                db=audit_db,
                action="admin.backup_restore",
                actor_user_id=actor_id,
                entity_type="backup",
                entity_id=payload.filename,
                request=request,
            )
        finally:
            audit_db.close()
    except Exception:  # noqa: BLE001
        pass

    return BackupRestoreResponse(detail=detail)
