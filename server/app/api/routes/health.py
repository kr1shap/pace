from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
    version: str


class ReadinessResponse(BaseModel):
    status: Literal["ready"] = "ready"
    checks: dict[str, Literal["ok"]]


router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(service="pace-api", version=settings.app_version)


@router.get("/ready", response_model=ReadinessResponse, summary="Readiness probe")
async def readiness() -> ReadinessResponse:
    # Database and upstream checks will be added when those adapters exist.
    return ReadinessResponse(checks={})

