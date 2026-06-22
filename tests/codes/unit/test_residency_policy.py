import pytest

from app.platform.gpu.policy import ResidencyPolicy
from app.platform.gpu.types import (
    ModelKind,
    QueueState,
    ScheduleAction,
    SchedulerState,
)


@pytest.fixture
def policy() -> ResidencyPolicy:
    return ResidencyPolicy(
        epoch_max_seconds=30,
        epoch_max_cost=8192,
        min_residency_seconds=10,
        switch_cooldown_seconds=5,
        queue_max_wait_seconds=15,
    )


def test_loads_oldest_queue_when_no_model_is_resident(policy: ResidencyPolicy) -> None:
    state = SchedulerState(
        current=None,
        embedding=QueueState(pending=4, oldest_wait_seconds=3),
        reranking=QueueState(pending=2, oldest_wait_seconds=7),
    )

    decision = policy.decide(state)

    assert decision.action is ScheduleAction.LOAD
    assert decision.target is ModelKind.RERANKING


def test_empty_current_queue_switches_immediately(policy: ResidencyPolicy) -> None:
    state = SchedulerState(
        current=ModelKind.EMBEDDING,
        embedding=QueueState(),
        reranking=QueueState(pending=2),
    )

    decision = policy.decide(state)

    assert decision.action is ScheduleAction.SWITCH
    assert decision.target is ModelKind.RERANKING


def test_queue_deadline_overrides_minimum_residency(
    policy: ResidencyPolicy,
) -> None:
    state = SchedulerState(
        current=ModelKind.EMBEDDING,
        embedding=QueueState(pending=10),
        reranking=QueueState(pending=1, oldest_wait_seconds=15),
        residency_seconds=2,
        seconds_since_switch=2,
    )

    decision = policy.decide(state)

    assert decision.action is ScheduleAction.SWITCH
    assert decision.reason == "queue_deadline"


def test_embedding_queue_also_has_starvation_protection(
    policy: ResidencyPolicy,
) -> None:
    state = SchedulerState(
        current=ModelKind.RERANKING,
        embedding=QueueState(pending=1, oldest_wait_seconds=15),
        reranking=QueueState(pending=10),
        residency_seconds=2,
        seconds_since_switch=2,
    )

    decision = policy.decide(state)

    assert decision.action is ScheduleAction.SWITCH
    assert decision.target is ModelKind.EMBEDDING


def test_epoch_cost_switches_when_both_queues_have_work(
    policy: ResidencyPolicy,
) -> None:
    state = SchedulerState(
        current=ModelKind.EMBEDDING,
        embedding=QueueState(pending=10),
        reranking=QueueState(pending=10),
        residency_seconds=20,
        seconds_since_switch=20,
        epoch_cost=8192,
    )

    decision = policy.decide(state)

    assert decision.action is ScheduleAction.SWITCH
    assert decision.reason == "epoch_cost_budget"
