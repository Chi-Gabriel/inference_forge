from dataclasses import dataclass

import pytest

from app.platform.gpu.residency import ResidencyCoordinator
from app.platform.gpu.types import ModelKind, ModelState, ResidencyMode


@dataclass
class FakeModel:
    kind: ModelKind
    resident_vram_gib: float
    state: ModelState = ModelState.UNLOADED
    load_count: int = 0
    offload_count: int = 0

    async def prepare_cpu(self) -> None:
        self.state = ModelState.CPU_READY

    async def load_gpu(self) -> None:
        self.load_count += 1
        self.state = ModelState.GPU_LOADING

    async def warmup(self) -> None:
        self.state = ModelState.GPU_READY

    async def offload_cpu(self) -> None:
        self.offload_count += 1
        self.state = ModelState.CPU_READY


def make_models(vram: float = 15.2) -> dict[ModelKind, FakeModel]:
    return {
        ModelKind.EMBEDDING: FakeModel(ModelKind.EMBEDDING, vram),
        ModelKind.RERANKING: FakeModel(ModelKind.RERANKING, vram),
    }


def test_auto_mode_rejects_two_8b_models_on_24gb_profile() -> None:
    coordinator = ResidencyCoordinator(make_models(), ResidencyMode.AUTO, 22, 5, 1)

    assert coordinator.required_vram_gib() == pytest.approx(36.4)
    assert coordinator.effective_mode is ResidencyMode.SWAPPING


def test_auto_mode_accepts_8b_embedding_and_2b_reranker_profile() -> None:
    models = make_models()
    models[ModelKind.RERANKING].resident_vram_gib = 4
    coordinator = ResidencyCoordinator(models, ResidencyMode.AUTO, 23, 2.5, 1)

    assert coordinator.required_vram_gib() == pytest.approx(22.7)
    assert coordinator.effective_mode is ResidencyMode.CO_RESIDENT


def test_unsafe_explicit_co_residency_is_rejected() -> None:
    with pytest.raises(ValueError, match="VRAM budget"):
        ResidencyCoordinator(make_models(), ResidencyMode.CO_RESIDENT, 22, 5, 1)


@pytest.mark.asyncio
async def test_swapping_offloads_previous_model() -> None:
    models = make_models()
    coordinator = ResidencyCoordinator(models, ResidencyMode.SWAPPING, 22, 5, 1)
    await coordinator.prepare()
    await coordinator.ensure_gpu(ModelKind.EMBEDDING)
    await coordinator.ensure_gpu(ModelKind.RERANKING)

    assert models[ModelKind.EMBEDDING].state is ModelState.CPU_READY
    assert models[ModelKind.EMBEDDING].offload_count == 1
    assert models[ModelKind.RERANKING].state is ModelState.GPU_READY


@pytest.mark.asyncio
async def test_co_resident_mode_keeps_previous_model_loaded() -> None:
    models = make_models(vram=4)
    coordinator = ResidencyCoordinator(models, ResidencyMode.AUTO, 22, 5, 1)
    await coordinator.prepare()
    await coordinator.ensure_gpu(ModelKind.EMBEDDING)
    await coordinator.ensure_gpu(ModelKind.RERANKING)

    assert coordinator.effective_mode is ResidencyMode.CO_RESIDENT
    assert all(model.state is ModelState.GPU_READY for model in models.values())
