"""Экспорт и импорт визиток пользователя (JSON / CSV)."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.schemas.card import CardCreate, CardTheme
from app.models import Card, CardTemplate, User
from app.services import card_service
from app.services.exceptions import (
    CardImportError,
    InvalidFileError,
    SlugGenerationError,
    TemplateNotFoundError,
)

ExportFormat = Literal["json", "csv"]

TRANSFER_VERSION = 1
MAX_IMPORT_CARDS = 200

# Поля переносимого снимка визитки (без id/slug/файлов)
EXPORT_SCALAR_FIELDS = (
    "title",
    "full_name",
    "job_title",
    "department",
    "company",
    "phone",
    "phone_additional",
    "telegram",
    "whatsapp",
    "viber",
    "wechat",
    "messenger_max",
    "discord",
    "vk",
    "email",
    "website",
    "address",
    "note",
    "is_active",
)

CSV_HEADERS = (
    *EXPORT_SCALAR_FIELDS,
    "template_code",
    "theme",
)

TITLE_MAX_LEN = 255


def _export_datetime_stamp(moment: datetime | None = None) -> str:
    """Метка даты/времени выгрузки для суффикса title."""
    moment = moment or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")


def _title_with_import_marker(title: str | None, stamp: str) -> str:
    """Добавляет к названию суффикс _import_<дата_время выгрузки>."""
    base = (title or "").rstrip()
    suffix = f"_import_{stamp}"
    # Не дублируем, если уже есть такой же суффикс выгрузки
    if base.endswith(suffix):
        return base[:TITLE_MAX_LEN]
    combined = f"{base}{suffix}"
    if len(combined) <= TITLE_MAX_LEN:
        return combined
    # Обрезаем исходное название, чтобы суффикс всегда поместился
    keep = TITLE_MAX_LEN - len(suffix)
    if keep < 1:
        return suffix[:TITLE_MAX_LEN]
    return f"{base[:keep]}{suffix}"


def _card_to_export_dict(card: Card, export_stamp: str) -> dict[str, Any]:
    theme = card.theme if isinstance(card.theme, dict) else {}
    try:
        theme = CardTheme.model_validate(theme).model_dump()
    except Exception:
        theme = CardTheme().model_dump()

    item: dict[str, Any] = {
        field: getattr(card, field) for field in EXPORT_SCALAR_FIELDS
    }
    item["title"] = _title_with_import_marker(card.title, export_stamp)
    item["template_code"] = card.template.code if card.template else None
    item["theme"] = theme
    return item


def list_user_cards_for_export(db: Session, user: User) -> list[Card]:
    return list(
        db.scalars(
            select(Card)
            .options(joinedload(Card.template))
            .where(
                Card.user_id == user.id,
                Card.deleted_at.is_(None),
            )
            .order_by(Card.created_at.asc(), Card.id.asc())
        ).unique().all()
    )


def build_export_payload(cards: list[Card], export_at: datetime | None = None) -> dict[str, Any]:
    moment = export_at or datetime.now(timezone.utc)
    stamp = _export_datetime_stamp(moment)
    return {
        "version": TRANSFER_VERSION,
        "exported_at": moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cards": [_card_to_export_dict(card, stamp) for card in cards],
    }


def export_cards_json(db: Session, user: User) -> str:
    payload = build_export_payload(list_user_cards_for_export(db, user))
    return json.dumps(payload, ensure_ascii=False, indent=2)


def export_cards_csv(db: Session, user: User) -> str:
    cards = list_user_cards_for_export(db, user)
    stamp = _export_datetime_stamp()
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_HEADERS, extrasaction="ignore")
    writer.writeheader()
    for card in cards:
        row = _card_to_export_dict(card, stamp)
        theme = row.pop("theme")
        row["theme"] = json.dumps(theme, ensure_ascii=False)
        # CSV: bool → true/false
        if row.get("is_active") is not None:
            row["is_active"] = "true" if row["is_active"] else "false"
        writer.writerow(row)
    return buffer.getvalue()


def _resolve_template_id(db: Session, template_code: str | None) -> str | None:
    if not template_code:
        return None
    code = template_code.strip()
    if not code:
        return None
    template = db.scalar(
        select(CardTemplate).where(
            CardTemplate.code == code,
            CardTemplate.is_active.is_(True),
        )
    )
    if template is None:
        raise TemplateNotFoundError(f"Template not found: {code}")
    return template.id


def _parse_bool(value: Any, default: bool = True) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "да"}:
        return True
    if text in {"0", "false", "no", "n", "нет"}:
        return False
    return default


def _normalize_import_item(raw: dict[str, Any]) -> dict[str, Any]:
    data = dict(raw)

    theme_raw = data.pop("theme", None)
    if isinstance(theme_raw, str) and theme_raw.strip():
        try:
            theme_raw = json.loads(theme_raw)
        except json.JSONDecodeError as exc:
            raise CardImportError("Invalid theme JSON.") from exc
    if theme_raw is None or theme_raw == "":
        theme_raw = {}
    if not isinstance(theme_raw, dict):
        raise CardImportError("theme must be an object or JSON object string.")

    data["theme"] = theme_raw
    data.pop("template_id", None)
    data.pop("avatar_file_id", None)
    data.pop("logo_file_id", None)
    data.pop("id", None)
    data.pop("slug", None)
    data.pop("public_url", None)

    if "is_active" in data:
        data["is_active"] = _parse_bool(data.get("is_active"), default=True)

    # Пустые строки → None для опциональных полей
    for key, value in list(data.items()):
        if value == "":
            data[key] = None

    return data


def _cards_from_json(content: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise CardImportError("Invalid JSON file.") from exc

    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = payload.get("cards")
        if items is None:
            raise CardImportError("JSON must contain a 'cards' array.")
    else:
        raise CardImportError("Unsupported JSON structure.")

    if not isinstance(items, list):
        raise CardImportError("'cards' must be an array.")

    if len(items) > MAX_IMPORT_CARDS:
        raise CardImportError(f"Too many cards (max {MAX_IMPORT_CARDS}).")

    result: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise CardImportError(f"Card #{index} must be an object.")
        result.append(item)
    return result


def _cards_from_csv(content: str) -> list[dict[str, Any]]:
    # Убираем BOM
    if content.startswith("\ufeff"):
        content = content.lstrip("\ufeff")

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise CardImportError("CSV has no header row.")

    rows = list(reader)
    if len(rows) > MAX_IMPORT_CARDS:
        raise CardImportError(f"Too many cards (max {MAX_IMPORT_CARDS}).")

    return [dict(row) for row in rows]


def import_cards(
    db: Session,
    user: User,
    content: str,
    fmt: ExportFormat,
) -> dict[str, Any]:
    """
    Импортирует визитки текущего пользователя.
    Возвращает сводку: created, failed, errors[].
    """
    if fmt == "json":
        raw_items = _cards_from_json(content)
    else:
        raw_items = _cards_from_csv(content)

    created = 0
    failed = 0
    errors: list[dict[str, Any]] = []

    for index, raw in enumerate(raw_items, start=1):
        try:
            normalized = _normalize_import_item(raw)
            template_code = normalized.pop("template_code", None)
            if isinstance(template_code, str):
                template_code = template_code.strip() or None
            else:
                template_code = None

            is_active = _parse_bool(normalized.pop("is_active", True), default=True)

            try:
                template_id = _resolve_template_id(db, template_code)
            except TemplateNotFoundError:
                # Неизвестный шаблон — создаём без шаблона
                template_id = None

            payload = CardCreate.model_validate(
                {
                    **normalized,
                    "template_id": template_id,
                    "avatar_file_id": None,
                    "logo_file_id": None,
                }
            )

            card = card_service.create_card(db=db, user=user, payload=payload)
            if not is_active:
                card.is_active = False
                db.add(card)
                db.commit()
            created += 1
        except (ValidationError, CardImportError, InvalidFileError, SlugGenerationError) as exc:
            failed += 1
            message = str(exc)
            if isinstance(exc, ValidationError):
                message = "; ".join(
                    f"{'.'.join(str(p) for p in err.get('loc', ()))}: {err.get('msg')}"
                    for err in exc.errors()
                )
            errors.append({"index": index, "error": message})
        except Exception as exc:  # noqa: BLE001 — собираем сводку по строкам
            failed += 1
            errors.append({"index": index, "error": str(exc)})

    return {
        "created": created,
        "failed": failed,
        "errors": errors[:50],
    }
