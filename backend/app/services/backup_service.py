"""Резервное копирование БД и uploads."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import utcnow
from app.models.backup_settings import BackupSettings
from app.services.exceptions import ServiceError

BACKUP_FILENAME_RE = re.compile(r"^dbcs_backup_\d{8}_\d{6}\.tar\.gz$")
SCHEDULE_CHOICES = ("off", "hourly", "daily", "weekly")
ALLOWED_STORAGE_PREFIXES = (
    Path("/var/lib/dbcs"),
    Path("/opt/dbcs/backups"),
)


class BackupError(ServiceError):
    pass


@dataclass(frozen=True)
class DbConn:
    user: str
    password: str
    host: str
    port: int
    database: str


@dataclass
class BackupFileInfo:
    filename: str
    size_bytes: int
    created_at: datetime


def _parse_database_url(url: str) -> DbConn:
    parsed = urlparse(url)
    if parsed.scheme not in ("mysql", "mysql+pymysql", "mariadb", "mariadb+pymysql"):
        raise BackupError("Неподдерживаемый DATABASE_URL для резервного копирования.")
    if not parsed.username or not parsed.path or parsed.path == "/":
        raise BackupError("DATABASE_URL не содержит пользователя или имя БД.")
    return DbConn(
        user=unquote(parsed.username),
        password=unquote(parsed.password or ""),
        host=parsed.hostname or "127.0.0.1",
        port=parsed.port or 3306,
        database=unquote(parsed.path.lstrip("/").split("?")[0]),
    )


def validate_storage_path(raw: str) -> Path:
    text = (raw or "").strip()
    if not text:
        raise BackupError("Путь хранения не задан.")
    path = Path(text).expanduser()
    if not path.is_absolute():
        raise BackupError("Путь хранения должен быть абсолютным.")
    resolved = path.resolve()
    if any(part == ".." for part in path.parts):
        raise BackupError("Путь хранения содержит недопустимые сегменты.")
    if not any(
        resolved == prefix or prefix in resolved.parents
        for prefix in (p.resolve() for p in ALLOWED_STORAGE_PREFIXES)
    ):
        allowed = ", ".join(str(p) for p in ALLOWED_STORAGE_PREFIXES)
        raise BackupError(f"Путь хранения должен находиться внутри: {allowed}.")
    return resolved


def ensure_backup_settings_schema(db: Session) -> None:
    """Создаёт таблицу backup_settings вне текущей транзакции (иначе MariaDB 1412)."""
    from sqlalchemy import inspect

    bind = db.get_bind()
    try:
        if inspect(bind).has_table(BackupSettings.__tablename__):
            return
    except Exception:  # noqa: BLE001
        pass

    # DDL только если таблицы нет — в AUTOCOMMIT, чтобы не ломать session transaction.
    with bind.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        BackupSettings.__table__.create(conn, checkfirst=True)


def get_or_create_settings(db: Session) -> BackupSettings:
    try:
        settings = db.get(BackupSettings, 1)
    except Exception:  # noqa: BLE001
        db.rollback()
        ensure_backup_settings_schema(db)
        settings = db.get(BackupSettings, 1)

    if settings is None:
        # Таблицы могло не быть до ensure — повторяем после DDL.
        ensure_backup_settings_schema(db)
        settings = db.get(BackupSettings, 1)

    if settings is not None:
        return settings

    defaults = get_settings()
    settings = BackupSettings(
        id=1,
        storage_path=str(defaults.backup_dir_default),
        schedule="daily",
        schedule_hour=3,
        schedule_weekday=0,
        retention_count=7,
        enabled=True,
        updated_at=utcnow(),
    )
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def update_settings(
    db: Session,
    *,
    storage_path: str | None = None,
    schedule: str | None = None,
    schedule_hour: int | None = None,
    schedule_weekday: int | None = None,
    retention_count: int | None = None,
    enabled: bool | None = None,
) -> BackupSettings:
    row = get_or_create_settings(db)

    if storage_path is not None:
        path = validate_storage_path(storage_path)
        path.mkdir(parents=True, exist_ok=True)
        row.storage_path = str(path)

    if schedule is not None:
        if schedule not in SCHEDULE_CHOICES:
            raise BackupError("Недопустимое значение периодичности.")
        row.schedule = schedule
        row.enabled = schedule != "off"

    if schedule_hour is not None:
        if not 0 <= schedule_hour <= 23:
            raise BackupError("Час расписания должен быть от 0 до 23.")
        row.schedule_hour = schedule_hour

    if schedule_weekday is not None:
        if not 0 <= schedule_weekday <= 6:
            raise BackupError("День недели должен быть от 0 (пн) до 6 (вс).")
        row.schedule_weekday = schedule_weekday

    if retention_count is not None:
        if not 1 <= retention_count <= 100:
            raise BackupError("Число хранимых копий должно быть от 1 до 100.")
        row.retention_count = retention_count

    if enabled is not None:
        row.enabled = enabled
        if not enabled:
            row.schedule = "off"
        elif row.schedule == "off":
            row.schedule = "daily"

    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def _mark_status(
    db: Session,
    row: BackupSettings,
    *,
    status: str,
    message: str,
    backup_file: str | None = None,
) -> None:
    row.last_run_at = utcnow()
    row.last_status = status
    row.last_message = message[:2000]
    if backup_file is not None:
        row.last_backup_file = backup_file
    row.updated_at = utcnow()
    db.commit()


def _mysqldump(conn: DbConn, out_file: Path) -> None:
    env = {**os.environ, "MYSQL_PWD": conn.password}
    cmd = [
        "mysqldump",
        "-h",
        conn.host,
        "-P",
        str(conn.port),
        "-u",
        conn.user,
        "--single-transaction",
        "--routines",
        "--triggers",
        "--default-character-set=utf8mb4",
        "--result-file",
        str(out_file),
        conn.database,
    ]
    try:
        proc = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
    except FileNotFoundError as exc:
        raise BackupError("mysqldump не найден. Установите mariadb-client.") from exc
    except subprocess.TimeoutExpired as exc:
        raise BackupError("mysqldump превысил лимит времени.") from exc
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "unknown error").strip()
        raise BackupError(f"mysqldump завершился с ошибкой: {err[:500]}")
    if not out_file.exists() or out_file.stat().st_size == 0:
        raise BackupError("mysqldump создал пустой файл.")


def _mysql_restore(conn: DbConn, sql_file: Path) -> None:
    env = {**os.environ, "MYSQL_PWD": conn.password}
    cmd = [
        "mysql",
        "-h",
        conn.host,
        "-P",
        str(conn.port),
        "-u",
        conn.user,
        "--default-character-set=utf8mb4",
        "--force",
        conn.database,
    ]
    try:
        with sql_file.open("rb") as fh:
            proc = subprocess.run(
                cmd,
                env=env,
                stdin=fh,
                capture_output=True,
                text=True,
                timeout=1800,
                check=False,
            )
    except FileNotFoundError as exc:
        raise BackupError("mysql-клиент не найден. Установите mariadb-client.") from exc
    except subprocess.TimeoutExpired as exc:
        raise BackupError("Восстановление БД превысило лимит времени.") from exc
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "unknown error").strip()
        raise BackupError(f"mysql restore завершился с ошибкой: {err[:500]}")


def _terminate_other_db_sessions(conn: DbConn) -> None:
    """Снимает metadata locks: закрывает чужие сессии того же DB-пользователя."""
    try:
        import pymysql
    except ImportError:
        return

    try:
        link = pymysql.connect(
            host=conn.host,
            port=conn.port,
            user=conn.user,
            password=conn.password,
            database=conn.database,
            charset="utf8mb4",
            connect_timeout=10,
            read_timeout=30,
            write_timeout=30,
            autocommit=True,
        )
    except Exception:  # noqa: BLE001
        return

    try:
        with link.cursor() as cur:
            cur.execute("SET SESSION lock_wait_timeout=15")
            cur.execute(
                """
                SELECT id
                FROM information_schema.processlist
                WHERE db = %s
                  AND user = %s
                  AND id <> CONNECTION_ID()
                """,
                (conn.database, conn.user),
            )
            pids = [int(row[0]) for row in cur.fetchall()]
            for pid in pids:
                try:
                    cur.execute(f"KILL {pid}")
                except Exception:  # noqa: BLE001
                    pass
    finally:
        try:
            link.close()
        except Exception:  # noqa: BLE001
            pass


def _apply_retention(storage: Path, keep: int) -> None:
    files = sorted(
        (p for p in storage.iterdir() if p.is_file() and BACKUP_FILENAME_RE.match(p.name)),
        key=lambda p: p.name,
        reverse=True,
    )
    for old in files[keep:]:
        try:
            old.unlink()
        except OSError:
            pass


def list_backups(db: Session) -> list[BackupFileInfo]:
    row = get_or_create_settings(db)
    storage = validate_storage_path(row.storage_path)
    if not storage.exists():
        return []
    items: list[BackupFileInfo] = []
    for path in storage.iterdir():
        if not path.is_file() or not BACKUP_FILENAME_RE.match(path.name):
            continue
        stat = path.stat()
        items.append(
            BackupFileInfo(
                filename=path.name,
                size_bytes=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).replace(
                    tzinfo=None
                ),
            )
        )
    items.sort(key=lambda x: x.filename, reverse=True)
    return items


def create_backup(db: Session) -> BackupFileInfo:
    row = get_or_create_settings(db)
    settings = get_settings()
    storage = validate_storage_path(row.storage_path)
    storage.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"dbcs_backup_{stamp}.tar.gz"
    archive_path = storage / filename
    conn = _parse_database_url(settings.database_url)
    uploads_dir = Path(settings.uploads_dir)

    try:
        with tempfile.TemporaryDirectory(prefix="dbcs-backup-") as tmp:
            tmp_path = Path(tmp)
            sql_path = tmp_path / "database.sql"
            meta_path = tmp_path / "meta.json"
            _mysqldump(conn, sql_path)
            meta = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "app_version": settings.app_version,
                "database": conn.database,
                "includes_uploads": uploads_dir.is_dir(),
            }
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(sql_path, arcname="database.sql")
                tar.add(meta_path, arcname="meta.json")
                if uploads_dir.is_dir():
                    tar.add(uploads_dir, arcname="uploads")

        _apply_retention(storage, row.retention_count)
        info = BackupFileInfo(
            filename=filename,
            size_bytes=archive_path.stat().st_size,
            created_at=utcnow(),
        )
        _mark_status(
            db,
            row,
            status="success",
            message=f"Создан архив {filename}",
            backup_file=filename,
        )
        return info
    except BackupError as exc:
        if archive_path.exists():
            archive_path.unlink(missing_ok=True)
        _mark_status(db, row, status="error", message=str(exc))
        raise
    except Exception as exc:  # noqa: BLE001
        if archive_path.exists():
            archive_path.unlink(missing_ok=True)
        _mark_status(db, row, status="error", message=str(exc))
        raise BackupError(f"Ошибка резервного копирования: {exc}") from exc


def _run_alembic_upgrade() -> None:
    """Доводит схему БД до текущих миграций приложения (после restore из старого дампа)."""
    backend_root = Path(__file__).resolve().parents[2]
    alembic_bin = backend_root / ".venv" / "bin" / "alembic"
    cmd = [str(alembic_bin) if alembic_bin.is_file() else "alembic", "upgrade", "head"]
    env = {**os.environ, "PYTHONPATH": str(backend_root)}
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(backend_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except FileNotFoundError as exc:
        raise BackupError("alembic не найден — не удалось обновить схему после restore.") from exc
    except subprocess.TimeoutExpired as exc:
        raise BackupError("alembic upgrade превысил лимит времени.") from exc
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "unknown error").strip()
        raise BackupError(f"alembic upgrade завершился с ошибкой: {err[:500]}")


def restore_backup(db: Session, filename: str) -> str:
    name = Path(filename).name
    if not BACKUP_FILENAME_RE.match(name):
        raise BackupError("Некорректное имя файла резервной копии.")

    row = get_or_create_settings(db)
    settings = get_settings()
    storage = validate_storage_path(row.storage_path)
    archive_path = (storage / name).resolve()
    if not str(archive_path).startswith(str(storage.resolve())):
        raise BackupError("Файл вне каталога хранения.")
    if not archive_path.is_file():
        raise BackupError("Файл резервной копии не найден.")

    conn = _parse_database_url(settings.database_url)
    uploads_dir = Path(settings.uploads_dir)

    # Освобождаем connection запроса до DROP/restore, иначе зависание на metadata lock.
    try:
        db.rollback()
        db.connection().invalidate()
    except Exception:  # noqa: BLE001
        pass

    try:
        with tempfile.TemporaryDirectory(prefix="dbcs-restore-") as tmp:
            tmp_path = Path(tmp)
            with tarfile.open(archive_path, "r:gz") as tar:
                for member in tar.getmembers():
                    member_path = Path(member.name)
                    if member_path.is_absolute() or ".." in member_path.parts:
                        raise BackupError("Архив содержит небезопасные пути.")
                extract_kwargs: dict = {}
                if hasattr(tarfile, "data_filter"):
                    extract_kwargs["filter"] = "data"
                tar.extractall(tmp_path, **extract_kwargs)

            sql_path = tmp_path / "database.sql"
            if not sql_path.is_file():
                raise BackupError("В архиве нет database.sql.")

            _terminate_other_db_sessions(conn)
            _mysql_restore(conn, sql_path)

            extracted_uploads = tmp_path / "uploads"
            if extracted_uploads.is_dir():
                uploads_dir.mkdir(parents=True, exist_ok=True)
                for child in list(uploads_dir.iterdir()):
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink(missing_ok=True)
                for child in extracted_uploads.iterdir():
                    dest = uploads_dir / child.name
                    if child.is_dir():
                        shutil.copytree(child, dest)
                    else:
                        shutil.copy2(child, dest)

        _run_alembic_upgrade()

        from app.db.session import SessionLocal
        from sqlalchemy import text

        fresh = SessionLocal()
        try:
            # Старые refresh-сессии из дампа / текущей сессии больше недействительны.
            try:
                fresh.execute(text("DELETE FROM auth_sessions"))
                fresh.commit()
            except Exception:  # noqa: BLE001
                fresh.rollback()

            row = get_or_create_settings(fresh)
            message = (
                f"Восстановлено из {name}. "
                "Все сессии сброшены — выполните вход заново."
            )
            _mark_status(fresh, row, status="restored", message=message, backup_file=name)
            return message
        finally:
            fresh.close()
    except BackupError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise BackupError(f"Ошибка восстановления: {exc}") from exc


def is_backup_due(row: BackupSettings, now: datetime | None = None) -> bool:
    if not row.enabled or row.schedule == "off":
        return False

    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    last = row.last_run_at

    if row.schedule == "hourly":
        if last is None:
            return True
        return (now - last) >= timedelta(minutes=55)

    if row.schedule == "daily":
        if now.hour != row.schedule_hour:
            return False
        if last is None:
            return True
        return last.date() < now.date()

    if row.schedule == "weekly":
        # ISO: Monday=0 … Sunday=6 — совпадает с schedule_weekday
        if now.weekday() != row.schedule_weekday:
            return False
        if now.hour != row.schedule_hour:
            return False
        if last is None:
            return True
        return (now - last) >= timedelta(days=6)

    return False


def run_scheduled_if_due(db: Session) -> BackupFileInfo | None:
    row = get_or_create_settings(db)
    if not is_backup_due(row):
        return None
    return create_backup(db)
