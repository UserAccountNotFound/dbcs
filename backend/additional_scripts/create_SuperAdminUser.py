#!/usr/bin/env python3
"""
Интерактивный скрипт для создания учетной записи SUPERADMIN.

Запуск из папки backend:
    .venv/bin/python additional_scripts/create_SuperAdminUser.py

При запуске через curl|bash stdin занят скриптом — ввод идёт с /dev/tty.
Неинтерактивно (CI / автоматизация):
    SUPERADMIN_EMAIL=admin@example.com \\
    SUPERADMIN_FULL_NAME='Admin' \\
    SUPERADMIN_PASSWORD='...' \\
    .venv/bin/python additional_scripts/create_SuperAdminUser.py

Скрипт использует те же функции хеширования (Argon2id) и модели БД,
что и основное приложение, поэтому учетная запись будет полностью совместима.
"""
from __future__ import annotations

import getpass
import os
import sys
from typing import Optional, TextIO

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.security import hash_password, normalize_email
from app.db.session import SessionLocal
from app.models import User
from app.models.enums import UserRole

_TTY_IN: Optional[TextIO] = None


def _open_tty_stdin() -> Optional[TextIO]:
    """Поток для интерактивного ввода (работает при curl|bash)."""
    global _TTY_IN
    if sys.stdin.isatty():
        return sys.stdin
    if _TTY_IN is not None:
        return _TTY_IN
    try:
        _TTY_IN = open("/dev/tty", "r", encoding="utf-8", errors="replace")
        return _TTY_IN
    except OSError:
        return None


def prompt_line(message: str) -> str:
    """Строка с терминала; не использует pipe-stdin установщика."""
    tty = _open_tty_stdin()
    if tty is None:
        raise RuntimeError(
            "Нет TTY для ввода. Задайте SUPERADMIN_EMAIL, SUPERADMIN_FULL_NAME "
            "и SUPERADMIN_PASSWORD в окружении."
        )
    sys.stdout.write(message)
    sys.stdout.flush()
    line = tty.readline()
    if line == "":
        raise EOFError("Ввод прерван (EOF)")
    return line.rstrip("\n\r")


def prompt_password_hidden(message: str) -> str:
    """Пароль без эха; getpass на Unix сам открывает /dev/tty."""
    tty = _open_tty_stdin()
    if tty is None and not sys.stdin.isatty():
        raise RuntimeError(
            "Нет TTY для ввода пароля. Задайте SUPERADMIN_PASSWORD в окружении."
        )
    # stream=None → на Unix getpass читает /dev/tty
    return getpass.getpass(message)


def prompt_email() -> str:
    """Запрашивает email с валидацией."""
    while True:
        email = prompt_line(" Email нового администратора: ").strip()
        if not email:
            print("   Email не может быть пустым.")
            continue
        if "@" not in email or "." not in email.split("@")[-1]:
            print("   Неверный формат email.")
            continue
        return normalize_email(email)


def prompt_full_name() -> str:
    """Запрашивает полное имя."""
    while True:
        name = prompt_line("Полное имя: ").strip()
        if not name:
            print("   Имя не может быть пустым.")
            continue
        return name


def prompt_password() -> str:
    """Запрашивает пароль с подтверждением (без отображения символов)."""
    while True:
        password = prompt_password_hidden(" Пароль (мин. 12 символов): ")
        if len(password) < 12:
            print("   Пароль должен быть не менее 12 символов.")
            continue

        confirm = prompt_password_hidden(" Подтвердите пароль: ")
        if password != confirm:
            print("   Пароли не совпадают.")
            continue

        return password


def credentials_from_env() -> Optional[tuple[str, str, str]]:
    """Неинтерактивный режим через переменные окружения."""
    email = os.environ.get("SUPERADMIN_EMAIL", "").strip()
    full_name = os.environ.get("SUPERADMIN_FULL_NAME", "").strip()
    password = os.environ.get("SUPERADMIN_PASSWORD", "")
    if not email and not full_name and not password:
        return None
    missing = [
        name
        for name, val in (
            ("SUPERADMIN_EMAIL", email),
            ("SUPERADMIN_FULL_NAME", full_name),
            ("SUPERADMIN_PASSWORD", password),
        )
        if not val
    ]
    if missing:
        raise RuntimeError(
            "Для неинтерактивного режима задайте все переменные: "
            + ", ".join(missing)
        )
    if "@" not in email or "." not in email.split("@")[-1]:
        raise RuntimeError("SUPERADMIN_EMAIL: неверный формат email.")
    if len(password) < 12:
        raise RuntimeError("SUPERADMIN_PASSWORD: минимум 12 символов.")
    return normalize_email(email), full_name, password


def create_superuser(email: str, full_name: str, password: str) -> None:
    """Создает пользователя с ролью SUPERADMIN в БД."""
    db = SessionLocal()

    try:
        existing = db.scalar(select(User).where(User.email == email))
        if existing:
            print(f"\nПользователь с email '{email}' уже существует.")
            sys.exit(1)

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


def main() -> None:
    print("\n╔══════════════════════════════════════════╗")
    print("║   Создание учетной записи SUPERADMIN     ║")
    print("╚══════════════════════════════════════════╝\n")

    try:
        from_env = credentials_from_env()
        if from_env:
            email, full_name, password = from_env
            print("Параметры взяты из SUPERADMIN_* окружения.")
        else:
            email = prompt_email()
            full_name = prompt_full_name()
            password = prompt_password()

        print("\n Создание пользователя...")
        create_superuser(email, full_name, password)

    except KeyboardInterrupt:
        print("\n\n Операция отменена пользователем.")
        sys.exit(1)
    except (EOFError, RuntimeError) as e:
        print(f"\n {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n Непредвиденная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
