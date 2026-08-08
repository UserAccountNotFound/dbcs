#!/usr/bin/env python3
"""
Скрипт наполнения БД базовыми шаблонами визиток.

Запуск:
    cd /opt/dbcs/backend
    source .venv/bin/activate
    set -a && source .env && set +a
    python seed_templates.py
"""
import sys

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import CardTemplate


BASE_TEMPLATES = [
    {
        "code": "classic",
        "name": "Классический",
        "description": "Традиционная визитка с фото слева и текстом справа. Подходит для большинства случаев.",
        "schema_json": {
            "primary_color": "#0f766e",
            "secondary_color": "#f3f4f6",
            "text_color": "#111827",
            "heading_font": "inter",
            "body_font": "inter",
            "layout_type": "classic",
            "show_photo": True,
            "show_qr": True,
            "show_logo": False,
            "photo_position": "left",
            "border_radius": 16,
            "shadow": True,
            "gradient_header": False,
        },
    },
    {
        "code": "modern",
        "name": "Современный",
        "description": "Минималистичный дизайн с крупным фото сверху и акцентными цветами.",
        "schema_json": {
            "primary_color": "#2563eb",
            "secondary_color": "#eff6ff",
            "text_color": "#1e293b",
            "heading_font": "roboto",
            "body_font": "roboto",
            "layout_type": "modern",
            "show_photo": True,
            "show_qr": True,
            "show_logo": False,
            "photo_position": "top",
            "border_radius": 24,
            "shadow": True,
            "gradient_header": True,
        },
    },
    {
        "code": "compact",
        "name": "Компактный",
        "description": "Только essential-информация: имя, должность и контакты. Без фото.",
        "schema_json": {
            "primary_color": "#059669",
            "secondary_color": "#ecfdf5",
            "text_color": "#064e3b",
            "heading_font": "open_sans",
            "body_font": "open_sans",
            "layout_type": "compact",
            "show_photo": False,
            "show_qr": True,
            "show_logo": False,
            "photo_position": "left",
            "border_radius": 12,
            "shadow": False,
            "gradient_header": False,
        },
    },
    {
        "code": "corporate",
        "name": "Корпоративный",
        "description": "Строгий деловой стиль с логотипом компании и сдержанными цветами.",
        "schema_json": {
            "primary_color": "#1e3a8a",
            "secondary_color": "#f8fafc",
            "text_color": "#0f172a",
            "heading_font": "inter",
            "body_font": "inter",
            "layout_type": "corporate",
            "show_photo": True,
            "show_qr": False,
            "show_logo": True,
            "photo_position": "right",
            "border_radius": 8,
            "shadow": True,
            "gradient_header": False,
        },
    },
    {
        "code": "creative",
        "name": "Креативный",
        "description": "Яркий дизайн с градиентами и необычной компоновкой для творческих профессий.",
        "schema_json": {
            "primary_color": "#db2777",
            "secondary_color": "#fdf2f8",
            "text_color": "#831843",
            "heading_font": "roboto",
            "body_font": "open_sans",
            "layout_type": "creative",
            "show_photo": True,
            "show_qr": True,
            "show_logo": False,
            "photo_position": "top",
            "border_radius": 32,
            "shadow": True,
            "gradient_header": True,
        },
    },
]


def seed_templates() -> None:
    db = SessionLocal()
    
    try:
        created_count = 0
        skipped_count = 0
        
        for template_data in BASE_TEMPLATES:
            # Проверяем, существует ли уже шаблон с таким code
            existing = db.scalar(
                select(CardTemplate).where(CardTemplate.code == template_data["code"])
            )
            
            if existing:
                print(f"Шаблон '{template_data['code']}' уже существует, пропускаем.")
                skipped_count += 1
                continue
            
            template = CardTemplate(
                code=template_data["code"],
                name=template_data["name"],
                description=template_data["description"],
                schema_json=template_data["schema_json"],
                is_active=True,
            )
            
            db.add(template)
            created_count += 1
            print(f"Создан шаблон: {template_data['name']} ({template_data['code']})")
        
        db.commit()
        
        print("\n" + "=" * 50)
        print(f"Итого: создано {created_count}, пропущено {skipped_count}")
        print("=" * 50)
        
    except Exception as e:
        db.rollback()
        print(f"Ошибка при создании шаблонов: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print("=== Наполнение БД базовыми шаблонами ===\n")
    seed_templates()
    print("\nГотово!")