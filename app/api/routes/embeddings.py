from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.api.dependencies import require_api_key
from app.platform.jobs.store import JobStore
from app.platform.jobs.types import JobKind, JobPublic, public_job
from app.services.runtime.types import EmbeddingJobPayload

router = APIRouter(
    prefix="/embeddings",
    tags=["embeddings"],
    dependencies=[Depends(require_api_key)],
)


class OpenAIEmbeddingRequest(BaseModel):
    input: str | list[str]
    model: str | None = None
    dimensions: int = 4096


@router.post("/jobs", response_model=JobPublic)
async def create_embedding_job(
    payload: EmbeddingJobPayload,
    request: Request,
) -> JobPublic:
    record = await job_store(request).create(JobKind.EMBEDDING, payload.model_dump())
    return public_job(record)


@router.post("", response_model=JobPublic)
async def create_openai_embedding_job(
    payload: OpenAIEmbeddingRequest,
    request: Request,
) -> JobPublic:
    inputs = payload.input if isinstance(payload.input, list) else [payload.input]
    job_payload = EmbeddingJobPayload(
        model=payload.model,
        input=[{"type": "text", "text": item} for item in inputs],
        dimensions=payload.dimensions,
    )
    record = await job_store(request).create(
        JobKind.EMBEDDING, job_payload.model_dump()
    )
    return public_job(record)


def job_store(request: Request) -> JobStore:
    return request.app.state.job_store
