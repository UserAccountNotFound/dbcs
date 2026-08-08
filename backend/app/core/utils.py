from fastapi import Request


def get_client_ip(request: Request) -> str | None:
    """
    Пока берем прямой IP клиента.

    Позже, если backend будет работать за Nginx/reverse proxy,
    нужно будет аккуратно парсить X-Forwarded-For и доверять
    только первому hop из доверенной сети.
    """
    if request.client is None:
        return None

    return request.client.host


def get_user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")