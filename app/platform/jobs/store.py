import asyncio
import time
from collections import deque
from collections.abc import Awaitable, Callable

from app.platform.jobs.types import JobKind, JobRecord, JobStatus

JobHandler = Callable[[JobRecord], Awaitable[dict]]


class InMemoryJobStore:
    def __init__(self, debug: bool = False) -> None:
        self.debug = debug
        self._jobs: dict[str, JobRecord] = {}
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._recent: deque[str] = deque(maxlen=1000)
        self._worker: asyncio.Task | None = None
        self._handler: JobHandler | None = None

    def configure(self, handler: JobHandler) -> None:
        self._handler = handler

    def start(self) -> None:
        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._worker is None:
            return
        self._worker.cancel()
        try:
            await self._worker
        except asyncio.CancelledError:
            pass

    async def create(self, kind: JobKind, payload: dict) -> JobRecord:
        record = JobRecord(kind=kind, payload=payload)
        self._jobs[record.id] = record
        self._recent.appendleft(record.id)
        await self._queue.put(record.id)
        return record

    def get(self, job_id: str) -> JobRecord:
        record = self._jobs.get(job_id)
        if record is None:
            raise KeyError(job_id)
        return record

    def update(
        self,
        job_id: str,
        status: JobStatus,
        progress: int,
        stage_label: str,
    ) -> None:
        record = self.get(job_id)
        record.status = status
        record.progress = max(0, min(100, progress))
        record.stage_label = stage_label
        record.updated_at = time.time()

    async def _run(self) -> None:
        while True:
            job_id = await self._queue.get()
            record = self.get(job_id)
            record.started_at = time.time()
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
                self._queue.task_done()


def safe_error(exc: Exception) -> str:
    if isinstance(exc, (ValueError, KeyError, RuntimeError)):
        return str(exc).strip("'") or "Request failed"
    return "Internal job execution failed"
