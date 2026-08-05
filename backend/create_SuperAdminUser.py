#!/usr/bin/env python3
"""
Интерактивный скрипт для создания учетной записи SUPERADMIN.

Запуск из папки backend:
    python create_superuser.py

Скрипт использует те же функции хеширования (Argon2id) и модели БД,
что и основное приложение, поэтому учетная запись будет полностью совместима.
"""
import getpass
import sys

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.security import hash_password, normalize_email
from app.db.session import SessionLocal
from app.models import User
from app.models.enums import UserRole


def prompt_email() -> str:
    """Запрашивает email с валидацией."""
    while True:
        email = input("📧 Email нового администратора: ").strip()
        if not email:
            print("   ❌ Email не может быть пустым.")
            continue
        if "@" not in email or "." not in email.split("@")[-1]:
            print("   ❌ Неверный формат email.")
            continue
        return normalize_email(email)


def prompt_full_name() -> str:
    """Запрашивает полное имя."""
    while True:
        name = input("👤 Полное имя: ").strip()
        if not name:
            print("   ❌ Имя не может быть пустым.")
            continue
        return name


def prompt_password() -> str:
    """Запрашивает пароль с подтверждением (без отображения символов)."""
    while True:
        password = getpass.getpass("🔑 Пароль (мин. 12 символов): ")
        if len(password) < 12:
            print("   ❌ Пароль должен быть не менее 12 символов.")
            continue
        
        confirm = getpass.getpass("🔑 Подтвердите пароль: ")
        if password != confirm:
            print("   ❌ Пароли не совпадают.")
            continue
        
        return password


def create_superuser(email: str, full_name: str, password: str) -> None:
    """Создает пользователя с ролью SUPERADMIN в БД."""
    db = SessionLocal()
    
    try:
        # Проверяем, существует ли уже пользователь
        existing = db.scalar(select(User).where(User.email == email))
        if existing:
            print(f"\nПользователь с email '{email}' уже существует.")
            sys.exit(1)
        
        # Создаем пользователя
        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=UserRole.SUPERADMIN,
            is_active=True,
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print("\n" + "=" * 50)
        print("Учетная запись SUPERADMIN успешно создана!")
        print("=" * 50)
        print(f"   ID:    {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Имя:   {user.full_name}")
        print(f"   Роль:  {user.role.value}")
        print("=" * 50)
        print("\nТеперь вы можете войти в систему и открыть админ-панель.")
        
    except SQLAlchemyError as e:
        db.rollback()
        print(f"\n Ошибка базы данных: {e}")
        print("   Убедитесь, что миграции применены: alembic upgrade head")
        sys.exit(1)
    finally:
        db.close()


def main():
    print("\n╔══════════════════════════════════════════╗")
    print("║   Создание учетной записи SUPERADMIN     ║")
    print("╚══════════════════════════════════════════╝\n")
    
    try:
        email = prompt_email()
        full_name = prompt_full_name()
        password = prompt_password()
        
        print("\n Создание пользователя...")
        create_superuser(email, full_name, password)
        
    except KeyboardInterrupt:
        print("\n\n Операция отменена пользователем.")
        sys.exit(1)
    except Exception as e:
        print(f"\n Непредвиденная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()