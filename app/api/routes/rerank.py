from fastapi import APIRouter, Depends, Request

from app.api.dependencies import require_api_key
from app.platform.jobs.store import InMemoryJobStore
from app.platform.jobs.types import JobKind, JobPublic, public_job
from app.services.runtime.types import RerankJobPayload

router = APIRouter(
    prefix="/rerank",
    tags=["reranking"],
    dependencies=[Depends(require_api_key)],
)


@router.post("/jobs", response_model=JobPublic)
async def create_rerank_job(
    payload: RerankJobPayload,
    request: Request,
) -> JobPublic:
    record = await job_store(request).create(JobKind.RERANKING, payload.model_dump())
    return public_job(record)


def job_store(request: Request) -> InMemoryJobStore:
    return request.app.state.job_store
