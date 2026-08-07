import hashlib
import uuid
from pathlib import Path

import magic
from fastapi import UploadFile
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import File
from app.services.exceptions import (
    FileTooLargeError,
    UnsupportedFileTypeError,
    InvalidFileError,
    FileNotFoundError as FileNotFoundServiceError,
)

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

MAX_IMAGE_DIMENSION = 4096


def _sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Недопустимое расширение. Разрешены: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return ext


def _validate_mime(data: bytes, expected_ext: str) -> str:
    detected_mime = magic.from_buffer(data, mime=True)
    
    if detected_mime not in ALLOWED_MIME_TYPES:
        raise UnsupportedFileTypeError(
            f"Недопустимый MIME-тип: {detected_mime}. Разрешены только изображения."
        )
    
    # Проверяем соответствие MIME и расширения
    mime_to_ext = {
        "image/jpeg": {".jpg", ".jpeg"},
        "image/png": {".png"},
        "image/webp": {".webp"},
    }
    
    if expected_ext not in mime_to_ext.get(detected_mime, set()):
        raise InvalidFileError(
            "Расширение файла не соответствует его содержимому."
        )
    
    return detected_mime


def _validate_image_dimensions(data: bytes) -> None:
    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()  # Проверяем целостность
            
            # Повторно открываем для получения размеров
            with Image.open(io.BytesIO(data)) as img2:
                width, height = img2.size
                
                if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                    raise InvalidFileError(
                        f"Размеры изображения превышают {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION}"
                    )
    except Image.UnidentifiedImageError:
        raise InvalidFileError("Файл поврежден или не является изображением.")
    except Exception as e:
        if isinstance(e, InvalidFileError):
            raise
        raise InvalidFileError(f"Ошибка валидации изображения: {str(e)}")


import io


def upload_file(
    db: Session,
    user_id: str,
    file: UploadFile,
) -> File:
    # 1. Читаем содержимое
    data = file.file.read()
    file.file.seek(0)  # Возвращаем указатель для повторного чтения
    
    # 2. Проверка размера
    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(data) > max_size_bytes:
        raise FileTooLargeError(
            f"Размер файла превышает {settings.max_upload_size_mb} МБ"
        )
    
    if len(data) == 0:
        raise InvalidFileError("Файл пуст.")
    
    # 3. Проверка расширения
    original_name = file.filename or "unnamed.jpg"
    ext = _validate_extension(original_name)
    
    # 4. Проверка MIME-типа
    detected_mime = _validate_mime(data, ext)
    
    # 5. Проверка размеров изображения
    _validate_image_dimensions(data)
    
    # 6. Вычисляем хеш
    file_hash = _sha256_of_bytes(data)
    
    # 7. Проверяем, нет ли уже такого файла (дедупликация)
    existing = db.scalar(select(File).where(File.sha256 == file_hash))
    if existing:
        return existing
    
    # 8. Генерируем уникальное имя
    storage_key = f"{uuid.uuid4()}{ext}"
    storage_path = settings.uploads_dir / storage_key
    
    # 9. Создаем директории, если их нет
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    
    # 10. Сохраняем файл
    with open(storage_path, "wb") as f:
        f.write(data)
    
    # 11. Создаем запись в БД
    file_record = File(
        owner_user_id=user_id,
        storage_key=storage_key,
        original_name=original_name[:512],
        mime_type=detected_mime,
        size_bytes=len(data),
        sha256=file_hash,
    )
    
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    
    return file_record


def get_file(db: Session, file_id: str) -> File:
    file = db.get(File, file_id)
    if not file:
        raise FileNotFoundServiceError("Файл не найден.")
    return file


def get_file_path(file: File) -> Path:
    path = settings.uploads_dir / file.storage_key
    if not path.exists():
        raise FileNotFoundServiceError("Файл отсутствует в хранилище.")
    return path


def delete_file(db: Session, file: File) -> None:
    # Удаляем физический файл
    path = settings.uploads_dir / file.storage_key
    if path.exists():
        path.unlink()
    
    # Удаляем запись из БД
    db.delete(file)
    db.commit()
    