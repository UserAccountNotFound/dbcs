"""Работа с CSS-файлами шаблонов на диске."""

from __future__ import annotations

import re
from pathlib import Path

from app.core.config import settings
from app.services.exceptions import TemplateError

# Опасные конструкции в CSS (базовая защита)
_FORBIDDEN_CSS = re.compile(
    r"(@import\b|expression\s*\(|-moz-binding\b|behavior\s*:)",
    re.IGNORECASE,
)

_CODE_RE = re.compile(r"^[a-z0-9_-]+$")

MAX_CSS_BYTES = 256 * 1024  # 256 KB


def templates_css_dir() -> Path:
    path = Path(settings.templates_css_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def css_path_for_code(code: str) -> Path:
    if not _CODE_RE.fullmatch(code):
        raise TemplateError("Некорректный код шаблона.")

    root = templates_css_dir()
    path = (root / f"{code}.css").resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise TemplateError("Некорректный путь к CSS шаблона.") from exc
    return path


def css_url_for_code(code: str) -> str:
    return f"{settings.api_v1_prefix}/templates/{code}/css"


def validate_css_content(css: str) -> str:
    if not css or not css.strip():
        raise TemplateError("CSS шаблона пуст.")
    if len(css.encode("utf-8")) > MAX_CSS_BYTES:
        raise TemplateError("CSS шаблона слишком большой.")
    if _FORBIDDEN_CSS.search(css):
        raise TemplateError(
            "CSS содержит запрещённые конструкции (@import, expression, behavior)."
        )
    return css


def read_template_css(code: str) -> str:
    path = css_path_for_code(code)
    if not path.is_file():
        raise TemplateError("CSS-файл шаблона не найден.")
    try:
        css = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TemplateError("Не удалось прочитать CSS шаблона.") from exc
    return validate_css_content(css)


def write_template_css(code: str, css: str) -> Path:
    css = validate_css_content(css)
    path = css_path_for_code(code)
    try:
        path.write_text(css, encoding="utf-8")
    except OSError as exc:
        raise TemplateError("Не удалось сохранить CSS шаблона.") from exc
    return path


def template_css_exists(code: str) -> bool:
    try:
        return css_path_for_code(code).is_file()
    except TemplateError:
        return False
