import time
import uuid
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    QUEUED = "queued"
    RESOLVING_MEDIA = "resolving_media"
    DOWNLOADING = "downloading"
    PROBING_MEDIA = "probing_media"
    SEGMENTING = "segmenting"
    EMBEDDING = "embedding"
    RERANKING = "reranking"
    COMPLETE = "complete"
    FAILED = "failed"


class JobKind(StrEnum):
    EMBEDDING = "embedding"
    RERANKING = "reranking"


class JobRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"job_{uuid.uuid4().hex}")
    kind: JobKind
    status: JobStatus = JobStatus.QUEUED
    progress: int = Field(default=0, ge=0, le=100)
    stage_label: str = "Queued"
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    elapsed_ms: int | None = None
    error: str | None = None
    payload: dict[str, Any]
    result: dict[str, Any] | None = None


class JobPublic(BaseModel):
    id: str
    job_id: str
    kind: JobKind
    status: JobStatus
    progress: int
    stage_label: str
    created_at: float
    updated_at: float
    elapsed_ms: int | None = None
    error: str | None = None
    result: dict[str, Any] | None = None


def public_job(record: JobRecord) -> JobPublic:
    return JobPublic(
        id=record.id,
        job_id=record.id,
        kind=record.kind,
        status=record.status,
        progress=record.progress,
        stage_label=record.stage_label,
        created_at=record.created_at,
        updated_at=record.updated_at,
        elapsed_ms=record.elapsed_ms,
        error=record.error,
        result=record.result,
    )
