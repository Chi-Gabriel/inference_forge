from app.platform.config import Settings
from app.platform.jobs.redis_store import RedisJobStore
from app.platform.jobs.store import InMemoryJobStore, JobStore


def create_job_store(settings: Settings) -> JobStore:
    if settings.job_store_backend == "memory":
        return InMemoryJobStore(settings.app_debug, settings.job_ttl_hours)
    if settings.job_store_backend in {"auto", "redis"}:
        store = RedisJobStore(
            settings.redis_url,
            settings.job_store_redis_prefix,
            settings.job_store_redis_block_seconds,
            settings.job_ttl_hours,
            settings.app_debug,
        )
        try:
            store.ping()
            return store
        except Exception:
            if settings.job_store_backend == "redis":
                raise
    return InMemoryJobStore(settings.app_debug, settings.job_ttl_hours)
