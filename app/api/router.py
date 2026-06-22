from fastapi import APIRouter

from app.api.routes import embeddings, health, jobs, media, models, rerank

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(models.router, prefix="/v1")
api_router.include_router(media.router, prefix="/v1")
api_router.include_router(jobs.router, prefix="/v1")
api_router.include_router(embeddings.router, prefix="/v1")
api_router.include_router(rerank.router, prefix="/v1")
