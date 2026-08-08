from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, normalize_email
from app.models import User, UserRole
from app.services.exceptions import EmailAlreadyExistsError


def get_by_email(db: Session, email: str) -> User | None:
    normalized_email = normalize_email(email)

    return db.scalar(
        select(User).where(User.email == normalized_email)
    )


def create_user(
    db: Session,
    email: str,
    password: str,
    full_name: str,
    role: UserRole = UserRole.USER,
) -> User:
    user = User(
        email=normalize_email(email),
        password_hash=hash_password(password),
        full_name=full_name.strip(),
        role=role,
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise EmailAlreadyExistsError("Email already exists.") from exc

    db.refresh(user)

    return user