from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.platform.config import Settings, get_settings

router = APIRouter(tags=["models"])


class ModelCapabilities(BaseModel):
    text: bool
    image: bool
    video: bool


class ModelInfo(BaseModel):
    id: str
    object: Literal["model"] = "model"
    service: Literal["embedding", "reranking"]
    capabilities: ModelCapabilities


class ModelList(BaseModel):
    object: Literal["list"] = "list"
    data: list[ModelInfo]


@router.get("/models", response_model=ModelList)
async def list_models(settings: Settings = Depends(get_settings)) -> ModelList:
    capabilities = ModelCapabilities(text=True, image=True, video=True)
    available: list[ModelInfo] = []
    if settings.embedding_enabled:
        available.append(
            ModelInfo(
                id=settings.embedding_model_id,
                service="embedding",
                capabilities=capabilities,
            )
        )
    if settings.reranking_enabled:
        available.append(
            ModelInfo(
                id=settings.reranking_model_id,
                service="reranking",
                capabilities=capabilities,
            )
        )
    return ModelList(data=available)
