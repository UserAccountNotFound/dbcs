from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

from fastapi import Request


def _is_trusted_proxy(host: str | None) -> bool:
    """Доверяем заголовкам X-Forwarded-* только от локальных/приватных прокси."""
    if not host:
        return False
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return bool(ip.is_loopback or ip.is_private or ip.is_link_local)


def get_client_ip(request: Request) -> str | None:
    """
    IP реального клиента.

    За Nginx берём X-Real-IP / первый адрес из X-Forwarded-For,
    если непосредственный peer — доверенный прокси (localhost/private).
    """
    peer = request.client.host if request.client else None

    if peer and _is_trusted_proxy(peer):
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # Слева направо: оригинальный клиент, затем прокси
            first = forwarded.split(",")[0].strip()
            if first:
                return first
        real_ip = request.headers.get("x-real-ip")
        if real_ip and real_ip.strip():
            return real_ip.strip()

    return peer


def get_user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


def is_internal_referrer(url: str | None) -> bool:
    """
    True, если URL — наша же страница визитки/API, а не внешний источник трафика.
    Браузерный Referer на API-запрос часто равен URL SPA (/public/card/...),
    его нельзя считать источником.
    """
    if not url or not url.strip():
        return True

    try:
        parsed = urlparse(url.strip())
    except Exception:
        return False

    path = (parsed.path or "").lower()
    if "/public/card" in path:
        return True
    if path.startswith("/api/") or "/api/v1/" in path:
        return True

    # Хост из PUBLIC_BASE_URL — тоже «свой» сайт
    try:
        from app.core.config import settings

        base = urlparse(settings.public_base_url)
        if (
            parsed.hostname
            and base.hostname
            and parsed.hostname.lower() == base.hostname.lower()
        ):
            return True
    except Exception:
        pass

    return False


def get_visit_referrer(request: Request) -> str | None:
    """
    Источник перехода на визитку.

    Приоритет:
    1) X-DBCS-Referrer — document.referrer со SPA (настоящий внешний источник)
    2) стандартный Referer/Referrer HTTP-заголовка
    Собственные URL визитки отбрасываем.
    """
    raw = (
        request.headers.get("x-dbcs-referrer")
        or request.headers.get("referer")
        or request.headers.get("referrer")
    )
    if raw is not None:
        raw = raw.strip()
    if not raw or is_internal_referrer(raw):
        return None
    return raw[:2048]
