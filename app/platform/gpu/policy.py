from dataclasses import dataclass

from app.platform.gpu.types import (
    ModelKind,
    ScheduleAction,
    ScheduleDecision,
    SchedulerState,
)


@dataclass(frozen=True, slots=True)
class ResidencyPolicy:
    epoch_max_seconds: float
    epoch_max_cost: int
    min_residency_seconds: float
    switch_cooldown_seconds: float
    queue_max_wait_seconds: float
    debug: bool = False

    def decide(self, state: SchedulerState) -> ScheduleDecision:
        if state.current is None:
            target = self._initial_target(state)
            if target is None:
                return ScheduleDecision(ScheduleAction.IDLE, None, "queues_empty")
            return ScheduleDecision(ScheduleAction.LOAD, target, "work_available")

        current = state.current
        alternative = self._alternative(current)
        current_queue = state.queue_for(current)
        alternative_queue = state.queue_for(alternative)

        if alternative_queue.pending == 0:
            if current_queue.pending == 0:
                return ScheduleDecision(ScheduleAction.IDLE, current, "queues_empty")
            return ScheduleDecision(ScheduleAction.STAY, current, "no_competing_work")

        if current_queue.pending == 0:
            return ScheduleDecision(
                ScheduleAction.SWITCH, alternative, "current_queue_empty"
            )

        if alternative_queue.oldest_wait_seconds >= self.queue_max_wait_seconds:
            return ScheduleDecision(
                ScheduleAction.SWITCH, alternative, "queue_deadline"
            )

        if state.residency_seconds < self.min_residency_seconds:
            return ScheduleDecision(ScheduleAction.STAY, current, "minimum_residency")

        if state.seconds_since_switch < self.switch_cooldown_seconds:
            return ScheduleDecision(ScheduleAction.STAY, current, "switch_cooldown")

        if state.epoch_seconds >= self.epoch_max_seconds:
            return ScheduleDecision(
                ScheduleAction.SWITCH, alternative, "epoch_time_budget"
            )

        if state.epoch_cost >= self.epoch_max_cost:
            return ScheduleDecision(
                ScheduleAction.SWITCH, alternative, "epoch_cost_budget"
            )

        return ScheduleDecision(ScheduleAction.STAY, current, "continue_epoch")

    def _initial_target(self, state: SchedulerState) -> ModelKind | None:
        embedding = state.embedding
        reranking = state.reranking
        if embedding.pending == 0 and reranking.pending == 0:
            return None
        if embedding.pending == 0:
            return ModelKind.RERANKING
        if reranking.pending == 0:
            return ModelKind.EMBEDDING
        if reranking.oldest_wait_seconds >= embedding.oldest_wait_seconds:
            return ModelKind.RERANKING
        return ModelKind.EMBEDDING

    @staticmethod
    def _alternative(kind: ModelKind) -> ModelKind:
        if kind is ModelKind.EMBEDDING:
            return ModelKind.RERANKING
        return ModelKind.EMBEDDING
