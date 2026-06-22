import base64
import concurrent.futures
import hashlib
import os
import time

from app.platform.config import Settings
from app.platform.media.store import MediaStore
from app.platform.media.types import MediaKind, MediaRecord

PIXEL = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8A"
    "AwMCAO+/p9sAAAAASUVORK5CYII="
)


def test_media_store_rebuilds_existing_hash_ids(tmp_path) -> None:
    uploads = tmp_path / "uploads"
    uploads.mkdir(parents=True)
    media_file = uploads / "media_existing.png"
    media_file.write_bytes(base64.b64decode(PIXEL))
    settings = Settings(media_root=tmp_path)

    store = MediaStore(settings)
    record = next(iter(store._records.values()))

    assert store.get(record.id).sha256 == record.sha256
    assert record.id.startswith("media_")


def test_media_cleanup_removes_expired_temp_and_decoded_files(tmp_path) -> None:
    settings = Settings(
        media_root=tmp_path,
        media_temp_ttl_hours=1,
        media_decoded_ttl_hours=1,
    )
    store = MediaStore(settings)
    old_time = time.time() - 7200
    temp_file = store.paths.temp / "old.tmp"
    decoded_file = store.paths.decoded / "media_a" / "old.mp4"
    decoded_file.parent.mkdir(parents=True)
    temp_file.write_text("old")
    decoded_file.write_text("old")
    for path in [temp_file, decoded_file]:
        path.touch()
        os.utime(path, (old_time, old_time))

    removed = store.cleanup()

    assert removed["temp"] == 1
    assert removed["decoded"] == 1
    assert not temp_file.exists()
    assert not decoded_file.exists()


def test_media_cleanup_removes_expired_indexed_upload(tmp_path) -> None:
    settings = Settings(media_root=tmp_path, media_upload_ttl_hours=1)
    store = MediaStore(settings)
    upload = store.paths.uploads / "media_test.png"
    upload.write_bytes(base64.b64decode(PIXEL))
    record = MediaRecord(
        id="media_test",
        kind=MediaKind.IMAGE,
        content_type="image/png",
        sha256="abc",
        size_bytes=upload.stat().st_size,
        path=upload,
    )
    store._records[record.id] = record
    store._by_hash[record.sha256] = record.id
    old_time = time.time() - 7200

    os.utime(upload, (old_time, old_time))

    removed = store.cleanup()

    assert removed["uploads"] == 1
    assert record.id not in store._records
    assert record.sha256 not in store._by_hash


def test_extractor_url_can_be_disabled(tmp_path) -> None:
    settings = Settings(media_root=tmp_path, media_extractor_enabled=False)
    store = MediaStore(settings)

    try:
        store.download_url("https://www.youtube.com/watch?v=abc")
    except ValueError as exc:
        assert "disabled" in str(exc)
    else:
        raise AssertionError("extractor URL should be rejected when disabled")


def test_same_source_url_downloads_are_locked(tmp_path, monkeypatch) -> None:
    settings = Settings(media_root=tmp_path)
    store = MediaStore(settings)
    payload = base64.b64decode(PIXEL)
    digest = hashlib.sha256(payload).hexdigest()
    calls = 0

    def fake_download(url, temp_root, settings):
        nonlocal calls
        calls += 1
        time.sleep(0.05)
        temp = temp_root / f"direct-{calls}.png"
        temp.write_bytes(payload)
        return temp, "image/png", digest, len(payload)

    monkeypatch.setattr("app.platform.media.store.download_direct_url", fake_download)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(store.download_url, "https://example.com/test.png")
            for _ in range(2)
        ]
        records = [future.result() for future in futures]

    assert calls == 1
    assert records[0].id == records[1].id


def test_preview_does_not_touch_original_file(tmp_path, monkeypatch) -> None:
    settings = Settings(media_root=tmp_path)
    store = MediaStore(settings)
    video = store.paths.downloads / "media_test.mp4"
    video.write_bytes(b"fake")
    record = MediaRecord(
        id="media_test",
        kind=MediaKind.VIDEO,
        content_type="video/mp4",
        sha256="abc",
        size_bytes=4,
        path=video,
    )
    store._records[record.id] = record
    old_time = time.time() - 7200
    os.utime(video, (old_time, old_time))
    monkeypatch.setattr(
        "app.platform.media.browser_preview._video_codec", lambda path: "h264"
    )

    store.preview(record.id)

    assert video.stat().st_mtime == old_time
