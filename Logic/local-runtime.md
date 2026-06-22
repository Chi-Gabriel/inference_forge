# Local runtime

The local runtime is the non-Docker path for rented GPU hosts where Docker or NVIDIA Container Toolkit is unavailable. It uses the repository `.venv`, reads `.env` through the application settings, and keeps media/model cache on the host filesystem.

The API and web console still run as separate processes. The web console remains an external client and communicates only through public HTTP endpoints.

Redis is optional for the current implementation because jobs are stored in-process. Keep `REDIS_URL` configured anyway so the same environment is ready when the Redis-backed queue replaces the development job store.

Host requirements are Python, the `.venv` dependencies, FFmpeg, and NVIDIA/CUDA visibility for GPU inference. `HF_HOME` should point to a persistent directory so model checkpoints are not redownloaded every session.

## Related files

- `scripts/start-api.sh` starts the FastAPI API with the repository virtual environment.
- `scripts/start-web.sh` starts the static web console.
- `scripts/start.sh` starts both local processes and stops both when either exits.
- `.env.example` owns local runtime defaults.
- `README.md` owns short local run instructions.
- `deployment.md` owns host setup and operational notes.
