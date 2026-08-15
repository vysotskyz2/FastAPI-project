from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.infrastructure.logging_config import setup_logging
from src.interfaces.api.exceptions import register_exception_handlers
from src.interfaces.api.routers import transactions, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="Transaction service",
        lifespan=lifespan,
    )
    application.include_router(users.router)
    application.include_router(transactions.router)
    register_exception_handlers(application)
    return application


app = create_app()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
