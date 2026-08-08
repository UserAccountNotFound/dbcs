from app.db.base import utcnow
from app.models import Card


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

    if card.phone:
        lines.append(
            f"TEL;TYPE=CELL,VOICE:{_escape_vcard_value(card.phone)}"
        )

    if card.email:
        lines.append(
            f"EMAIL;TYPE=WORK:{_escape_vcard_value(card.email)}"
        )

    if card.website:
        lines.append(
            f"URL:{_escape_vcard_value(card.website)}"
        )

    if card.address:
        lines.append(
            f"ADR;TYPE=WORK:;;{_escape_vcard_value(card.address)};;;;"
        )

    if card.note:
        lines.append(
            f"NOTE:{_escape_vcard_value(card.note)}"
        )

    rev = utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines.append(f"REV:{rev}")

    lines.append("END:VCARD")

    return "\r\n".join(lines) + "\r\n"