import logging
import sys
from typing import Final

LOG_FORMAT: Final[str] = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    root_logger.setLevel(logging.INFO)

    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = logging.FileHandler("system.log")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)


configure_logging()
logger = logging.getLogger("system")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def truncate_text(value: str | None, limit: int = 200) -> str:
    if not value:
        return ""
    return value if len(value) <= limit else f"{value[:limit]}..."
