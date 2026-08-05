from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


class AdminUserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    mfa_enabled: bool
    created_at: datetime
    last_login_at: datetime | None
    cards_count: int = 0


class AdminUserListResponse(BaseModel):
    items: list[AdminUserResponse]
    total: int
    limit: int
    offset: int

class AdminUserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=12, max_length=128)
    role: UserRole = UserRole.USER

class AdminUserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=12, max_length=128)

class AdminCardResponse(BaseModel):
    id: str
    slug: str
    title: str
    full_name: str
    is_active: bool
    created_at: datetime
    user_email: EmailStr
    visits_count: int = 0


class AdminCardListResponse(BaseModel):
    items: list[AdminCardResponse]
    total: int
    limit: int
    offset: int


class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_type: str | None
    entity_id: str | None
    created_at: datetime
    actor_email: EmailStr | None
    details: dict | None = None


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int


class OverviewStatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_cards: int
    active_cards: int
    total_visits: int
    total_vcard_downloads: int