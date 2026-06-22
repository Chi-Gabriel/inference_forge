from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class MediaKind(StrEnum):
    IMAGE = "image"
    VIDEO = "video"


class MediaRecord(BaseModel):
    id: str
    kind: MediaKind
    content_type: str
    sha256: str
    size_bytes: int = Field(ge=0)
    path: Path
    source_url: str | None = None
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None


class VideoSegment(BaseModel):
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    path: Path
