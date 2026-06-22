# Jobs and batching

Every GPU request crosses a queue and batching boundary. A work item carries its service kind, creation time, deadline, estimated cost, and opaque service payload.

Batch admission is limited by aggregate cost. Service-specific estimators account for tokens, images, sampled frames, and modality preprocessing. Items that cannot fit alone are rejected before GPU execution.

A resident model processes bounded epochs rather than draining a continuously changing queue. An epoch ends when its time or cost budget is consumed, the queue snapshot is complete, or another queue reaches its maximum wait.

Model switching occurs only between batches. Minimum residency and switch cooldown values prevent oscillation. An overdue competing queue overrides normal throughput preference.

Co-residency is allowed only when profiled model peaks plus activation reserve and fragmentation margin fit below the configured VRAM cap.

The public implementation uses the same job contract for Redis and memory stores. When Redis is reachable, jobs and progress are stored under the configured Redis prefix and queued through a Redis list. If Redis is unavailable and the backend is `auto`, the app falls back to an in-process store for development continuity. For production-like runs, force `JOB_STORE_BACKEND=redis` so startup fails instead of silently losing durability.

Redis-backed jobs survive API restarts. Unfinished non-terminal jobs are requeued on startup. Completed and failed jobs remain readable until Redis state is intentionally cleared.

## Related files

- `app/api/routes/jobs.py` owns public job lookup.
- `app/platform/jobs/types.py` owns job status, kind, internal record, and public response contracts.
- `app/platform/jobs/store.py` owns the job-store interface, in-process fallback queue, worker loop, progress updates, and safe error shaping.
- `app/platform/jobs/redis_store.py` owns Redis job records, Redis queue claiming, restart recovery, and Redis-backed worker execution.
- `app/platform/jobs/factory.py` owns memory/Redis backend selection.
- `app/services/runtime/executor.py` owns dispatch from job kind to embedding or reranking execution.
- `app/workers/scheduler.py` owns the reusable scheduler shape for the later Redis-backed batching worker.
- `app/platform/gpu/policy.py` owns queue starvation, residency epoch, and switch decision policy.
