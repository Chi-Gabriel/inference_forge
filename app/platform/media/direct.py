import hashlib
import urllib.error
import urllib.request
from pathlib import Path

from app.platform.config import Settings

CHUNK_SIZE = 1024 * 1024


def download_direct_url(
    url: str,
    temp_root: Path,
    settings: Settings,
) -> tuple[Path, str, str, int]:
    request = urllib.request.Request(url, headers={"User-Agent": "InferenceForge/0.1"})
    opener = urllib.request.build_opener(
        LimitedRedirectHandler(settings.media_download_redirect_limit)
    )
    try:
        with opener.open(
            request, timeout=settings.media_download_timeout_seconds
        ) as response:
            content_type = response.headers.get_content_type()
            temp = temp_root / f"download-{hashlib.sha256(url.encode()).hexdigest()}"
            sha256 = hashlib.sha256()
            size = 0
            with temp.open("wb") as target:
                while True:
                    chunk = response.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > settings.media_download_max_bytes:
                        temp.unlink(missing_ok=True)
                        raise ValueError(
                            "Downloaded media exceeds the configured size limit"
                        )
                    sha256.update(chunk)
                    target.write(chunk)
    except urllib.error.URLError as exc:
        raise ValueError("Media download failed") from exc
    return temp, content_type, sha256.hexdigest(), size


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
