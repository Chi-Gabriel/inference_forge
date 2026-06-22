import base64

from app.platform.config import Settings
from app.platform.media.store import MediaStore

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
