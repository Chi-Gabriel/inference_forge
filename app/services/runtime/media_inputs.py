from pathlib import Path

from app.platform.media.probe import cut_video_segment
from app.platform.media.store import MediaStore
from app.platform.media.types import MediaKind, MediaRecord, VideoSegment
from app.services.runtime.types import (
    MultimodalInput,
    SamplingOptions,
    SegmentationOptions,
)

MIN_TAIL_SEGMENT_SECONDS = 2.0


class MediaInputResolver:
    def __init__(self, media_store: MediaStore, debug: bool = False) -> None:
        self.media_store = media_store
        self.debug = debug

    def resolve_for_qwen(self, item: MultimodalInput) -> dict[str, str]:
        if item.type == "text":
            if not item.text:
                raise ValueError("Text input requires text")
            return {"text": item.text}
        record = self._record(item)
        if item.type == "image":
            if record.kind is not MediaKind.IMAGE:
                raise ValueError("Image input requires an image media id")
            return {"image": str(record.path.resolve())}
        if item.type == "video":
            if record.kind is not MediaKind.VIDEO:
                raise ValueError("Video input requires a video media id")
            return {"video": str(record.path.resolve())}
        if item.type == "video_segment":
            segment = self.resolve_segment(record, item)
            return {"video": str(segment.path.resolve())}
        raise ValueError("Unsupported input type")

    def expand_embedding_inputs(
        self,
        items: list[MultimodalInput],
    ) -> tuple[list[dict[str, str]], list[dict]]:
        qwen_inputs: list[dict[str, str]] = []
        metadata: list[dict] = []
        for index, item in enumerate(items):
            if item.type == "video" and item.segmentation:
                record = self._record(item)
                for segment in self.segment_video(
                    record,
                    item.segmentation,
                    item.sampling or SamplingOptions(),
                ):
                    qwen_inputs.append({"video": str(segment.path.resolve())})
                    metadata.append(
                        {
                            "id": f"{record.id}:{segment.start_seconds:.3f}",
                            "type": "video_segment",
                            "media_id": record.id,
                            "segment": {
                                "start_seconds": segment.start_seconds,
                                "end_seconds": segment.end_seconds,
                            },
                        }
                    )
            else:
                qwen_inputs.append(self.resolve_for_qwen(item))
                metadata.append(self._metadata(item, index))
        return qwen_inputs, metadata

    def segment_video(
        self,
        record: MediaRecord,
        segmentation: SegmentationOptions,
        sampling: SamplingOptions,
    ) -> list[VideoSegment]:
        if record.duration_seconds is None:
            raise ValueError("Video duration is unavailable")
        if segmentation.overlap_seconds >= segmentation.chunk_seconds:
            raise ValueError("Overlap must be smaller than chunk seconds")
        stride = segmentation.chunk_seconds - segmentation.overlap_seconds
        segments: list[VideoSegment] = []
        start = 0.0
        while start < record.duration_seconds:
            end = min(start + segmentation.chunk_seconds, record.duration_seconds)
            if end - start < MIN_TAIL_SEGMENT_SECONDS and segments:
                break
            path = self._segment_path(record, start, end, sampling)
            if not path.exists():
                cut_video_segment(record.path, path, start, end - start, self.debug)
            segments.append(
                VideoSegment(start_seconds=start, end_seconds=end, path=path)
            )
            start += stride
        return segments

    def resolve_segment(
        self,
        record: MediaRecord,
        item: MultimodalInput,
    ) -> VideoSegment:
        if record.kind is not MediaKind.VIDEO:
            raise ValueError("Video segment requires a video media id")
        if not item.segment:
            raise ValueError("Video segment input requires segment times")
        start = float(item.segment.get("start_seconds", item.segment.get("start", 0)))
        end = float(item.segment.get("end_seconds", item.segment.get("end", 0)))
        if end <= start:
            raise ValueError("Video segment end must be after start")
        sampling = item.sampling or SamplingOptions()
        path = self._segment_path(record, start, end, sampling)
        if not path.exists():
            cut_video_segment(record.path, path, start, end - start, self.debug)
        return VideoSegment(start_seconds=start, end_seconds=end, path=path)

    def _record(self, item: MultimodalInput) -> MediaRecord:
        if not item.media_id:
            raise ValueError(f"{item.type} input requires media_id")
        try:
            return self.media_store.get(item.media_id)
        except KeyError as exc:
            raise ValueError("Media id was not found") from exc

    def _metadata(self, item: MultimodalInput, index: int) -> dict:
        return {
            "id": f"item_{index}",
            "type": item.type,
            "text": item.text,
            "media_id": item.media_id,
            "segment": item.segment,
        }

    def _segment_path(
        self,
        record: MediaRecord,
        start: float,
        end: float,
        sampling: SamplingOptions,
    ) -> Path:
        values = [
            record.id,
            _path_number(start, 3),
            _path_number(end, 3),
            _path_number(sampling.fps, 2),
            str(sampling.max_frames),
        ]
        name = "_".join(values) + ".mp4"
        return self.media_store.paths.decoded / record.id / name


def _path_number(value: float, precision: int) -> str:
    return f"{value:.{precision}f}".replace(".", "p")
