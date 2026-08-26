#!/usr/bin/env python3
"""
Наполнение БД метаданными шаблонов (CSS лежит в templates/css/{code}.css).

Неинтерактивный скрипт — безопасен при запуске из install.sh / curl|bash
(stdin не используется).

Запуск:
    cd /opt/dbcs/backend
    set -a && source .env && set +a
    .venv/bin/python additional_scripts/seed_templates_vCard.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# При запуске как additional_scripts/*.py в sys.path попадает эта папка, не backend/
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import CardTemplate
from app.services import css_template_service


BASE_TEMPLATES = [
    {
        "code": "classic",
        "name": "Vanilla",
        "description": "Светлый минималистичный профиль. CSS: classic.css",
        "schema_json": {
            "version": 2,
            "default_accent": "#0f766e",
            "default_scheme": "light",
        },
    },
    {
        "code": "modern",
        "name": "Galaxy",
        "description": "Тёмный космический профиль. CSS: modern.css",
        "schema_json": {
            "version": 2,
            "default_accent": "#a78bfa",
            "default_scheme": "dark",
        },
    },
    {
        "code": "compact",
        "name": "Mono",
        "description": "Терминальный минимализм. CSS: compact.css",
        "schema_json": {
            "version": 2,
            "default_accent": "#22c55e",
            "default_scheme": "dark",
        },
    },
    {
        "code": "corporate",
        "name": "Flare",
        "description": "Тёплый светлый профиль. CSS: corporate.css",
        "schema_json": {
            "version": 2,
            "default_accent": "#ea580c",
            "default_scheme": "light",
        },
    },
    {
        "code": "creative",
        "name": "Aurora",
        "description": "Polygon-стиль: сеть частиц и ghost-кнопки. CSS: creative.css",
        "schema_json": {
            "version": 2,
            "effect": "polygon",
            "default_accent": "#ffffff",
            "default_scheme": "dark",
        },
    },
]


def seed_templates() -> None:
    if not os.environ.get("DATABASE_URL", "").strip():
        print(
            "Ошибка: DATABASE_URL не задан. "
            "Загрузите .env (set -a && source .env && set +a) перед запуском."
        )
        sys.exit(1)

    db = SessionLocal()

    try:
        created_count = 0
        updated_count = 0
        missing_css: list[str] = []

        for template_data in BASE_TEMPLATES:
            code = template_data["code"]
            if not css_template_service.template_css_exists(code):
                missing_css.append(code)

            existing = db.scalar(
                select(CardTemplate).where(CardTemplate.code == code)
            )

            if existing:
                existing.name = template_data["name"]
                existing.description = template_data["description"]
                existing.schema_json = template_data["schema_json"]
                existing.is_active = True
                updated_count += 1
                print(f"Обновлён шаблон: {template_data['name']} ({code})")
                continue

            template = CardTemplate(
                code=code,
                name=template_data["name"],
                description=template_data["description"],
                schema_json=template_data["schema_json"],
                is_active=True,
            )
            db.add(template)
            created_count += 1
            print(f"Создан шаблон: {template_data['name']} ({code})")

        db.commit()

        print("\n" + "=" * 50)
        print(f"Итого: создано {created_count}, обновлено {updated_count}")
        if missing_css:
            print(f"ВНИМАНИЕ: нет CSS на диске для: {', '.join(missing_css)}")
        else:
            print("Все CSS-файлы на месте.")
        print("=" * 50)

    except Exception as e:
        db.rollback()
        print(f"Ошибка при создании шаблонов: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print("=== Наполнение БД метаданными CSS-шаблонов ===\n")
    seed_templates()
    print("\nГотово!")
