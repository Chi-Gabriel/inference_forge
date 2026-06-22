import asyncio
from collections.abc import Sequence
from typing import Any

from app.platform.gpu.types import ModelKind, ModelState


class QwenRerankingEngine:
    kind = ModelKind.RERANKING

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
            await asyncio.to_thread(
                self._score,
                {"text": "warmup query"},
                [{"text": "warmup document"}],
                None,
                self.video_fps,
                self.max_frames,
            )
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

    async def rerank(
        self,
        query: dict[str, Any],
        documents: Sequence[dict[str, Any]],
        instruction: str | None = None,
        video_fps: float | None = None,
        max_frames: int | None = None,
    ) -> list[float]:
        if self.state is not ModelState.GPU_READY:
            raise RuntimeError("Reranking model is not GPU ready")
        if not documents:
            return []
        return await asyncio.to_thread(
            self._score,
            query,
            list(documents),
            instruction,
            video_fps or self.video_fps,
            max_frames or self.max_frames,
        )

    def _load_model(self) -> Any:
        import importlib.util
        import sys

        import torch
        from huggingface_hub import snapshot_download

        snapshot = snapshot_download(repo_id=self.model_id, revision=self.revision)
        script = f"{snapshot}/scripts/qwen3_vl_reranker.py"
        module_name = f"qwen_reranker_{self.revision}"
        spec = importlib.util.spec_from_file_location(module_name, script)
        if spec is None or spec.loader is None:
            raise RuntimeError("Pinned Qwen reranking implementation is unavailable")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module.Qwen3VLReranker(
            model_name_or_path=snapshot,
            max_length=self.max_length,
            max_frames=self.max_frames,
            fps=self.video_fps,
            dtype=torch.bfloat16,
            attn_implementation="sdpa",
        )

    def _move_to(self, device: str) -> None:
        if self._model is None:
            raise RuntimeError("Reranking model has not been prepared")
        self._model.model.to(device)
        self._model.score_linear.to(device)

    def _score(
        self,
        query: dict[str, Any],
        documents: list[dict[str, Any]],
        instruction: str | None,
        video_fps: float,
        max_frames: int,
    ) -> list[float]:
        if self._model is None:
            raise RuntimeError("Reranking model has not been prepared")
        effective_instruction = instruction or self._model.default_instruction
        pairs = [
            self._model.format_mm_instruction(
                query_text=query.get("text"),
                query_image=query.get("image"),
                query_video=query.get("video"),
                doc_text=document.get("text"),
                doc_image=document.get("image"),
                doc_video=document.get("video"),
                instruction=effective_instruction,
                fps=video_fps,
                max_frames=max_frames,
            )
            for document in documents
        ]
        inputs = self._model.tokenize(pairs).to(self._model.model.device)
        return self._model.compute_scores(inputs)

    @staticmethod
    def _release_cuda_cache() -> None:
        import torch

        if torch.cuda.is_available():
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
