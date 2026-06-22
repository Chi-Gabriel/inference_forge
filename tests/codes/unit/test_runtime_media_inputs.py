from app.platform.config import Settings
from app.platform.media.store import MediaStore
from app.platform.media.types import MediaKind, MediaRecord
from app.services.runtime.media_inputs import MediaInputResolver
from app.services.runtime.types import (
    MultimodalInput,
    SamplingOptions,
    SegmentationOptions,
)


def test_video_segment_path_preserves_mp4_extension(tmp_path) -> None:
    store = MediaStore(Settings(media_root=tmp_path))
    resolver = MediaInputResolver(store)
    record = MediaRecord(
        id="media_test",
        kind=MediaKind.VIDEO,
        content_type="video/mp4",
        sha256="abc",
        size_bytes=1,
        path=tmp_path / "downloads" / "media_test.mp4",
        duration_seconds=10,
    )

    path = resolver._segment_path(record, 0, 10, SamplingOptions(fps=1, max_frames=16))

    assert path.name == "media_test_0p000_10p000_1p00_16.mp4"


def test_qwen_video_input_uses_absolute_path(tmp_path) -> None:
    store = MediaStore(Settings(media_root=tmp_path))
    resolver = MediaInputResolver(store)
    video = tmp_path / "downloads" / "media_test.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"fake")
    record = MediaRecord(
        id="media_test",
        kind=MediaKind.VIDEO,
        content_type="video/mp4",
        sha256="abc",
        size_bytes=4,
        path=video,
        duration_seconds=10,
    )
    store._records[record.id] = record

    qwen_input = resolver.resolve_for_qwen(
        MultimodalInput(type="video", media_id=record.id)
    )

    assert qwen_input["video"].startswith("/")


def test_video_segmentation_skips_tiny_tail(tmp_path, monkeypatch) -> None:
    store = MediaStore(Settings(media_root=tmp_path))
    resolver = MediaInputResolver(store)
    video = tmp_path / "downloads" / "media_test.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    video.write_bytes(b"fake")
    record = MediaRecord(
        id="media_test",
        kind=MediaKind.VIDEO,
        content_type="video/mp4",
        sha256="abc",
        size_bytes=4,
        path=video,
        duration_seconds=21,
    )

    def fake_cut(source, target, start_seconds, duration_seconds, debug=False):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"segment")

    monkeypatch.setattr("app.services.runtime.media_inputs.cut_video_segment", fake_cut)

    segments = resolver.segment_video(
        record,
        SegmentationOptions(chunk_seconds=10, overlap_seconds=0),
        SamplingOptions(fps=1, max_frames=4),
    )

    assert [(item.start_seconds, item.end_seconds) for item in segments] == [
        (0, 10),
        (10, 20),
    ]
