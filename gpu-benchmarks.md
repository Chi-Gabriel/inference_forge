# GPU benchmarks

## 2026-06-21 — RTX 3090

Hardware and runtime:

- NVIDIA RTX 3090, 24 GiB
- BF16 with PyTorch SDPA
- Qwen3-VL-Embedding-8B revision `2c4565515e0f265c6511776e7193b22c0968ddc7`
- Qwen3-VL-Reranker-2B revision `4bd860ac4f15ad1897a214615cccc700f8f71818`
- Both models resident unless a result explicitly says standalone

Times include media decode, preprocessing, inference, and result transfer, but exclude initial model loading. CUDA reserved memory may retain an earlier allocator high-water mark; allocated memory and OOM boundaries are the more reliable per-case comparisons.

### Video fixtures

The videos were generated moving-pattern H.264 MP4 files at 640×360 and 10 source FPS.

| Video | Exact duration | File size | Sampling at 1 FPS |
|---|---:|---:|---:|
| Short | 10.0 s | 1,076,732 bytes | up to 10 frames |
| Medium | 30.0 s | 3,240,458 bytes | capped to 16 frames |
| Long | 60.0 s | 6,503,396 bytes | capped to 16 or 32 frames |

### Standalone 2B reranker

| Input | Batch | Time | Peak reserved | Outcome |
|---|---:|---:|---:|---|
| Short text pairs | 128 | 0.59 s | 5.06 GiB | Success |
| 10 s video, 10 frames | 16 | 4.63 s | 10.07 GiB | Success |
| 30 s video, 16 frames | 16 | 7.69 s | 14.80 GiB | Success |
| 30 s video, 16 frames | 32 | 15.77 s | 21.21 GiB | Success |
| 30 s video, 16 frames | 48 | 23.59 s | 23.12 GiB | Edge success |
| 30 s video, 16 frames | 64 | 18.85 s | — | CUDA OOM |
| 60 s video, 32 frames | 16 | 18.10 s | 19.04 GiB | Success |

Short-text throughput plateaued around 216 pairs per second. The 48-video result is a stress boundary and must not be used as an operational limit.

### Co-resident reranker workload

The 8B embedder and 2B reranker occupy approximately 19.2 GiB before workload activations.

| Input | Batch | Time | Peak reserved | Outcome |
|---|---:|---:|---:|---|
| Short text pairs | 256 | 1.11 s | 21.10 GiB | Success |
| Short text pairs | 512 | 2.21 s | 23.03 GiB | Edge success |
| 30 s video, 16 frames | 4 | 2.24 s | ≤23.03 GiB | Success |
| 30 s video, 16 frames | 8 | 4.69 s | ≤23.03 GiB | Edge success |
| 30 s video, 16 frames | 12 | 4.35 s | — | CUDA OOM |

### Co-resident embedding workload

| Input | Batch | Time | Peak reserved | Outcome |
|---|---:|---:|---:|---|
| Short text | 128 | 0.78 s | 19.80 GiB | Success |
| 512×512 image | 12 | 1.27 s | 20.52 GiB | Success |
| 10 s video, 10 frames | 4 | 2.31 s | 21.23 GiB | Success |
| 10 s video, 10 frames | 8 | 4.29 s | 22.99 GiB | Edge success |
| 30 s video, 16 frames | 4 | 3.51 s | ≤22.99 GiB | Success |
| 30 s video, 16 frames | 8 | 7.48 s | 23.11 GiB | Edge success |
| 30 s video, 16 frames | 10 | 3.99 s | — | CUDA OOM |

### Swapping overhead

Both inactive models were retained in system RAM.

| Transition | Offload | Load and warm | Total |
|---|---:|---:|---:|
| Embedding 8B → reranker 2B | 12.52 s | 0.96 s | 13.48 s |
| Reranker 2B → embedding 8B | 2.12 s | 3.81 s | 5.93 s |

### Initial operational limits

| Service workload | Queue batch maximum |
|---|---:|
| Embedding, short text | 128 |
| Embedding, 512-pixel images | 8 |
| Embedding, video at 1 FPS and at most 16 frames | 4 |
| Reranking, short text pairs | 256 |
| Reranking, image pairs | 8 pending dedicated measurement |
| Reranking, video pairs at 1 FPS and at most 16 frames | 4 |

These are admission ceilings, not batching targets. The scheduler should close a batch earlier when estimated tokens or visual pixels reach its cost budget. Video batch 6–8 can be enabled later as a high-throughput profile, but it materially reduces OOM recovery headroom.
