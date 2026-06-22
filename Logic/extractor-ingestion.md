# Extractor ingestion

Extractor ingestion allows public media download requests to resolve player/provider URLs through `yt-dlp`. This is intentionally separate from direct URL downloads because provider pages can involve redirects, manifests, playlists, authentication failures, long videos, and large generated outputs.

Extractor ingestion is enabled by `MEDIA_EXTRACTOR_ENABLED` and constrained by an allowlist. The initial provider allowlist is YouTube, TikTok, Facebook, and `fb.watch`. A request outside the allowlist follows normal direct-download behavior.

The extractor path must keep the same safety boundaries as direct downloads:

- only public HTTP API callers can request ingestion;
- provider hosts must be allowlisted;
- playlists are disabled;
- output file size is bounded by `MEDIA_DOWNLOAD_MAX_BYTES`;
- media duration is bounded by `MEDIA_EXTRACTOR_MAX_DURATION_SECONDS`;
- extractor socket timeout is bounded by `MEDIA_EXTRACTOR_TIMEOUT_SECONDS`;
- output is hash-deduped into stable media ids;
- repeated source URLs are cached for the current process;
- temp extractor work directories are under media temp storage and are cleaned by TTL;
- safe client errors must not expose internal paths, stack traces, cookies, or provider internals.

Extractor downloads are for testing and controlled ingestion. If a provider needs cookies, login, proxying, rate-limit handling, or special legal/operator controls, that provider should get its own feature document before those options are enabled.

## Related files

- `app/platform/media/extractor.py` owns `yt-dlp` host matching, bounded options, duration filtering, and temporary output selection.
- `app/platform/media/store.py` owns routing between direct downloads and extractor downloads, hash dedupe, and source URL cache.
- `app/platform/config.py` owns extractor enablement, allowlist, timeout, duration, format, and size settings.
- `Logic/media-ingestion.md` owns the broader media storage, cleanup, and media-id rules.
- `deployment.md` owns install and runtime notes for `yt-dlp`.
