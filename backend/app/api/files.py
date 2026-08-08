from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.schemas.file import FileResponse as FileResponseSchema
from app.models import User
from app.services import audit_service, file_service
from app.services.exceptions import (
    FileTooLargeError,
    UnsupportedFileTypeError,
    InvalidFileError,
    FileNotFoundError as FileNotFoundServiceError,
)

router = APIRouter(prefix="/files", tags=["Files"])


@router.post(
    "/upload",
    response_model=FileResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузить изображение (аватар/логотип)",
)
async def upload_file(
    file: UploadFile,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FileResponseSchema:
    try:
        file_record = file_service.upload_file(db, user.id, file)
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except (UnsupportedFileTypeError, InvalidFileError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    
    audit_service.log(
        db=db,
        action="file.upload",
        actor_user_id=user.id,
        entity_type="file",
        entity_id=file_record.id,
        request=request,
        details={
            "original_name": file_record.original_name,
            "size_bytes": file_record.size_bytes,
            "mime_type": file_record.mime_type,
        },
    )
    
    return FileResponseSchema.model_validate(file_record)


@router.get(
    "/{file_id}",
    summary="Скачать файл (с проверкой прав)",
)
def get_file(
    file_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    try:
        file = file_service.get_file(db, file_id)
    except FileNotFoundServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден.",
        ) from exc
    
    # Проверка прав: только владелец может скачать файл
    if file.owner_user_id != user.id and user.role.value not in ("ADMIN", "SUPERADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен.",
        )
    
    try:
        file_path = file_service.get_file_path(file)
    except FileNotFoundServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл отсутствует в хранилище.",
        ) from exc
    
    return FileResponse(
        path=file_path,
        media_type=file.mime_type,
        filename=file.original_name,
        headers={"Cache-Control": "private, max-age=3600"},
    )


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить файл",
)
def delete_file(
    file_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    try:
        file = file_service.get_file(db, file_id)
    except FileNotFoundServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Файл не найден.",
        ) from exc
    
    if file.owner_user_id != user.id and user.role.value not in ("ADMIN", "SUPERADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен.",
        )
    
    file_service.delete_file(db, file)
    
    audit_service.log(
        db=db,
        action="file.delete",
        actor_user_id=user.id,
        entity_type="file",
        entity_id=file_id,
        request=request,
    )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)