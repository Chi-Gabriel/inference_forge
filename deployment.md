# Deployment notes

## 2026-06-21

- Copy `.env.example` to `.env` and tune the GPU residency values for the host.
- Python 3.11 is the initial supported GPU runtime. Install the `gpu` dependency group only in GPU worker images.
- The official Qwen implementation pins PyTorch 2.8, Torchvision 0.23, and Transformers 4.57.3 or newer; validate FlashAttention separately against the deployed CUDA stack.
- Model files are not downloaded during application installation. GPU worker provisioning will download pinned Hugging Face revisions in the model integration phase.
- The embedding revision `2c4565515e0f265c6511776e7193b22c0968ddc7` has been cached and validated with Qwen's reference class on the RTX 3090.
- Standard Hugging Face HTTP transfer was required after the Xet transfer path stalled. Set `HF_HUB_DISABLE_XET=1` if the same behavior occurs during provisioning.
- The reranking revision `b212dc8c91a8164aef1ea2de9c1a867611e75c04` has been cached and validated with batched lower-level scoring.
- Both 8B models can remain in system RAM on the current host, but not in 24 GiB VRAM. The measured embedding-to-reranking transition is about 17 seconds; use the longer default residency epoch values unless latency requirements justify another deployment topology.
- The initial single-GPU profile now uses Qwen3-VL-Reranker-2B revision `4bd860ac4f15ad1897a214615cccc700f8f71818` beside the 8B embedder. With a 23 GiB cap, 2.5 GiB activation reserve, and 1 GiB margin, automatic residency selects co-resident mode.
- Keep GPU execution serialized. Initial video admission is 1 FPS, at most 16 frames, and at most four video items or pairs per batch. See `gpu-benchmarks.md` before changing these limits.

## 2026-06-22

- The development web console can be served with `python -m http.server 8080 -d web`.
- Browser access requires the API host to allow the console origin through `CORS_ALLOWED_ORIGINS`. The default development origins are localhost and 127.0.0.1 on ports 5173 and 8080.
- TikTok, Facebook, YouTube, or other extractor-backed URL ingestion is enabled through the bounded `yt-dlp` path documented in `Logic/extractor-ingestion.md`.
- Install the updated runtime dependencies after pulling this change: `pip install -e '.[dev]'` for API development or the equivalent image rebuild. `python-multipart` is required for media uploads.
- Configure `MEDIA_ROOT`, media byte limits, direct-download timeout/redirect limits, and `MEDIA_ALLOWED_CONTENT_TYPES` for the deployment host.
- `API_KEY` is optional. If set, public `/v1` work routes require `Authorization: Bearer <API_KEY>`.
- Docker runtime is now rooted at `compose.yaml`. Start with `cp .env.example .env` and `docker compose up --build`.
- GPU Docker runs require NVIDIA Container Toolkit on the host. Validate `docker run --rm --gpus all nvidia/cuda:12.8.1-base-ubuntu22.04 nvidia-smi` before debugging application-level CUDA issues.
- Docker volumes are used for Redis data, media bytes, and Hugging Face model cache. Remove them only when intentionally clearing state: `docker compose down -v`.
- The API image installs the `gpu` optional dependency group and FFmpeg. Rebuild the image after dependency or CUDA-runtime changes.
- Non-Docker hosts can use `./scripts/start.sh` after `cp .env.example .env`. This starts the API and web console from the repository `.venv`.
- Fresh non-Docker hosts can use `./setup.sh`. It performs host package installation when possible, syncs `.venv`, writes local `.env` defaults, verifies CUDA, and starts the stack. Use `./setup.sh --no-start` for provisioning only.
- For non-Docker GPU hosts, validate `nvidia-smi`, `ffmpeg`, and `.venv/bin/python -c "import torch; print(torch.cuda.is_available())"` before debugging model execution.
- Keep `HF_HOME=hf_cache` or another persistent host path in `.env` so Hugging Face checkpoints survive restarts on rented machines.
- If port `3000` is occupied on a rented host, start the web console with `WEB_PORT=<port> ./scripts/start-web.sh`.
- Non-Docker Redis can be started with `./scripts/start-redis.sh` when `redis-server` is installed. It stores append-only Redis data under `var/redis` by default.
- `JOB_STORE_BACKEND=auto` uses Redis when reachable and falls back to memory. Use `JOB_STORE_BACKEND=redis` for production-like runs where job durability must not silently downgrade.
- If Redis is missing on a non-Docker host, install it with the host package manager when allowed, for example `apt install -y redis-server` on a root shell.
- Automatic cleanup is controlled by `CLEANUP_ENABLED`, `CLEANUP_INTERVAL_SECONDS`, `JOB_TTL_HOURS`, and the `MEDIA_*_TTL_HOURS` settings. Model cache cleanup is intentionally manual.
- Provider/player URL ingestion now uses `yt-dlp`. Install or rebuild dependencies after pulling: `pip install -e '.[dev,gpu]'`. Tune `MEDIA_EXTRACTOR_ENABLED`, `MEDIA_EXTRACTOR_ALLOWED_HOSTS`, `MEDIA_EXTRACTOR_TIMEOUT_SECONDS`, `MEDIA_EXTRACTOR_MAX_DURATION_SECONDS`, `MEDIA_DOWNLOAD_MAX_BYTES`, and `MEDIA_EXTRACTOR_FORMAT`.
