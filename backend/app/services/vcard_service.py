import re
from typing import Literal

from app.db.base import utcnow
from app.models import Card

MessengerKind = Literal[
    "telegram",
    "whatsapp",
    "viber",
    "wechat",
    "messenger_max",
    "discord",
    "vk",
]

MESSENGER_LABELS: dict[MessengerKind, str] = {
    "telegram": "Telegram",
    "whatsapp": "WhatsApp",
    "viber": "Viber",
    "wechat": "WeChat",
    "messenger_max": "Max",
    "discord": "Discord",
    "vk": "VK",
}


def _escape_vcard_value(value: str | None) -> str:
    if value is None:
        return ""

    value = str(value)

    value = value.replace("\r\n", "\n")
    value = value.replace("\r", "\n")

    value = value.replace("\\", "\\\\")
    value = value.replace("\n", "\\n")
    value = value.replace(",", "\\,")
    value = value.replace(";", "\\;")

    return value


def _strip_at(value: str) -> str:
    return re.sub(r"^@+", "", value).strip()


def _digits_only(value: str) -> str:
    return re.sub(r"\D", "", value)


_ALLOWED_ABSOLUTE_SCHEMES = frozenset(
    {"http", "https", "viber", "tg", "telegram", "whatsapp"}
)


def _as_absolute_url(value: str) -> str | None:
    v = value.strip()
    if not v:
        return None
    if v.startswith("//"):
        return f"https:{v}"
    match = re.match(r"^([a-z][a-z0-9+.-]*):", v, re.I)
    if match:
        scheme = match.group(1).lower()
        if scheme not in _ALLOWED_ABSOLUTE_SCHEMES:
            return None
        return v
    return None


def build_messenger_url(kind: MessengerKind, raw: str) -> str | None:
    """Собирает URL/deep-link для мессенджера (логика как на публичной визитке)."""
    value = raw.strip()
    if not value:
        return None

    existing = _as_absolute_url(value)
    if existing:
        return existing

    if kind == "telegram":
        u = _strip_at(value)
        if u.startswith("t.me/"):
            return f"https://{u}"
        return f"https://t.me/{u}"

    if kind == "whatsapp":
        digits = _digits_only(value)
        return f"https://wa.me/{digits}" if digits else None

    if kind == "viber":
        digits = _digits_only(value)
        if len(digits) >= 7:
            return f"viber://chat?number=%2B{digits}"
        return None

    if kind == "wechat":
        return None

    if kind == "messenger_max":
        u = _strip_at(value)
        if "max.ru" in u:
            return f"https://{re.sub(r'^https?://', '', u, flags=re.I)}"
        return f"https://max.ru/{u}"

    if kind == "discord":
        u = value.strip()
        if "discord.gg" in u or "discord.com" in u:
            if re.match(r"^https?://", u, re.I):
                return u
            if re.match(r"^[a-z][a-z0-9+.-]*:", u, re.I):
                return None
            return f"https://{u}"
        return None

    if kind == "vk":
        u = _strip_at(value)
        if "vk.com" in u or "vk.ru" in u:
            return f"https://{re.sub(r'^https?://', '', u, flags=re.I)}"
        return f"https://vk.com/{u}"

    return None


def _split_full_name(full_name: str) -> tuple[str, str]:
    """
    Возвращает (first_name, last_name).

    Это упрощенная логика для vCard:
    - одно слово: считаем его именем;
    - два слова: первое имя, второе фамилия;
    - больше слов: последнее слово считаем фамилией, остальные именем.
    """
    parts = full_name.strip().split()

    if not parts:
        return "", ""

    if len(parts) == 1:
        return parts[0], ""

    if len(parts) == 2:
        return parts[0], parts[1]

    return " ".join(parts[:-1]), parts[-1]


def _append_labeled_url(lines: list[str], item_index: int, label: str, url: str) -> int:
    """Добавляет URL с подписью (itemN) для iOS и обычный URL для остальных клиентов."""
    escaped_url = _escape_vcard_value(url)
    escaped_label = _escape_vcard_value(label)
    lines.append(f"item{item_index}.URL:{escaped_url}")
    lines.append(f"item{item_index}.X-ABLabel:{escaped_label}")
    lines.append(f"URL:{escaped_url}")
    return item_index + 1


def build_vcard(card: Card) -> str:
    lines: list[str] = []

    lines.append("BEGIN:VCARD")
    lines.append("VERSION:3.0")

    first_name, last_name = _split_full_name(card.full_name)

    lines.append(
        "N:"
        f"{_escape_vcard_value(last_name)};"
        f"{_escape_vcard_value(first_name)};;;"
    )

    lines.append(
        f"FN:{_escape_vcard_value(card.full_name)}"
    )

    if card.job_title:
        lines.append(
            f"TITLE:{_escape_vcard_value(card.job_title)}"
        )

    if card.company and card.department:
        lines.append(
            "ORG:"
            f"{_escape_vcard_value(card.company)};"
            f"{_escape_vcard_value(card.department)}"
        )
    elif card.company:
        lines.append(
            f"ORG:{_escape_vcard_value(card.company)}"
        )
    elif card.department:
        lines.append(
            f"ORG:{_escape_vcard_value(card.department)}"
        )

    item_index = 1

    if card.phone:
        tel = _escape_vcard_value(card.phone)
        lines.append(f"item{item_index}.TEL:{tel}")
        lines.append(f"item{item_index}.X-ABLabel:Мобильный")
        lines.append(f"TEL;TYPE=CELL,VOICE:{tel}")
        item_index += 1

    if card.phone_additional:
        tel = _escape_vcard_value(card.phone_additional)
        lines.append(f"item{item_index}.TEL:{tel}")
        lines.append(f"item{item_index}.X-ABLabel:Доп. телефон")
        lines.append(f"TEL;TYPE=WORK,VOICE:{tel}")
        item_index += 1

    if card.email:
        lines.append(
            f"EMAIL;TYPE=WORK:{_escape_vcard_value(card.email)}"
        )

    if card.website:
        site = card.website.strip()
        if not re.match(r"^https?://", site, re.I):
            if re.match(r"^[a-z][a-z0-9+.-]*:", site, re.I):
                site = ""
            else:
                site = f"https://{site}"
        if site:
            item_index = _append_labeled_url(
                lines,
                item_index,
                "Сайт",
                site,
            )

    messenger_fields: list[tuple[MessengerKind, str | None]] = [
        ("telegram", card.telegram),
        ("whatsapp", card.whatsapp),
        ("viber", card.viber),
        ("wechat", card.wechat),
        ("messenger_max", card.messenger_max),
        ("discord", card.discord),
        ("vk", card.vk),
    ]

    note_extra: list[str] = []

    for kind, raw_value in messenger_fields:
        if not raw_value or not str(raw_value).strip():
            continue
        raw = str(raw_value).strip()
        label = MESSENGER_LABELS[kind]
        url = build_messenger_url(kind, raw)
        if url:
            item_index = _append_labeled_url(lines, item_index, label, url)
        else:
            note_extra.append(f"{label}: {raw}")

    if card.address:
        lines.append(
            f"ADR;TYPE=WORK:;;{_escape_vcard_value(card.address)};;;;"
        )

    note_parts: list[str] = []
    if card.note and str(card.note).strip():
        note_parts.append(str(card.note).strip())
    if note_extra:
        note_parts.extend(note_extra)

    if note_parts:
        lines.append(
            f"NOTE:{_escape_vcard_value('\n'.join(note_parts))}"
        )

    rev = utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines.append(f"REV:{rev}")

    lines.append("END:VCARD")

    return "\r\n".join(lines) + "\r\n"
