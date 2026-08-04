from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.security import hash_pii
from app.core.utils import get_client_ip, get_user_agent
from app.models import AuditLog


def log(
    db: Session,
    action: str,
    actor_user_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    request: Request | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    ip_hash = None
    user_agent_hash = None

    if request is not None:
        ip_hash = hash_pii(get_client_ip(request))
        user_agent_hash = hash_pii(get_user_agent(request))

    audit_entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_hash=ip_hash,
        user_agent_hash=user_agent_hash,
        details_json=details or {},
    )

    db.add(audit_entry)
    db.commit()