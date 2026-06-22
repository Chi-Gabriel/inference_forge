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
