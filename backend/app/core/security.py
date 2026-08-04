import hashlib
import hmac

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import settings


password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_pii(value: str | None) -> str | None:
    """
    Псевдонимизация/хеширование чувствительных значений:
    IP, User-Agent и т.п.

    Используется HMAC-SHA256 с SECRET_KEY, чтобы значения
    нельзя было просто восстановить rainbow-таблицами.
    """
    if value is None or value == "":
        return None

    return hmac.new(
        settings.secret_key.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()