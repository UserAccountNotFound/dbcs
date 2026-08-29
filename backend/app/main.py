from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.db.session import SessionLocal
from app.services import system_settings_service


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        swagger_ui_oauth2_redirect_url="/api/docs/oauth2-redirect",
    )

    @app.middleware("http")
    async def docs_access_control(request: Request, call_next):
        path = request.url.path
        openapi_path = f"{settings.api_v1_prefix}/openapi.json"
        is_docs = path == "/api/docs" or path.startswith("/api/docs/")
        is_redoc = path == "/api/redoc" or path.startswith("/api/redoc/")
        is_openapi = path == openapi_path

        if not (is_docs or is_redoc or is_openapi):
            return await call_next(request)

        db = SessionLocal()
        try:
            flags = system_settings_service.get_docs_flags(db)
        finally:
            db.close()

        if is_docs and not flags.docs_enabled:
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        if is_redoc and not flags.redoc_enabled:
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        if is_openapi and not (flags.docs_enabled or flags.redoc_enabled):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})

        return await call_next(request)

    allowed_origins = settings.allowed_origins_list

    if allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=[
                "GET",
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
                "OPTIONS",
            ],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "X-Requested-With",
                "X-DBCS-Referrer",
            ],
            expose_headers=[
                "Content-Disposition",
            ],
        )

    app.include_router(
        api_router,
        prefix=settings.api_v1_prefix,
    )

    return app


app = create_app()
