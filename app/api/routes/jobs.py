from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.dependencies import require_api_key
from app.platform.jobs.store import JobStore
from app.platform.jobs.types import JobPublic, public_job

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/{job_id}", response_model=JobPublic)
async def get_job(job_id: str, request: Request) -> JobPublic:
    try:
        return public_job(await job_store(request).get(job_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job id was not found") from exc


def job_store(request: Request) -> JobStore:
    return request.app.state.job_store
