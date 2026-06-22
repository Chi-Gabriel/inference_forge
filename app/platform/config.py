from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = Field(default=8000, ge=1, le=65535)
    redis_url: str = "redis://redis:6379/0"

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
