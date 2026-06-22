from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class EmbeddingRequestItem:
    value: str | dict[str, Any]
