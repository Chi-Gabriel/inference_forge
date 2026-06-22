from app.platform.media.browser_preview import browser_preview
from app.platform.media.types import MediaKind, MediaRecord
from app.platform.storage.paths import StoragePaths


def test_image_preview_uses_original_file(tmp_path) -> None:
    paths = StoragePaths(tmp_path)
    paths.ensure()
    image = paths.uploads / "media_test.png"
    image.write_bytes(b"fake")
    record = MediaRecord(
        id="media_test",
        kind=MediaKind.IMAGE,
        content_type="image/png",
        sha256="abc",
        size_bytes=4,
        path=image,
    )

    path, content_type = browser_preview(record, paths, False)

    assert path == image
    assert content_type == "image/png"


def test_browser_safe_video_preview_uses_original_file(tmp_path, monkeypatch) -> None:
    paths = StoragePaths(tmp_path)
    paths.ensure()
    video = paths.downloads / "media_test.mp4"
    video.write_bytes(b"fake")
    record = MediaRecord(
        id="media_test",
        kind=MediaKind.VIDEO,
        content_type="video/mp4",
        sha256="abc",
        size_bytes=4,
        path=video,
    )
    monkeypatch.setattr(
        "app.platform.media.browser_preview._video_codec", lambda path: "h264"
    )

    path, content_type = browser_preview(record, paths, False)

    assert path == video
    assert content_type == "video/mp4"
