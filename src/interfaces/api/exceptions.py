from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.application.exceptions import DomainException


def register_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
