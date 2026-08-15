import sys

from loguru import logger


def setup_logging() -> None:
    logger.remove()
    logger.add(sys.stderr, level="INFO")
