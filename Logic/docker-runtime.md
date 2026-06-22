# Docker runtime

The root Docker runtime starts the API, Redis, and the static web console as separate services. The web container is only a static client and must keep using the public API boundary.

The API image includes FFmpeg and GPU Python dependencies because the current app process owns both HTTP job intake and the in-process worker. Model files are cached in a named Hugging Face volume so restarts do not redownload checkpoints. Media bytes are stored in a named media volume and remain outside Redis.

Redis is part of the stack now even though the current job store is still in-process. It is the target backing service for short-lived jobs, queues, locks, progress, media ids, and cache metadata. Large videos and vectors must stay on filesystem/object storage, not Redis.

The compose file requests all GPUs for the API service. Hosts must have the NVIDIA driver and NVIDIA Container Toolkit configured before GPU inference jobs can run inside Docker.

## Related files

- `Dockerfile` owns the API image, Python dependency installation, FFmpeg installation, and Uvicorn command.
- `compose.yaml` owns local orchestration for API, Redis, web console, GPU access, and persistent volumes.
- `.dockerignore` owns Docker build-context exclusions.
- `.env.example` owns runtime configuration defaults that can be copied to `.env`.
- `deployment.md` owns operational commands and host setup notes.
- `README.md` owns the short local run instructions.
