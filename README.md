# Inference Forge

Inference Forge is a worker-backed multimodal inference system. The initial single-GPU profile uses Qwen3-VL-Embedding-8B with Qwen3-VL-Reranker-2B; shared API, media, queue, batching, cache, and GPU lifecycle facilities are designed for reuse by future inference services.

The HTTP API never invokes a GPU model directly. Requests pass through a job and batching boundary before reaching a model worker.

## Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
pytest
```

GPU dependencies are deliberately optional:

```bash
pip install -e '.[dev,gpu]'
```

See `Logic/` for behavior and invariants. Deployment-sensitive changes are recorded in `deployment.md`.

Measured RTX 3090 limits and stress results are recorded in `gpu-benchmarks.md`.

## Local runtime without Docker

For rented GPU hosts where Docker is unavailable, use the root scripts:

```bash
cp .env.example .env
./scripts/start.sh
```

Or run the processes separately:

```bash
./scripts/start-api.sh
./scripts/start-web.sh
```

Services:

- API: `http://localhost:8000`
- Web console: `http://localhost:8080`

If port `8080` is already used, override it:

```bash
WEB_PORT=18080 ./scripts/start-web.sh
```

The current development job store is in-process, so Redis is not required for this local path yet. Keep `REDIS_URL` configured for the later Redis-backed worker.

## Docker runtime

Copy the example environment and start the stack:

```bash
cp .env.example .env
docker compose up --build
```

Services:

- API: `http://localhost:8000`
- Web console: `http://localhost:8080`
- Redis: `localhost:6379`

The API container requests GPU access. The host must have NVIDIA drivers, Docker, Docker Compose, and NVIDIA Container Toolkit installed for GPU inference jobs. The first embedding or reranking job downloads model files into the `hf_cache` Docker volume.

## Web console

The development web console lives in `web/` and talks to the public HTTP API only.

```bash
python -m http.server 8080 -d web
```

Open `http://localhost:8080`, set the API base URL, and enter an API key if the deployment requires one. The first console workflow targets video/text/image embedding parameter tests and is documented in `Logic/web-console.md`.

## Initial public API

- `GET /v1/models`
- `POST /v1/media/uploads`
- `POST /v1/media/downloads`
- `GET /v1/media/{media_id}`
- `POST /v1/embeddings/jobs`
- `POST /v1/embeddings`
- `POST /v1/rerank/jobs`
- `GET /v1/jobs/{job_id}`

The current job store is in-process for development. It preserves the external job contract, but it is not the final Redis-backed distributed queue.
