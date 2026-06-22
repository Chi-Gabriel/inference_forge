import json
import subprocess
from pathlib import Path


def probe_media(path: Path, debug: bool = False) -> dict[str, float | int | str | None]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=True)
    payload = json.loads(completed.stdout)
    video_stream = next(
        (
            stream
            for stream in payload.get("streams", [])
            if stream.get("codec_type") == "video"
        ),
        {},
    )
    duration = payload.get("format", {}).get("duration") or video_stream.get("duration")
    return {
        "duration_seconds": float(duration) if duration else None,
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
    }


def cut_video_segment(
    source: Path,
    target: Path,
    start_seconds: float,
    duration_seconds: float,
    debug: bool = False,
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-ss",
        str(start_seconds),
        "-i",
        str(source),
        "-t",
        str(duration_seconds),
        "-c",
        "copy",
        str(target),
    ]
    try:
        subprocess.run(command, capture_output=not debug, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip().splitlines()
        message = detail[-1] if detail else "FFmpeg failed to cut video segment"
        raise ValueError(message) from exc
