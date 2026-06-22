from dataclasses import dataclass
from enum import StrEnum


class ModelKind(StrEnum):
    EMBEDDING = "embedding"
    RERANKING = "reranking"


class ResidencyMode(StrEnum):
    DEDICATED = "dedicated"
    CO_RESIDENT = "co_resident"
    SWAPPING = "swapping"
    AUTO = "auto"


class ModelState(StrEnum):
    UNLOADED = "unloaded"
    CPU_READY = "cpu_ready"
    GPU_LOADING = "gpu_loading"
    GPU_READY = "gpu_ready"
    CPU_OFFLOADING = "cpu_offloading"
    FAILED = "failed"


class ScheduleAction(StrEnum):
    IDLE = "idle"
    STAY = "stay"
    LOAD = "load"
    SWITCH = "switch"


@dataclass(frozen=True, slots=True)
class QueueState:
    pending: int = 0
    oldest_wait_seconds: float = 0
    estimated_cost: int = 0

    def __post_init__(self) -> None:
        if self.pending < 0 or self.oldest_wait_seconds < 0 or self.estimated_cost < 0:
            raise ValueError("Queue values cannot be negative")


@dataclass(frozen=True, slots=True)
class SchedulerState:
    current: ModelKind | None
    embedding: QueueState
    reranking: QueueState
    residency_seconds: float = 0
    seconds_since_switch: float = 0
    epoch_seconds: float = 0
    epoch_cost: int = 0

    def queue_for(self, kind: ModelKind) -> QueueState:
        if kind is ModelKind.EMBEDDING:
            return self.embedding
        return self.reranking


@dataclass(frozen=True, slots=True)
class ScheduleDecision:
    action: ScheduleAction
    target: ModelKind | None
    reason: str
