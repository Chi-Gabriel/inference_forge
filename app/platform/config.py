from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:8080",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = Field(default=8000, ge=1, le=65535)
    cors_allowed_origins: list[str] = Field(default=DEFAULT_CORS_ALLOWED_ORIGINS)
    api_key: str | None = None
    redis_url: str = "redis://redis:6379/0"
    job_store_backend: Literal["auto", "memory", "redis"] = "auto"
    job_store_redis_prefix: str = "inference_forge"
    job_store_redis_block_seconds: int = Field(default=2, ge=1, le=30)
    job_ttl_hours: float = Field(default=24, gt=0)
    cleanup_enabled: bool = True
    cleanup_interval_seconds: int = Field(default=3600, ge=60)
    media_upload_ttl_hours: float = Field(default=168, gt=0)
    media_download_ttl_hours: float = Field(default=168, gt=0)
    media_temp_ttl_hours: float = Field(default=6, gt=0)
    media_decoded_ttl_hours: float = Field(default=24, gt=0)
    media_cache_ttl_hours: float = Field(default=168, gt=0)
    media_root: Path = Path("var/media")
    media_upload_max_bytes: int = Field(default=1_073_741_824, gt=0)
    media_download_max_bytes: int = Field(default=1_073_741_824, gt=0)
    media_download_timeout_seconds: float = Field(default=30, gt=0)
    media_download_redirect_limit: int = Field(default=3, ge=0, le=10)
    media_extractor_enabled: bool = True
    media_extractor_timeout_seconds: int = Field(default=180, gt=0)
    media_extractor_max_duration_seconds: int = Field(default=600, gt=0)
    media_extractor_allowed_hosts: list[str] = Field(
        default=[
            "youtube.com",
            "youtu.be",
            "tiktok.com",
            "facebook.com",
            "fb.watch",
        ]
    )
    media_extractor_format: str = "bv*+ba/b"
    media_allowed_content_types: list[str] = Field(
        default=[
            "video/mp4",
            "video/quicktime",
            "video/webm",
            "image/jpeg",
            "image/png",
            "image/webp",
        ]
    )

    embedding_enabled: bool = True
    reranking_enabled: bool = True
    embedding_model_id: str = "Qwen/Qwen3-VL-Embedding-8B"
    embedding_model_revision: str = "2c4565515e0f265c6511776e7193b22c0968ddc7"
    embedding_model_vram_gib: float = Field(default=15.2, gt=0)
    embedding_max_length: int = Field(default=8192, ge=64, le=32768)
    embedding_max_frames: int = Field(default=16, ge=1, le=64)
    embedding_video_fps: float = Field(default=1, gt=0, le=10)
    reranking_model_id: str = "Qwen/Qwen3-VL-Reranker-2B"
    reranking_model_revision: str = "4bd860ac4f15ad1897a214615cccc700f8f71818"
    reranking_model_vram_gib: float = Field(default=4, gt=0)
    reranking_max_length: int = Field(default=8192, ge=64, le=32768)
    reranking_max_frames: int = Field(default=16, ge=1, le=64)
    reranking_video_fps: float = Field(default=1, gt=0, le=10)

    gpu_residency_mode: Literal["dedicated", "co_resident", "swapping", "auto"] = "auto"
    gpu_vram_cap_gib: float = Field(default=23, gt=0)
    gpu_activation_reserve_gib: float = Field(default=2.5, ge=0)
    gpu_fragmentation_margin_gib: float = Field(default=1, ge=0)

    embedding_text_batch_max: int = Field(default=128, gt=0)
    embedding_image_batch_max: int = Field(default=8, gt=0)
    embedding_video_batch_max: int = Field(default=4, gt=0)
    reranking_text_pair_batch_max: int = Field(default=256, gt=0)
    reranking_image_pair_batch_max: int = Field(default=8, gt=0)
    reranking_video_pair_batch_max: int = Field(default=4, gt=0)

    model_epoch_max_seconds: float = Field(default=60, gt=0)
    model_epoch_max_cost: int = Field(default=8192, gt=0)
    model_min_residency_seconds: float = Field(default=30, ge=0)
    model_switch_cooldown_seconds: float = Field(default=15, ge=0)
    model_queue_max_wait_seconds: float = Field(default=30, gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
