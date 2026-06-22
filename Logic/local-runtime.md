# Local runtime

The local runtime is the non-Docker path for rented GPU hosts where Docker or NVIDIA Container Toolkit is unavailable. It uses the repository `.venv`, reads `.env` through the application settings, and keeps media/model cache on the host filesystem.

The API and web console still run as separate processes. The default local ports are API `8000` and web `3000`. The web console remains an external client and communicates only through public HTTP endpoints.

Redis is preferred for local runtime because jobs, progress, and terminal results survive API restarts. `./scripts/start.sh` starts Redis automatically when `redis-server` is installed. If Redis is unavailable and `JOB_STORE_BACKEND=auto`, the API falls back to in-process jobs. Set `JOB_STORE_BACKEND=redis` when durability should be mandatory.

Host requirements are Python, the `.venv` dependencies, FFmpeg, and NVIDIA/CUDA visibility for GPU inference. `HF_HOME` should point to a persistent directory so model checkpoints are not redownloaded every session.

`setup.sh` is the root bootstrap command for non-Docker hosts. It avoids `sudo`, installs host packages only when the current user can run `apt-get`, creates or reuses `.venv`, installs `.[dev,gpu]`, writes local runtime defaults to `.env`, verifies CUDA through PyTorch, and starts the stack unless `--no-start` is passed.

Cleanup runs inside the API process when `CLEANUP_ENABLED=true`. The local defaults keep uploads/downloads for seven days, temp files for six hours, decoded clips for one day, media cache artifacts for seven days, and terminal jobs for one day.

## Related files

- `setup.sh` bootstraps and optionally starts the full non-Docker runtime.
- `scripts/start-api.sh` starts the FastAPI API with the repository virtual environment.
- `scripts/start-redis.sh` starts a local Redis process with append-only persistence under `var/redis`.
- `scripts/start-web.sh` starts the static web console.
- `scripts/start.sh` starts Redis when available, then starts the API and web console.
- `app/platform/cleanup.py` owns automatic local cleanup behavior.
- `.env.example` owns local runtime defaults.
- `README.md` owns short local run instructions.
- `deployment.md` owns host setup and operational notes.
