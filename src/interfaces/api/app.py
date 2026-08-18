import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from src.infrastructure.kafka.base_consumer import BaseConsumer
from src.infrastructure.logging_config import setup_logging
from src.interfaces.api.containers import container
from src.interfaces.api.exceptions import register_exception_handlers
from src.interfaces.api.routers import transactions, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    event_producer = container.event_producer()
    await event_producer.start()

    consumers = [
        container.user_consumer(),
        container.transaction_consumer(),
    ]
    tasks = [asyncio.create_task(_run_consumer(consumer)) for consumer in consumers]
    logger.info("Kafka consumers started")

    yield

    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    for consumer in consumers:
        await consumer.stop()
    await event_producer.stop()
    logger.info("Kafka consumers stopped")


async def _run_consumer(consumer: BaseConsumer) -> None:
    while True:
        try:
            await consumer.run()
            return
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Consumer for topic '{}' crashed, restarting in 5s", consumer.topic)
            await asyncio.sleep(5)


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
