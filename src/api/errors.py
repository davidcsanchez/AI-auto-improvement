from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.core.logger import get_logger


logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def _handle_unexpected_error(_: Request, __: Exception) -> JSONResponse:
        logger.exception("Unhandled server error")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
