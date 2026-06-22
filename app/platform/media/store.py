import hashlib
import mimetypes
import shutil
import time
from pathlib import Path
from urllib.parse import urlparse

from fastapi import UploadFile

from app.platform.config import Settings
from app.platform.media.direct import download_direct_url
from app.platform.media.extractor import download_with_ytdlp, is_extractor_url
from app.platform.media.probe import probe_media
from app.platform.media.source_index import SourceUrlIndex
from app.platform.media.types import MediaKind, MediaRecord
from app.platform.storage.paths import StoragePaths

CHUNK_SIZE = 1024 * 1024
EXTENSIONS_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
}


class MediaStore:
    def __init__(self, settings: Settings, debug: bool = False) -> None:
        self.settings = settings
        self.paths = StoragePaths(settings.media_root)
        self.debug = debug
        self._records: dict[str, MediaRecord] = {}
        self._by_hash: dict[str, str] = {}
        self._sources = SourceUrlIndex()
        self.paths.ensure()
        self._load_existing()

    async def save_upload(self, upload: UploadFile) -> MediaRecord:
        content_type = upload.content_type or "application/octet-stream"
        self._validate_content_type(content_type)
        temp = self.paths.temp / f"upload-{id(upload)}"
        sha256 = hashlib.sha256()
        size = 0
        with temp.open("wb") as target:
            while chunk := await upload.read(CHUNK_SIZE):
                size += len(chunk)
                if size > self.settings.media_upload_max_bytes:
                    temp.unlink(missing_ok=True)
                    raise ValueError("Uploaded media exceeds the configured size limit")
                sha256.update(chunk)
                target.write(chunk)
        digest = sha256.hexdigest()
        return self._commit(temp, content_type, digest, size, self.paths.uploads)

    def download_url(self, url: str) -> MediaRecord:
        cached = self._sources.get(url)
        if cached is not None:
            return self.get(cached)
        with self._sources.lock(url):
            cached = self._sources.get(url)
            if cached is not None:
                return self.get(cached)
            return self._download_uncached_url(url)

    def _download_uncached_url(self, url: str) -> MediaRecord:
        allowed = self.settings.media_extractor_allowed_hosts
        if is_extractor_url(url, allowed):
            return self._download_extractor_url(url)
        self._validate_direct_url(url)
        temp, content_type, digest, size = download_direct_url(
            url, self.paths.temp, self.settings
        )
        self._validate_content_type(content_type)
        return self._commit(
            temp, content_type, digest, size, self.paths.downloads, source_url=url
        )

    def _download_extractor_url(self, url: str) -> MediaRecord:
        if not self.settings.media_extractor_enabled:
            raise ValueError("Extractor-backed media URLs are disabled")
        temp, content_type = download_with_ytdlp(url, self.paths.temp, self.settings)
        self._validate_content_type(content_type)
        sha256 = hashlib.sha256()
        size = 0
        with temp.open("rb") as source:
            while chunk := source.read(CHUNK_SIZE):
                size += len(chunk)
                sha256.update(chunk)
        return self._commit(
            temp,
            content_type,
            sha256.hexdigest(),
            size,
            self.paths.downloads,
            source_url=url,
        )

    def get(self, media_id: str) -> MediaRecord:
        record = self._records.get(media_id)
        if record is None:
            raise KeyError(media_id)
        record.path.touch(exist_ok=True)
        return record

    def cleanup(self, now: float | None = None) -> dict[str, int]:
        current = now or time.time()
        removed = {
            "uploads": self._cleanup_indexed_dir(
                self.paths.uploads, self.settings.media_upload_ttl_hours, current
            ),
            "downloads": self._cleanup_indexed_dir(
                self.paths.downloads, self.settings.media_download_ttl_hours, current
            ),
            "temp": self._cleanup_dir(
                self.paths.temp, self.settings.media_temp_ttl_hours, current
            ),
            "decoded": self._cleanup_dir(
                self.paths.decoded, self.settings.media_decoded_ttl_hours, current
            ),
            "cache": self._cleanup_dir(
                self.paths.cache, self.settings.media_cache_ttl_hours, current
            ),
        }
        self._prune_empty_dirs(self.paths.decoded)
        self._prune_empty_dirs(self.paths.cache)
        return removed

    def _commit(
        self,
        temp: Path,
        content_type: str,
        sha256: str,
        size: int,
        directory: Path,
        source_url: str | None = None,
    ) -> MediaRecord:
        if sha256 in self._by_hash:
            temp.unlink(missing_ok=True)
            record = self._records[self._by_hash[sha256]]
            if source_url:
                self._sources.set(source_url, record.id)
            return record
        extension = EXTENSIONS_BY_TYPE.get(content_type, "")
        media_id = f"media_{sha256[:24]}"
        target = directory / f"{media_id}{extension}"
        shutil.move(str(temp), target)
        kind = MediaKind.VIDEO if content_type.startswith("video/") else MediaKind.IMAGE
        metadata = probe_media(target, self.debug) if kind is MediaKind.VIDEO else {}
        record = MediaRecord(
            id=media_id,
            kind=kind,
            content_type=content_type,
            sha256=sha256,
            size_bytes=size,
            path=target,
            source_url=source_url,
            **metadata,
        )
        self._records[media_id] = record
        self._by_hash[sha256] = media_id
        if source_url:
            self._sources.set(source_url, media_id)
        return record

    def _validate_content_type(self, content_type: str) -> None:
        if content_type not in self.settings.media_allowed_content_types:
            raise ValueError("Unsupported media content type")

    def _validate_direct_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Only http and https media URLs are supported")

    def _load_existing(self) -> None:
        for directory in [self.paths.uploads, self.paths.downloads]:
            for path in directory.iterdir():
                if path.is_file():
                    self._index_existing(path)

    def _cleanup_indexed_dir(
        self, directory: Path, ttl_hours: float, now: float
    ) -> int:
        removed = 0
        for path in directory.iterdir():
            if not path.is_file() or not self._expired(path, ttl_hours, now):
                continue
            record = self._record_for_path(path)
            path.unlink(missing_ok=True)
            removed += 1
            if record is not None:
                self._records.pop(record.id, None)
                self._by_hash.pop(record.sha256, None)
                if record.source_url:
                    self._sources.pop(record.source_url)
        return removed

    def _cleanup_dir(self, directory: Path, ttl_hours: float, now: float) -> int:
        removed = 0
        for path in directory.rglob("*"):
            if path.is_file() and self._expired(path, ttl_hours, now):
                path.unlink(missing_ok=True)
                removed += 1
        return removed

    def _record_for_path(self, path: Path) -> MediaRecord | None:
        for record in self._records.values():
            if record.path == path:
                return record
        return None

    @staticmethod
    def _expired(path: Path, ttl_hours: float, now: float) -> bool:
        return now - path.stat().st_mtime > ttl_hours * 3600

    def _prune_empty_dirs(self, directory: Path) -> None:
        for path in sorted(directory.rglob("*"), reverse=True):
            if path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    continue

    def _index_existing(self, path: Path) -> None:
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if content_type not in self.settings.media_allowed_content_types:
            return
        sha256 = hashlib.sha256()
        size = 0
        with path.open("rb") as source:
            while chunk := source.read(CHUNK_SIZE):
                size += len(chunk)
                sha256.update(chunk)
        digest = sha256.hexdigest()
        media_id = f"media_{digest[:24]}"
        kind = MediaKind.VIDEO if content_type.startswith("video/") else MediaKind.IMAGE
        metadata = probe_media(path, self.debug) if kind is MediaKind.VIDEO else {}
        record = MediaRecord(
            id=media_id,
            kind=kind,
            content_type=content_type,
            sha256=digest,
            size_bytes=size,
            path=path,
            **metadata,
        )
        self._records[media_id] = record
        self._by_hash[digest] = media_id
