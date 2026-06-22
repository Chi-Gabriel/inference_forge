from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.platform.config import get_settings
from app.platform.jobs.store import InMemoryJobStore
from app.platform.media.store import MediaStore
from app.services.runtime import JobExecutor


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    media_store = MediaStore(settings, settings.app_debug)
    job_store = InMemoryJobStore(settings.app_debug)
    executor = JobExecutor(settings, media_store, job_store, settings.app_debug)
    job_store.configure(executor.execute)
    job_store.start()
    application.state.media_store = media_store
    application.state.job_store = job_store
    try:
        yield
    finally:
        await job_store.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="Inference Forge",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    application.include_router(api_router)
    return application


app = create_app()
