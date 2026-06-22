import asyncio
from collections.abc import Mapping
from typing import Protocol

from app.platform.errors import ResidencyTransitionError
from app.platform.gpu.types import ModelKind, ModelState, ResidencyMode


class ManagedModel(Protocol):
    kind: ModelKind
    state: ModelState
    resident_vram_gib: float

    async def prepare_cpu(self) -> None: ...

    async def load_gpu(self) -> None: ...

    async def warmup(self) -> None: ...

    async def offload_cpu(self) -> None: ...


class ResidencyCoordinator:
    def __init__(
        self,
        models: Mapping[ModelKind, ManagedModel],
        mode: ResidencyMode,
        vram_cap_gib: float,
        activation_reserve_gib: float,
        fragmentation_margin_gib: float,
        debug: bool = False,
    ) -> None:
        self._models = dict(models)
        self._configured_mode = mode
        self._vram_cap_gib = vram_cap_gib
        self._activation_reserve_gib = activation_reserve_gib
        self._fragmentation_margin_gib = fragmentation_margin_gib
        self._debug = debug
        self._lock = asyncio.Lock()
        if mode is ResidencyMode.DEDICATED and len(self._models) != 1:
            raise ValueError("Dedicated residency requires exactly one managed model")
        if mode is ResidencyMode.CO_RESIDENT and not self.can_co_reside():
            raise ValueError("Configured models exceed the co-resident VRAM budget")

    @property
    def effective_mode(self) -> ResidencyMode:
        if self._configured_mode is not ResidencyMode.AUTO:
            return self._configured_mode
        if self.can_co_reside():
            return ResidencyMode.CO_RESIDENT
        return ResidencyMode.SWAPPING

    def required_vram_gib(self) -> float:
        model_vram = sum(model.resident_vram_gib for model in self._models.values())
        return (
            model_vram + self._activation_reserve_gib + self._fragmentation_margin_gib
        )

    def can_co_reside(self) -> bool:
        return self.required_vram_gib() <= self._vram_cap_gib

    async def prepare(self) -> None:
        for model in self._models.values():
            await model.prepare_cpu()

    async def ensure_gpu(self, target: ModelKind) -> None:
        async with self._lock:
            model = self._models[target]
            if model.state is ModelState.GPU_READY:
                return

            if self.effective_mode is ResidencyMode.CO_RESIDENT:
                await self._activate(model)
                return

            active = [
                candidate
                for candidate in self._models.values()
                if candidate.state is ModelState.GPU_READY
                and candidate.kind is not target
            ]
            for candidate in active:
                await candidate.offload_cpu()

            try:
                await self._activate(model)
            except Exception as exc:
                await self._restore(active)
                raise ResidencyTransitionError(
                    f"Could not activate {target.value} model"
                ) from exc

    @staticmethod
    async def _activate(model: ManagedModel) -> None:
        await model.load_gpu()
        await model.warmup()

    @staticmethod
    async def _restore(models: list[ManagedModel]) -> None:
        for model in models:
            try:
                await model.load_gpu()
                await model.warmup()
            except Exception:
                continue
