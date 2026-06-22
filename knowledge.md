# Reusable engineering notes

- A multimodal batch limit expressed only as an item count is unsafe. Admission should use a cost derived from text tokens, image pixels, sampled video frames, and padding amplification.
- Model switching should happen at batch boundaries with bounded residency epochs. Draining a live queue completely can starve other model queues indefinitely.
- Co-residency must be decided from profiled peak memory plus a fragmentation margin, not checkpoint size or momentary free VRAM alone.
- A high-level model package can appear to run while silently leaving checkpoint weights uninitialized because its base-class key mapping differs from the checkpoint wrapper. Treat any missing/new-weight warning as a failed integration and verify against the publisher's reference class before trusting output or benchmarks.
- Reference helpers may advertise default prompts at their highest-level method while lower-level formatters still require an explicit value. Adapters that bypass a sequential helper for batching must reproduce its input normalization before calling lower layers.
