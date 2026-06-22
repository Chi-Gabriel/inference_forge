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
