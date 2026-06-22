# Media ingestion

Media ingestion is a public API capability shared by current and future services. Uploads and direct URL downloads produce stable hash-derived media ids. Media bytes stay on disk, not in Redis or job payloads.

Uploads are bounded by configured byte limits and allowed content types. Direct URL downloads are limited by scheme, redirect count, timeout, byte size, and content type.

Provider/player URLs such as TikTok, Facebook, and YouTube use the extractor ingestion path documented in `Logic/extractor-ingestion.md`. Extractor ingestion is allowed only through `yt-dlp` with provider allowlists, size limits, duration limits, timeouts, hash dedupe, safe errors, and cleanup.

Stored media is split by origin and purpose: uploads, downloads, temp files, decoded clips, and cache artifacts. The in-process media index is rebuilt from existing upload/download files at startup so hash-derived ids remain usable after a restart.

Browser playback uses a derived preview path, not the original media path. If downloaded video uses a browser-hostile codec such as HEVC/H.265, the API can transcode a cached H.264/yuv420p MP4 preview under media cache. This preview is for UI playback only; embedding and reranking keep using the original stored media unless a feature explicitly opts into normalized media.

Automatic cleanup is enabled by default. Uploads and downloads expire by file mtime, and media lookup refreshes mtime so recently used media is retained. Temp files, decoded clips, and cache artifacts have separate TTLs. Model checkpoint cache is not part of media cleanup and must not be deleted automatically.

## Related files

- `app/api/routes/media.py` owns the public media upload, download, and lookup endpoints.
- `app/platform/media/store.py` owns content-type checks, size limits, URL download safety, hashing, dedupe, and startup indexing.
- `app/platform/media/extractor.py` owns bounded `yt-dlp` provider URL extraction.
- `app/platform/media/browser_preview.py` owns browser-stable preview selection and H.264 preview transcoding.
- `app/platform/media/types.py` owns media records and segment types.
- `app/platform/media/probe.py` owns FFprobe metadata extraction and FFmpeg clip cutting.
- `app/platform/storage/paths.py` owns the upload, download, temp, decoded, and cache directory layout.
- `app/platform/cleanup.py` owns the background cleanup loop that invokes media and job cleanup.
- `app/platform/config.py` owns media limits, allowed content types, and storage root settings.
