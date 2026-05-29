from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.errors import register_exception_handlers
from src.api.dependencies import get_ticket_storage
from src.api.routes.process import router as process_router

from scripts.seed_db import seed_database 

@asynccontextmanager
async def lifespan(_: FastAPI):
    get_ticket_storage()
    await seed_database()
    yield

def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    register_exception_handlers(app)
    app.include_router(process_router)

    return app

app = create_app()