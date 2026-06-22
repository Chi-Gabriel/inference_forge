from typing import Any, Literal

from pydantic import BaseModel, Field


class SegmentationOptions(BaseModel):
    chunk_seconds: float = Field(default=10, gt=0)
    overlap_seconds: float = Field(default=0, ge=0)


class SamplingOptions(BaseModel):
    fps: float = Field(default=1, gt=0, le=10)
    max_frames: int = Field(default=16, ge=1, le=64)


class MultimodalInput(BaseModel):
    type: Literal["text", "image", "video", "video_segment"]
    text: str | None = None
    media_id: str | None = None
    segment: dict[str, float] | None = None
    segmentation: SegmentationOptions | None = None
    sampling: SamplingOptions | None = None


class EmbeddingJobPayload(BaseModel):
    model: str | None = None
    input: list[MultimodalInput]
    query: MultimodalInput | None = None
    dimensions: int = Field(default=4096, ge=64, le=4096)
    top_k: int = Field(default=8, ge=1, le=200)


class RerankJobPayload(BaseModel):
    query: MultimodalInput
    documents: list[MultimodalInput]
    instruction: str | None = None
    top_k: int = Field(default=8, ge=1, le=200)
    sampling: SamplingOptions | None = None


class ScoredItem(BaseModel):
    id: str
    type: str
    score: float | None = None
    rerank_score: float | None = None
    text: str | None = None
    media_id: str | None = None
    segment: dict[str, float] | None = None
    latency_ms: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
