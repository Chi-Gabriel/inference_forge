import asyncio

from app.platform.config import Settings
from app.platform.jobs.store import JobStore
from app.platform.media.store import MediaStore


class CleanupService:
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
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if not self.settings.cleanup_enabled:
            return
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass

    async def run_once(self) -> dict[str, object]:
        media = await asyncio.to_thread(self.media_store.cleanup)
        jobs = await self.job_store.cleanup()
        return {"media": media, "jobs": jobs}

    async def _run(self) -> None:
        while True:
            try:
                await self.run_once()
            except Exception:
                if self.debug:
                    raise
            await asyncio.sleep(self.settings.cleanup_interval_seconds)
