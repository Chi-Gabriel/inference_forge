import asyncio
import time
from collections.abc import Awaitable, Callable

import redis

from app.platform.jobs.store import safe_error
from app.platform.jobs.types import JobKind, JobRecord, JobStatus

JobHandler = Callable[[JobRecord], Awaitable[dict]]
TERMINAL_STATUSES = {JobStatus.COMPLETE, JobStatus.FAILED}


class RedisJobStore:
    def __init__(
        self,
        redis_url: str,
        prefix: str,
        block_seconds: int,
        job_ttl_hours: float,
        debug: bool = False,
    ) -> None:
        self.debug = debug
        self._redis = redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
        self._prefix = prefix.rstrip(":")
        self._block_seconds = block_seconds
        self._job_ttl_seconds = int(job_ttl_hours * 3600)
        self._handler: JobHandler | None = None
        self._worker: asyncio.Task | None = None
        self._stopping = False

    def configure(self, handler: JobHandler) -> None:
        self._handler = handler

    def start(self) -> None:
        self._stopping = False
        self._recover_unfinished_jobs()
        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._worker is None:
            return
        self._stopping = True
        self._worker.cancel()
        try:
            await self._worker
        except asyncio.CancelledError:
            pass
        await asyncio.to_thread(self._redis.close)

    async def create(self, kind: JobKind, payload: dict) -> JobRecord:
        record = JobRecord(kind=kind, payload=payload)
        await asyncio.to_thread(self._save, record)
        await asyncio.to_thread(self._redis.rpush, self._queue_key, record.id)
        return record

    async def get(self, job_id: str) -> JobRecord:
        data = await asyncio.to_thread(self._redis.get, self._job_key(job_id))
        if data is None:
            raise KeyError(job_id)
        return JobRecord.model_validate_json(data)

    async def update(
        self,
        job_id: str,
        status: JobStatus,
        progress: int,
        stage_label: str,
    ) -> None:
        record = await self.get(job_id)
        record.status = status
        record.progress = max(0, min(100, progress))
        record.stage_label = stage_label
        record.updated_at = time.time()
        await asyncio.to_thread(self._save, record)

    async def cleanup(self, now: float | None = None) -> int:
        current = now or time.time()
        return await asyncio.to_thread(self._cleanup_terminal_jobs, current)

    def ping(self) -> None:
        self._redis.ping()

    async def _run(self) -> None:
        while True:
            try:
                item = await asyncio.to_thread(
                    self._redis.blpop,
                    self._queue_key,
                    self._block_seconds,
                )
            except redis.exceptions.TimeoutError:
                if self._stopping:
                    return
                continue
            if item is None:
                continue
            job_id = item[1]
            record = await self.get(job_id)
            if record.status in TERMINAL_STATUSES:
                continue
            record.started_at = time.time()
            await asyncio.to_thread(self._save, record)
            try:
                if self._handler is None:
                    raise RuntimeError("Job handler is not configured")
                result = await self._handler(record)
                now = time.time()
                record.status = JobStatus.COMPLETE
                record.progress = 100
                record.stage_label = "Complete"
                record.completed_at = now
                record.updated_at = now
                record.elapsed_ms = int((now - (record.started_at or now)) * 1000)
                record.result = result
            except Exception as exc:
                now = time.time()
                record.status = JobStatus.FAILED
                record.progress = 0
                record.stage_label = "Failed"
                record.error = safe_error(exc)
                record.completed_at = now
                record.updated_at = now
                record.elapsed_ms = int((now - (record.started_at or now)) * 1000)
            finally:
                await asyncio.to_thread(self._save, record)

    def _recover_unfinished_jobs(self) -> None:
        for key in self._redis.scan_iter(f"{self._prefix}:job:*"):
            data = self._redis.get(key)
            if data is None:
                continue
            record = JobRecord.model_validate_json(data)
            if record.status in TERMINAL_STATUSES:
                continue
            record.status = JobStatus.QUEUED
            record.progress = 0
            record.stage_label = "Queued after restart"
            record.updated_at = time.time()
            self._save(record)
            self._redis.rpush(self._queue_key, record.id)

    def _save(self, record: JobRecord) -> None:
        key = self._job_key(record.id)
        if record.status in TERMINAL_STATUSES and record.completed_at is not None:
            self._redis.setex(key, self._job_ttl_seconds, record.model_dump_json())
            return
        self._redis.set(key, record.model_dump_json())

    def _cleanup_terminal_jobs(self, now: float) -> int:
        removed = 0
        for key in self._redis.scan_iter(f"{self._prefix}:job:*"):
            data = self._redis.get(key)
            if data is None:
                continue
            record = JobRecord.model_validate_json(data)
            if record.status not in TERMINAL_STATUSES or record.completed_at is None:
                continue
            if now - record.completed_at > self._job_ttl_seconds:
                removed += self._redis.delete(key)
        return removed

    @property
    def _queue_key(self) -> str:
        return f"{self._prefix}:jobs:queue"

    def _job_key(self, job_id: str) -> str:
        return f"{self._prefix}:job:{job_id}"
