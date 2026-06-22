import hashlib
import mimetypes
import shutil
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from fastapi import UploadFile

from app.platform.config import Settings
from app.platform.media.probe import probe_media
from app.platform.media.types import MediaKind, MediaRecord
from app.platform.storage.paths import StoragePaths

CHUNK_SIZE = 1024 * 1024
EXTRACTOR_HOST_HINTS = ("youtube.", "youtu.be", "tiktok.", "facebook.", "fb.watch")
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
        return self._commit(
            temp, content_type, sha256.hexdigest(), size, self.paths.uploads
        )

    def download_url(self, url: str) -> MediaRecord:
        self._validate_direct_url(url)
        request = urllib.request.Request(
            url, headers={"User-Agent": "InferenceForge/0.1"}
        )
        opener = urllib.request.build_opener(
            LimitedRedirectHandler(self.settings.media_download_redirect_limit)
        )
        try:
            with opener.open(
                request, timeout=self.settings.media_download_timeout_seconds
            ) as response:
                content_type = response.headers.get_content_type()
                self._validate_content_type(content_type)
                temp = (
                    self.paths.temp
                    / f"download-{hashlib.sha256(url.encode()).hexdigest()}"
                )
                sha256 = hashlib.sha256()
                size = 0
                with temp.open("wb") as target:
                    while True:
                        chunk = response.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > self.settings.media_download_max_bytes:
                            temp.unlink(missing_ok=True)
                            raise ValueError(
                                "Downloaded media exceeds the configured size limit"
                            )
                        sha256.update(chunk)
                        target.write(chunk)
        except urllib.error.URLError as exc:
            raise ValueError("Media download failed") from exc
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
        return record

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
            return self._records[self._by_hash[sha256]]
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
        return record

    def _validate_content_type(self, content_type: str) -> None:
        if content_type not in self.settings.media_allowed_content_types:
            raise ValueError("Unsupported media content type")

    def _validate_direct_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Only http and https media URLs are supported")
        host = parsed.netloc.lower()
        if any(hint in host for hint in EXTRACTOR_HOST_HINTS):
            raise ValueError("Extractor-backed media URLs are not enabled yet")

    def _load_existing(self) -> None:
        for directory in [self.paths.uploads, self.paths.downloads]:
            for path in directory.iterdir():
                if path.is_file():
                    self._index_existing(path)

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


class LimitedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.redirects = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirects += 1
        if self.redirects > self.limit:
            raise urllib.error.HTTPError(
                req.full_url,
                code,
                "Too many redirects",
                headers,
                fp,
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)
