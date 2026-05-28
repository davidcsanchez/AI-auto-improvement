from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.dependencies import get_ticket_storage
from src.api.routes.process import router as process_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_ticket_storage()
    yield


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(process_router)

    return app


app = create_app()
