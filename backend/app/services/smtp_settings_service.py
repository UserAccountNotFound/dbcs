"""Системные SMTP-настройки."""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.db.base import utcnow
from app.models.smtp_settings import SmtpSettings
from app.services.exceptions import ServiceError

GOOGLE_SMTP_DEFAULTS = {
    "host": "smtp.gmail.com",
    "port": 587,
    "use_tls": True,
    "use_ssl": False,
}


class SmtpSettingsError(ServiceError):
    pass


def _validate_enabled_config(row: SmtpSettings) -> None:
    """Ensure required fields are present when SMTP relay is enabled."""
    if not row.enabled:
        return
    if not row.host:
        raise SmtpSettingsError("Укажите SMTP host перед включением.")
    if not row.username:
        raise SmtpSettingsError("Укажите SMTP username перед включением.")
    if not row.password:
        raise SmtpSettingsError("Укажите SMTP password перед включением.")
    if not row.from_email:
        raise SmtpSettingsError("Укажите From email перед включением.")


def get_or_create_settings(db: Session) -> SmtpSettings:
    row = db.get(SmtpSettings, 1)
    if row is not None:
        return row
    row = SmtpSettings(
        id=1,
        enabled=False,
        host=GOOGLE_SMTP_DEFAULTS["host"],
        port=GOOGLE_SMTP_DEFAULTS["port"],
        use_tls=GOOGLE_SMTP_DEFAULTS["use_tls"],
        use_ssl=GOOGLE_SMTP_DEFAULTS["use_ssl"],
        username="",
        password="",
        from_email="",
        from_name="DBCS",
        updated_at=utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_settings(
    db: Session,
    *,
    enabled: bool | None = None,
    host: str | None = None,
    port: int | None = None,
    use_tls: bool | None = None,
    use_ssl: bool | None = None,
    username: str | None = None,
    password: str | None = None,
    from_email: str | None = None,
    from_name: str | None = None,
) -> SmtpSettings:
    row = get_or_create_settings(db)

    if host is not None:
        host = host.strip()
        if not host:
            raise SmtpSettingsError("SMTP host не может быть пустым.")
        if len(host) > 255:
            raise SmtpSettingsError("SMTP host слишком длинный.")
        row.host = host

    if port is not None:
        if not 1 <= port <= 65535:
            raise SmtpSettingsError("SMTP port должен быть от 1 до 65535.")
        row.port = port

    if use_tls is not None:
        row.use_tls = use_tls
    if use_ssl is not None:
        row.use_ssl = use_ssl

    if row.use_ssl and row.use_tls:
        if use_ssl is True:
            row.use_tls = False
        elif use_tls is True:
            row.use_ssl = False

    if username is not None:
        row.username = username.strip()
    if from_email is not None:
        row.from_email = from_email.strip()
    if from_name is not None:
        row.from_name = from_name.strip() or "DBCS"

    if password is not None and password != "":
        row.password = password

    if enabled is not None:
        row.enabled = enabled

    _validate_enabled_config(row)

    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def settings_to_public_dict(row: SmtpSettings) -> dict:
    return {
        "enabled": row.enabled,
        "host": row.host,
        "port": row.port,
        "use_tls": row.use_tls,
        "use_ssl": row.use_ssl,
        "username": row.username,
        "from_email": row.from_email,
        "from_name": row.from_name,
        "password_set": bool(row.password),
        "updated_at": row.updated_at,
    }


def _resolve_connection_params(
    row: SmtpSettings,
    *,
    host: str | None = None,
    port: int | None = None,
    use_tls: bool | None = None,
    use_ssl: bool | None = None,
    username: str | None = None,
    password: str | None = None,
    from_email: str | None = None,
    from_name: str | None = None,
) -> dict:
    resolved_host = (host if host is not None else row.host).strip()
    resolved_port = port if port is not None else row.port
    resolved_tls = use_tls if use_tls is not None else row.use_tls
    resolved_ssl = use_ssl if use_ssl is not None else row.use_ssl
    resolved_user = (username if username is not None else row.username).strip()

    password_provided = password is not None and password != ""
    endpoint_differs = (
        resolved_host.lower() != (row.host or "").strip().lower()
        or int(resolved_port) != int(row.port)
        or bool(resolved_tls) != bool(row.use_tls)
        or bool(resolved_ssl) != bool(row.use_ssl)
    )

    if password_provided:
        resolved_password = password
    elif endpoint_differs:
        raise SmtpSettingsError(
            "При проверке с другим SMTP-сервером (host/port/TLS) укажите пароль явно. "
            "Сохранённый пароль используется только для текущих настроек подключения."
        )
    else:
        resolved_password = row.password

    resolved_from = (from_email if from_email is not None else row.from_email).strip()
    resolved_from_name = (
        (from_name if from_name is not None else row.from_name).strip() or "DBCS"
    )

    if resolved_ssl and resolved_tls:
        resolved_tls = False

    if not resolved_host:
        raise SmtpSettingsError("Укажите SMTP host.")
    if not resolved_user:
        raise SmtpSettingsError("Укажите SMTP username.")
    if not resolved_password:
        raise SmtpSettingsError("Укажите SMTP password (или сохраните его заранее).")
    if not resolved_from:
        raise SmtpSettingsError("Укажите From email.")
    if not 1 <= int(resolved_port) <= 65535:
        raise SmtpSettingsError("SMTP port должен быть от 1 до 65535.")

    return {
        "host": resolved_host,
        "port": int(resolved_port),
        "use_tls": bool(resolved_tls),
        "use_ssl": bool(resolved_ssl),
        "username": resolved_user,
        "password": resolved_password,
        "from_email": resolved_from,
        "from_name": resolved_from_name,
    }


def send_test_email(
    db: Session,
    *,
    to_email: str,
    host: str | None = None,
    port: int | None = None,
    use_tls: bool | None = None,
    use_ssl: bool | None = None,
    username: str | None = None,
    password: str | None = None,
    from_email: str | None = None,
    from_name: str | None = None,
) -> str:
    to_email = (to_email or "").strip()
    if not to_email or "@" not in to_email:
        raise SmtpSettingsError("Укажите корректный адрес получателя.")

    row = get_or_create_settings(db)
    params = _resolve_connection_params(
        row,
        host=host,
        port=port,
        use_tls=use_tls,
        use_ssl=use_ssl,
        username=username,
        password=password,
        from_email=from_email,
        from_name=from_name,
    )

    msg = EmailMessage()
    msg["Subject"] = "DBCS: проверка SMTP"
    msg["From"] = f"{params['from_name']} <{params['from_email']}>"
    msg["To"] = to_email
    msg.set_content(
        "Это тестовое письмо от Digital Business Card Service.\n"
        "Если вы его получили, SMTP-настройки работают.\n"
    )

    context = ssl.create_default_context()
    try:
        if params["use_ssl"]:
            with smtplib.SMTP_SSL(
                params["host"],
                params["port"],
                timeout=30,
                context=context,
            ) as smtp:
                smtp.login(params["username"], params["password"])
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(params["host"], params["port"], timeout=30) as smtp:
                smtp.ehlo()
                if params["use_tls"]:
                    smtp.starttls(context=context)
                    smtp.ehlo()
                smtp.login(params["username"], params["password"])
                smtp.send_message(msg)
    except smtplib.SMTPAuthenticationError as exc:
        raise SmtpSettingsError(
            "Ошибка авторизации SMTP. Проверьте логин/пароль (для Gmail — app password)."
        ) from exc
    except smtplib.SMTPException as exc:
        raise SmtpSettingsError(f"SMTP ошибка: {exc}") from exc
    except OSError as exc:
        raise SmtpSettingsError(f"Не удалось подключиться к SMTP: {exc}") from exc

    return f"Тестовое письмо отправлено на {to_email}."
