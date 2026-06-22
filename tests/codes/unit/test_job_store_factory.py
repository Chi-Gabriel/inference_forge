import pytest

from app.platform.config import Settings
from app.platform.jobs.factory import create_job_store
from app.platform.jobs.store import InMemoryJobStore


class FakeRedisStore:
    def __init__(self, *args, fail_ping: bool = False, **kwargs) -> None:
        self.fail_ping = fail_ping

    def ping(self) -> None:
        if self.fail_ping:
            raise RuntimeError("redis unavailable")


def test_memory_backend_uses_in_memory_store(tmp_path) -> None:
    settings = Settings(job_store_backend="memory", media_root=tmp_path)

    store = create_job_store(settings)

    assert isinstance(store, InMemoryJobStore)


def test_auto_backend_falls_back_to_memory_when_redis_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    def make_store(*args, **kwargs) -> FakeRedisStore:
        return FakeRedisStore(fail_ping=True)

    monkeypatch.setattr("app.platform.jobs.factory.RedisJobStore", make_store)
    settings = Settings(job_store_backend="auto", media_root=tmp_path)

    store = create_job_store(settings)

    assert isinstance(store, InMemoryJobStore)


def test_redis_backend_raises_when_redis_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    def make_store(*args, **kwargs) -> FakeRedisStore:
        return FakeRedisStore(fail_ping=True)

    monkeypatch.setattr("app.platform.jobs.factory.RedisJobStore", make_store)
    settings = Settings(job_store_backend="redis", media_root=tmp_path)

    with pytest.raises(RuntimeError, match="redis unavailable"):
        create_job_store(settings)
