import time
from dataclasses import dataclass
from typing import Protocol

from app.platform.gpu.policy import ResidencyPolicy
from app.platform.gpu.residency import ResidencyCoordinator
from app.platform.gpu.types import (
    ModelKind,
    QueueState,
    ScheduleAction,
    SchedulerState,
)


@dataclass(frozen=True, slots=True)
class ClaimedBatch:
    kind: ModelKind
    item_ids: tuple[str, ...]
    estimated_cost: int


class BatchBroker(Protocol):
    async def queue_state(self, kind: ModelKind) -> QueueState: ...

    async def claim_batch(
        self, kind: ModelKind, max_cost: int
    ) -> ClaimedBatch | None: ...


class BatchExecutor(Protocol):
    async def execute(self, batch: ClaimedBatch) -> None: ...


class WorkerScheduler:
    def __init__(
        self,
        broker: BatchBroker,
        executor: BatchExecutor,
        residency: ResidencyCoordinator,
        policy: ResidencyPolicy,
        batch_max_cost: int,
        debug: bool = False,
    ) -> None:
        self._broker = broker
        self._executor = executor
        self._residency = residency
        self._policy = policy
        self._batch_max_cost = batch_max_cost
        self._debug = debug
        self._current: ModelKind | None = None
        self._residency_started = time.monotonic()
        self._last_switch = self._residency_started
        self._epoch_started = self._residency_started
        self._epoch_cost = 0

    async def run_once(self) -> bool:
        now = time.monotonic()
        embedding = await self._broker.queue_state(ModelKind.EMBEDDING)
        reranking = await self._broker.queue_state(ModelKind.RERANKING)
        state = SchedulerState(
            current=self._current,
            embedding=embedding,
            reranking=reranking,
            residency_seconds=now - self._residency_started,
            seconds_since_switch=now - self._last_switch,
            epoch_seconds=now - self._epoch_started,
            epoch_cost=self._epoch_cost,
        )
        decision = self._policy.decide(state)

        if decision.action is ScheduleAction.IDLE or decision.target is None:
            return False

        if decision.action in {ScheduleAction.LOAD, ScheduleAction.SWITCH}:
            await self._residency.ensure_gpu(decision.target)
            self._current = decision.target
            self._residency_started = now
            self._last_switch = now
            self._epoch_started = now
            self._epoch_cost = 0

        batch = await self._broker.claim_batch(decision.target, self._batch_max_cost)
        if batch is None:
            return False
        await self._executor.execute(batch)
        self._epoch_cost += batch.estimated_cost
        return True
