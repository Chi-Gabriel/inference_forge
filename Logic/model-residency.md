# Model residency

Residency modes are `dedicated`, `co_resident`, `swapping`, and `auto`.

- `dedicated` assigns a worker process and GPU to one model.
- `co_resident` keeps all configured models on the GPU after a validated memory check.
- `swapping` keeps one model on the GPU and inactive models in CPU memory when possible.
- `auto` selects co-residency only when the configured memory profile proves it safe; otherwise it swaps.

The lifecycle is CPU ready, GPU loading, GPU ready, CPU offloading, or failed. A switch completes the active batch, offloads the model, releases unused CUDA cache, loads and warms the next model, and only then marks the service ready.

Queue policy cannot switch a model during inference. A failed load leaves the target service unavailable and must not silently execute on an unintended device.

The initial RTX 3090 profile uses an 8B embedder and 2B reranker as co-resident models. They consume approximately 19.2 GiB before workload activations. GPU execution remains serialized even when weights co-reside.

Swapping remains available for oversized workloads. The measured embedding-to-reranking transition takes 13.48 seconds and the reverse transition takes 5.93 seconds when inactive weights are retained in CPU memory. Swapping therefore favors exceptional capacity over latency.
