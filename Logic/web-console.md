# Web console

The web console is an external client that lives in the repository for development convenience. It must communicate only through the public HTTP API. It must not import backend modules, read Redis, inspect media paths, call worker code, or depend on internal queue keys.

The first console feature is an embedding lab for finding usable video, image, and text parameters. The console stores the API base URL and API key in browser local storage. Run history and latency measurements are in memory only and may disappear on reload.

## API boundary

The console uses the same request path as any third-party client:

1. Check service availability with `GET /v1/models`.
2. Upload media with `POST /v1/media/uploads` or ask the backend to download a URL with `POST /v1/media/downloads`.
3. Create embedding jobs with `POST /v1/embeddings/jobs`.
4. Poll job progress with `GET /v1/jobs/{job_id}`.
5. Optionally create reranking jobs with `POST /v1/rerank/jobs`.

These endpoints are implemented against the first in-process job worker. The client contract should remain stable when job state and queues move to Redis-backed distributed workers.

All requests may include `Authorization: Bearer <api key>` when the user provides a key. The key is never sent anywhere except the configured API base URL.

## Video embedding lab

The video lab accepts either a local upload or a URL. URL support is split into two backend capabilities:

- Direct media URL download for simple files with bounded size, timeout, redirect, and content-type checks.
- Extractor-backed download for providers such as TikTok, Facebook, or YouTube only after a dedicated feature document defines `yt-dlp` installation, provider allowlists, max duration, max size, rate limits, cache identity, failure handling, and legal/operator controls.

The UI exposes chunk seconds, overlap seconds, FPS, max frames per chunk, embedding dimensions, top-k, and reranking enablement. These values are part of cache identity because they change the sampled content and resulting vectors.

The expected embedding result for segmented video is a list of items with media metadata, segment start/end seconds, embedding latency, and either vectors or a server-side vector reference. The console can visualize scores on a horizontal timeline. Each segment occupies width proportional to its duration. Color intensity represents similarity score. A vertical playhead follows the browser video position, and clicking a segment seeks the video.

Reranking is an optional second pass. The console first displays vector-search scores, then overlays reranker scores when available so model behavior can be compared without losing the baseline.

## Text and image labs

Text and image labs follow the same pattern: submit inputs through embedding jobs, measure latency, then query with text or another media item. Text results should show matched item text, score, vector latency, and optional rerank score. Image results should show thumbnails, score, vector latency, and optional rerank score.

## Job status expectations

Job status responses should be structured enough for progress bars:

- `queued`
- `resolving_media`
- `downloading`
- `probing_media`
- `segmenting`
- `embedding`
- `reranking`
- `complete`
- `failed`

Each status update should include an integer progress percentage when known, a human-readable stage label, safe error details on failure, elapsed milliseconds, and per-stage timing when available.

## UX standard

The console should prioritize one-screen interpretation over raw logs. Video results should use a compact timeline, not a tall vertical list. Configuration, progress, query, and results should remain visible together on desktop layouts. Advanced raw payloads may be collapsible, but the primary view must answer: what was processed, with which parameters, how long it took, and where the query matched.
