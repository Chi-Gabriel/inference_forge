import time

from app.platform.jobs.store import InMemoryJobStore
from app.platform.jobs.types import JobKind, JobStatus


async def test_in_memory_job_cleanup_removes_expired_terminal_jobs() -> None:
    store = InMemoryJobStore(job_ttl_hours=1)
    record = await store.create(JobKind.EMBEDDING, {"input": []})
    record.status = JobStatus.COMPLETE
    record.completed_at = time.time() - 7200

    removed = await store.cleanup()

    assert removed == 1
    try:
        await store.get(record.id)
    except KeyError:
        pass
    else:
        raise AssertionError("expired job should be removed")
