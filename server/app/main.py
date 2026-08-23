from collections.abc import Callable
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.router import api_router
from app.api.routes.health import router as health_router
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers


def _build_openapi(app: FastAPI, settings: Settings) -> Callable[[], dict[str, Any]]:
    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=settings.app_name,
            version=settings.app_version,
            description=(
                "Pace's read-only, money-habit API. Product endpoints are versioned under "
                f"`{settings.api_prefix}` and use Supabase bearer tokens."
            ),
            routes=app.routes,
            tags=[
                {"name": "system", "description": "Service health and readiness."},
                {"name": "v1", "description": "Pace MVP API (version 1)."},
            ],
        )
        schema.setdefault("components", {}).setdefault("securitySchemes", {})[
            "BearerAuth"
        ] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Supabase access token.",
        }
        app.openapi_schema = schema
        return schema

    return custom_openapi


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    docs_url = "/docs" if app_settings.docs_enabled else None
    redoc_url = "/redoc" if app_settings.docs_enabled else None
    openapi_url = "/openapi.json" if app_settings.docs_enabled else None

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )
    app.state.settings = app_settings
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(api_router, prefix=app_settings.api_prefix)
    app.openapi = _build_openapi(app, app_settings)
    return app


app = create_app()
