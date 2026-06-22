# Media ingestion

Media ingestion is a public API capability shared by current and future services. Uploads and direct URL downloads produce stable hash-derived media ids. Media bytes stay on disk, not in Redis or job payloads.

Uploads are bounded by configured byte limits and allowed content types. Direct URL downloads are limited by scheme, redirect count, timeout, byte size, and content type. Provider extractor URLs such as TikTok, Facebook, and YouTube are rejected until an extractor-specific feature document defines allowlists, limits, cache identity, rate limits, and operator controls.

Stored media is split by origin and purpose: uploads, downloads, temp files, decoded clips, and cache artifacts. The in-process media index is rebuilt from existing upload/download files at startup so hash-derived ids remain usable after a restart.
