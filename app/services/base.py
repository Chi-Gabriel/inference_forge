from typing import Protocol, TypeVar

from app.platform.gpu.types import ModelKind

PayloadT = TypeVar("PayloadT")
ResultT = TypeVar("ResultT")


class BatchInferenceService(Protocol[PayloadT, ResultT]):
    kind: ModelKind

    async def infer(self, items: list[PayloadT]) -> list[ResultT]: ...
