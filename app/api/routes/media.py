import asyncio

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from app.api.dependencies import require_api_key
from app.platform.media.store import MediaStore
from app.platform.media.types import MediaRecord

router = APIRouter(
    prefix="/media",
    tags=["media"],
    dependencies=[Depends(require_api_key)],
)


class MediaPublic(BaseModel):
    media_id: str
    id: str
    kind: str
    content_type: str
    size_bytes: int
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None


class DownloadRequest(BaseModel):
    url: str = Field(min_length=1, max_length=4096)


@router.post("/uploads", response_model=MediaPublic)
async def upload_media(
    request: Request,
    file: UploadFile = File(...),
) -> MediaPublic:
    store = media_store(request)
    try:
        return media_public(await store.save_upload(file))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/downloads", response_model=MediaPublic)
async def download_media(
    payload: DownloadRequest,
    request: Request,
) -> MediaPublic:
    store = media_store(request)
    try:
        record = await asyncio.to_thread(store.download_url, payload.url)
        return media_public(record)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{media_id}", response_model=MediaPublic)
async def get_media(media_id: str, request: Request) -> MediaPublic:
    try:
        return media_public(media_store(request).get(media_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Media id was not found") from exc


def media_store(request: Request) -> MediaStore:
    return request.app.state.media_store


def media_public(record: MediaRecord) -> MediaPublic:
    return MediaPublic(
        media_id=record.id,
        id=record.id,
        kind=record.kind.value,
        content_type=record.content_type,
        size_bytes=record.size_bytes,
        duration_seconds=record.duration_seconds,
        width=record.width,
        height=record.height,
    )
