from app.domain.exceptions import (
    CrossTenantAccessError,
    DomainError,
    InvalidStateTransitionError,
    PermissionDeniedError,
)
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request,
        exc: ValueError,
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(PermissionError)
    async def permission_error_handler(
        request: Request,
        exc: PermissionError,
    ) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(CrossTenantAccessError)
    async def cross_tenant_error_handler(
        request: Request,
        exc: CrossTenantAccessError,
    ) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(PermissionDeniedError)
    async def permission_denied_error_handler(
        request: Request,
        exc: PermissionDeniedError,
    ) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(InvalidStateTransitionError)
    async def invalid_state_error_handler(
        request: Request,
        exc: InvalidStateTransitionError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def domain_error_handler(
        request: Request,
        exc: DomainError,
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})