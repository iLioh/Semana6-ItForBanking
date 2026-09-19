"""Punto de entrada FastAPI."""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.app.config import PROJECT_ROOT, AppSettings, get_settings
from src.app.database import create_schema
from src.app.routes import router

logger = logging.getLogger("lab06.api")


def build_entra_scope(settings: AppSettings) -> str:
    """Return the fully qualified delegated scope expected by MSAL."""

    scope = settings.entra_required_scope
    if settings.entra_audience and "://" not in scope:
        return f"{settings.entra_audience.rstrip('/')}/{scope}"
    return scope


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.environment == "azure-demo" and os.getenv("LAB06_BLOB_BOOTSTRAP_ONCE") == "1":
        from src.app.blob_bootstrap import bootstrap_official_blobs

        bootstrap_official_blobs()
    if settings.applicationinsights_connection_string:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(connection_string=settings.applicationinsights_connection_string)
    # Local development remains zero-config. Production schema changes are
    # applied explicitly with Alembic during deployment so the runtime identity
    # does not need DDL permissions.
    if settings.environment == "local":
        create_schema()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="IBLaboratorio06 API",
        version="1.0.0",
        description=(
            "API académica para KYC, scoring explicable y clasificación de quejas simuladas. "
            "La decision final siempre corresponde a un analista humano."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
    )

    @app.middleware("http")
    async def correlation_middleware(request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' "
            "https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
            "connect-src 'self' https://login.microsoftonline.com "
            "https://*.microsoftonline.com; frame-ancestors 'none'"
        )
        logger.info(
            "request_completed method=%s path=%s status=%s correlation_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            correlation_id,
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": "VALIDATION_ERROR",
                "detail": "Entrada invalida: " + ", ".join(
                    ".".join(str(part) for part in item["loc"]) + ": " + item["type"]
                    for item in error.errors()
                ),
                "correlation_id": getattr(request.state, "correlation_id", "unknown"),
            },
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException):
        return JSONResponse(
            status_code=error.status_code,
            content={
                "error": "HTTP_ERROR",
                "detail": str(error.detail),
                "correlation_id": getattr(request.state, "correlation_id", "unknown"),
            },
            headers=error.headers,
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, error: Exception):
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        logger.error(
            "unexpected_error correlation_id=%s",
            correlation_id,
            exc_info=(type(error), error, error.__traceback__),
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "detail": "Error interno; consulte el identificador de correlacion.",
                "correlation_id": correlation_id,
            },
        )

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "environment": settings.environment,
            "ai_provider": settings.ai_provider,
        }

    @app.get("/api/v1/public-config", tags=["configuration"])
    def public_config() -> dict[str, str | bool]:
        """Expone solo metadatos publicos necesarios para iniciar sesion con Entra."""

        return {
            "authRequired": settings.auth_required,
            "entraClientId": settings.entra_client_id,
            "entraAuthority": (
                f"https://login.microsoftonline.com/{settings.entra_tenant_id}"
                if settings.entra_tenant_id
                else ""
            ),
            "entraScope": build_entra_scope(settings),
            "apiAudience": settings.entra_audience,
        }

    app.include_router(router)

    spa_root = PROJECT_ROOT / "frontend" / "dist"
    assets_root = spa_root / "assets"
    if assets_root.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_root), name="spa-assets")

        @app.get("/{path:path}", include_in_schema=False)
        def serve_spa(path: str):
            candidate = (spa_root / path).resolve()
            if candidate.is_file() and spa_root.resolve() in candidate.parents:
                return FileResponse(candidate)
            if path.startswith("api/"):
                return JSONResponse(status_code=404, content={"detail": "Not Found"})
            return FileResponse(spa_root / "index.html")

    return app


app = create_app()
