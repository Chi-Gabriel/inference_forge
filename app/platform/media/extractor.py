import hashlib
import mimetypes
import shutil
import uuid
from pathlib import Path
from urllib.parse import urlparse

from app.platform.config import Settings


def is_extractor_url(url: str, allowed_hosts: list[str]) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower().split("@")[-1].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    return any(
        host == allowed or host.endswith(f".{allowed}") for allowed in allowed_hosts
    )


def download_with_ytdlp(
    url: str, temp_root: Path, settings: Settings
) -> tuple[Path, str]:
    from yt_dlp import YoutubeDL
    from yt_dlp.utils import DownloadError

    source_key = hashlib.sha256(url.encode()).hexdigest()[:24]
    work_dir = temp_root / f"extractor-{source_key}-{uuid.uuid4().hex[:12]}"
    work_dir.mkdir(parents=True, exist_ok=True)
    before = {path for path in work_dir.rglob("*") if path.is_file()}
    options = {
        "format": settings.media_extractor_format,
        "outtmpl": str(work_dir / "%(extractor_key)s-%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "socket_timeout": settings.media_extractor_timeout_seconds,
        "max_filesize": settings.media_download_max_bytes,
        "noprogress": not settings.app_debug,
        "quiet": not settings.app_debug,
        "no_warnings": not settings.app_debug,
        "match_filter": _duration_filter(settings.media_extractor_max_duration_seconds),
    }
    try:
        with YoutubeDL(options) as downloader:
            downloader.extract_info(url, download=True)
    except DownloadError as exc:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise ValueError("Extractor media download failed") from exc
    candidates = [
        path
        for path in work_dir.rglob("*")
        if path.is_file() and path not in before and not path.name.endswith(".part")
    ]
    if not candidates:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise ValueError("Extractor did not produce a media file")
    media_path = max(candidates, key=lambda path: path.stat().st_size)
    if media_path.stat().st_size > settings.media_download_max_bytes:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise ValueError("Extracted media exceeds the configured size limit")
    content_type = mimetypes.guess_type(media_path.name)[0] or "video/mp4"
    return media_path, content_type


def _duration_filter(max_duration_seconds: int):
    def check(info: dict, *, incomplete: bool = False) -> str | None:
        duration = info.get("duration")
        if duration is not None and duration > max_duration_seconds:
            return "Extracted media exceeds the configured duration limit"
        return None

    return check
