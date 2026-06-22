import asyncio
import time

from app.platform.config import Settings
from app.platform.gpu.residency import ResidencyCoordinator
from app.platform.gpu.types import ModelKind, ResidencyMode
from app.platform.jobs.store import JobStore
from app.platform.jobs.types import JobKind, JobRecord, JobStatus
from app.platform.media.store import MediaStore
from app.services.embeddings.qwen import QwenEmbeddingEngine
from app.services.reranking.qwen import QwenRerankingEngine
from app.services.runtime.media_inputs import MediaInputResolver
from app.services.runtime.types import EmbeddingJobPayload, RerankJobPayload
from app.services.runtime.vector import cosine


class JobExecutor:
    def __init__(
        self,
        settings: Settings,
        media_store: MediaStore,
        job_store: JobStore,
        debug: bool = False,
    ) -> None:
        self.settings = settings
        self.media_store = media_store
        self.job_store = job_store
        self.debug = debug
        self.resolver = MediaInputResolver(media_store, debug)
        self._gpu_lock = asyncio.Lock()
        self._embedding = QwenEmbeddingEngine(
            settings.embedding_model_id,
            settings.embedding_model_revision,
            settings.embedding_model_vram_gib,
            settings.embedding_max_length,
            settings.embedding_max_frames,
            settings.embedding_video_fps,
            debug,
        )
        self._reranker = QwenRerankingEngine(
            settings.reranking_model_id,
            settings.reranking_model_revision,
            settings.reranking_model_vram_gib,
            settings.reranking_max_length,
            settings.reranking_max_frames,
            settings.reranking_video_fps,
            debug,
        )
        self._residency = ResidencyCoordinator(
            {
                ModelKind.EMBEDDING: self._embedding,
                ModelKind.RERANKING: self._reranker,
            },
            ResidencyMode(settings.gpu_residency_mode),
            settings.gpu_vram_cap_gib,
            settings.gpu_activation_reserve_gib,
            settings.gpu_fragmentation_margin_gib,
            debug,
        )

    async def execute(self, record: JobRecord) -> dict:
        if record.kind is JobKind.EMBEDDING:
            return await self._embedding_job(record)
        if record.kind is JobKind.RERANKING:
            return await self._rerank_job(record)
        raise ValueError("Unsupported job kind")

    async def _embedding_job(self, record: JobRecord) -> dict:
        payload = EmbeddingJobPayload.model_validate(record.payload)
        await self.job_store.update(
            record.id, JobStatus.RESOLVING_MEDIA, 12, "Resolving media"
        )
        started = time.perf_counter()
        qwen_inputs, metadata = self.resolver.expand_embedding_inputs(payload.input)
        query_input = (
            self.resolver.resolve_for_qwen(payload.query) if payload.query else None
        )
        await self.job_store.update(record.id, JobStatus.EMBEDDING, 45, "Embedding")
        async with self._gpu_lock:
            await self._residency.ensure_gpu(ModelKind.EMBEDDING)
            vectors = await self._embedding.embed(qwen_inputs, payload.dimensions)
            query_vector = (
                (await self._embedding.embed([query_input], payload.dimensions))[0]
                if query_input
                else None
            )
        latency_ms = int((time.perf_counter() - started) * 1000)
        items = self._score_embedding_items(metadata, vectors, query_vector, latency_ms)
        if query_vector:
            items.sort(key=lambda item: item["score"] or 0, reverse=True)
            items = items[: payload.top_k]
        return {
            "items": items,
            "count": len(items),
            "dimensions": payload.dimensions,
            "latency_ms": latency_ms,
        }

    async def _rerank_job(self, record: JobRecord) -> dict:
        payload = RerankJobPayload.model_validate(record.payload)
        await self.job_store.update(
            record.id, JobStatus.RESOLVING_MEDIA, 20, "Resolving media"
        )
        started = time.perf_counter()
        query = self.resolver.resolve_for_qwen(payload.query)
        documents = [self.resolver.resolve_for_qwen(item) for item in payload.documents]
        await self.job_store.update(record.id, JobStatus.RERANKING, 55, "Reranking")
        async with self._gpu_lock:
            await self._residency.ensure_gpu(ModelKind.RERANKING)
            scores = await self._reranker.rerank(
                query,
                documents,
                payload.instruction,
                payload.sampling.fps if payload.sampling else None,
                payload.sampling.max_frames if payload.sampling else None,
            )
        latency_ms = int((time.perf_counter() - started) * 1000)
        items = [
            {
                "id": f"item_{index}",
                "type": document.type,
                "score": float(score),
                "rerank_score": float(score),
                "text": document.text,
                "media_id": document.media_id,
                "segment": document.segment,
                "latency_ms": latency_ms,
            }
            for index, (document, score) in enumerate(
                zip(payload.documents, scores, strict=False)
            )
        ]
        items.sort(key=lambda item: item["score"], reverse=True)
        return {
            "items": items[: payload.top_k],
            "count": len(items),
            "latency_ms": latency_ms,
        }

    @staticmethod
    def _score_embedding_items(
        metadata: list[dict],
        vectors: list[list[float]],
        query_vector: list[float] | None,
        latency_ms: int,
    ) -> list[dict]:
        items = []
        for item, vector in zip(metadata, vectors, strict=False):
            score = cosine(query_vector, vector) if query_vector else None
            items.append(
                {
                    **item,
                    "score": score,
                    "latency_ms": latency_ms,
                }
            )
        return items
