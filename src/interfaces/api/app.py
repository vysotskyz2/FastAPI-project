import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger
from tenacity import RetryCallState, retry, stop_after_attempt, wait_fixed

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


async def _run_consumer(consumer: BaseConsumer, max_retries: int = 3, retry_delay: float = 5.0) -> None:
    def _log_retry_attempt(retry_state: RetryCallState) -> None:
        logger.warning(
            "Consumer for topic '{}' crashed (attempt {}/{}), restarting in {}s",
            consumer.topic,
            retry_state.attempt_number,
            max_retries,
            retry_delay,
        )

    @retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_fixed(retry_delay),
        before_sleep=_log_retry_attempt,
        reraise=True,
    )
    async def run() -> None:
        await consumer.run()

    try:
        await run()
    except Exception:
        logger.error(
            "Failed to start consumer for topic '{}' after {} attempts; giving up",
            consumer.topic,
            max_retries,
        )


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
