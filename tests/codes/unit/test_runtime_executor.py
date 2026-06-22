from app.platform.config import Settings
from app.platform.jobs.store import InMemoryJobStore
from app.platform.media.store import MediaStore
from app.services.runtime.executor import JobExecutor


def test_embedding_batches_use_video_limit(tmp_path) -> None:
    settings = Settings(media_root=tmp_path, embedding_video_batch_max=4)
    executor = JobExecutor(settings, MediaStore(settings), InMemoryJobStore())
    inputs = [{"video": f"/tmp/{index}.mp4"} for index in range(10)]

    batches = executor._embedding_batches(inputs)

    assert [len(batch) for _, batch in batches] == [4, 4, 2]
