import asyncio
from collections.abc import Sequence
from typing import Any

from app.platform.gpu.types import ModelKind, ModelState


class QwenEmbeddingEngine:
    kind = ModelKind.EMBEDDING

    def __init__(
        self,
        model_id: str,
        revision: str,
        resident_vram_gib: float,
        max_length: int = 8192,
        max_frames: int = 16,
        video_fps: float = 1,
        debug: bool = False,
    ) -> None:
        self.model_id = model_id
        self.revision = revision
        self.resident_vram_gib = resident_vram_gib
        self.max_length = max_length
        self.max_frames = max_frames
        self.video_fps = video_fps
        self.debug = debug
        self.state = ModelState.UNLOADED
        self._model: Any | None = None

    async def prepare_cpu(self) -> None:
        if self.state is not ModelState.UNLOADED:
            return
        self._model = await asyncio.to_thread(self._load_model)
        await asyncio.to_thread(self._move_to, "cpu")
        await asyncio.to_thread(self._release_cuda_cache)
        self.state = ModelState.CPU_READY

    async def load_gpu(self) -> None:
        if self.state is ModelState.GPU_READY:
            return
        if self._model is None:
            await self.prepare_cpu()
        self.state = ModelState.GPU_LOADING
        try:
            await asyncio.to_thread(self._move_to, "cuda")
        except Exception:
            self.state = ModelState.FAILED
            raise

    async def warmup(self) -> None:
        if self.state is not ModelState.GPU_LOADING:
            return
        try:
            await asyncio.to_thread(self._encode, ["warmup"], 4096)
            self.state = ModelState.GPU_READY
        except Exception:
            self.state = ModelState.FAILED
            raise

    async def offload_cpu(self) -> None:
        if self.state is not ModelState.GPU_READY:
            return
        self.state = ModelState.CPU_OFFLOADING
        try:
            await asyncio.to_thread(self._move_to, "cpu")
            await asyncio.to_thread(self._release_cuda_cache)
            self.state = ModelState.CPU_READY
        except Exception:
            self.state = ModelState.FAILED
            raise

    async def embed(
        self,
        inputs: Sequence[str | dict[str, Any]],
        dimensions: int = 4096,
    ) -> list[list[float]]:
        if self.state is not ModelState.GPU_READY:
            raise RuntimeError("Embedding model is not GPU ready")
        if not 64 <= dimensions <= 4096:
            raise ValueError("Embedding dimensions must be between 64 and 4096")
        return await asyncio.to_thread(self._encode, list(inputs), dimensions)

    def _load_model(self) -> Any:
        import importlib.util
        import sys

        import torch
        from huggingface_hub import snapshot_download

        snapshot = snapshot_download(repo_id=self.model_id, revision=self.revision)
        script = f"{snapshot}/scripts/qwen3_vl_embedding.py"
        module_name = f"qwen_embedding_{self.revision}"
        spec = importlib.util.spec_from_file_location(module_name, script)
        if spec is None or spec.loader is None:
            raise RuntimeError("Pinned Qwen embedding implementation is unavailable")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module.Qwen3VLEmbedder(
            model_name_or_path=snapshot,
            max_length=self.max_length,
            max_frames=self.max_frames,
            fps=self.video_fps,
            dtype=torch.bfloat16,
            attn_implementation="sdpa",
        )

    def _move_to(self, device: str) -> None:
        if self._model is None:
            raise RuntimeError("Embedding model has not been prepared")
        self._model.model.to(device)

    def _encode(
        self,
        inputs: list[str | dict[str, Any]],
        dimensions: int,
    ) -> list[list[float]]:
        if self._model is None:
            raise RuntimeError("Embedding model has not been prepared")
        import torch.nn.functional as functional

        formatted = []
        for item in inputs:
            value = dict(item) if isinstance(item, dict) else {"text": item}
            if value.get("video") is not None:
                value.setdefault("max_frames", self.max_frames)
                value.setdefault("fps", self.video_fps)
            formatted.append(value)
        embeddings = self._model.process(formatted, normalize=True)
        embeddings = functional.normalize(embeddings[:, :dimensions], p=2, dim=-1)
        return embeddings.float().cpu().tolist()

    @staticmethod
    def _release_cuda_cache() -> None:
        import torch

        if torch.cuda.is_available():
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
