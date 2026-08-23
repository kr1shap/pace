from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


def error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": jsonable_encoder(details or {}),
            }
        },
    )


def _default_http_code(status_code: int) -> str:
    return {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        429: "RATE_LIMITED",
        502: "UPSTREAM_FAILURE",
        503: "SERVICE_UNAVAILABLE",
    }.get(status_code, "HTTP_ERROR")


async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        code = str(exc.detail.get("code", _default_http_code(exc.status_code)))
        message = str(exc.detail.get("message", "Request failed."))
        details = exc.detail.get("details", {})
    else:
        code = _default_http_code(exc.status_code)
        message = str(exc.detail)
        details = {}

    return error_response(
        status_code=exc.status_code,
        code=code,
        message=message,
        details=details,
    )


async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    return error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="The request could not be validated.",
        details={"errors": exc.errors()},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
