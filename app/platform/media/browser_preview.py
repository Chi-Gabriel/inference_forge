import json
import subprocess
from pathlib import Path

from app.platform.media.types import MediaKind, MediaRecord
from app.platform.storage.paths import StoragePaths

VIDEO_CODEC_BROWSER_SAFE = {"h264", "avc1", "vp8", "vp9", "av1"}


def browser_preview(
    record: MediaRecord, paths: StoragePaths, debug: bool
) -> tuple[Path, str]:
    if record.kind is MediaKind.IMAGE:
        return record.path, record.content_type
    codec = _video_codec(record.path)
    if codec in VIDEO_CODEC_BROWSER_SAFE:
        return record.path, record.content_type
    target = paths.cache / "browser-preview" / f"{record.id}.mp4"
    if not target.exists() or target.stat().st_mtime < record.path.stat().st_mtime:
        _transcode_video(record.path, target, debug)
    return target, "video/mp4"


def _video_codec(path: Path) -> str | None:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name",
        str(path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=True)
    payload = json.loads(completed.stdout or "{}")
    streams = payload.get("streams") or []
    if not streams:
        return None
    codec = streams[0].get("codec_name")
    return str(codec).lower() if codec else None


def _transcode_video(source: Path, target: Path, debug: bool) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp.mp4")
    command = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",
        "-an",
        "-movflags",
        "+faststart",
        str(temporary),
    ]
    subprocess.run(command, capture_output=not debug, text=True, check=True)
    temporary.replace(target)
