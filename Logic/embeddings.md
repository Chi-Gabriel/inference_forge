# Embeddings

Qwen3-VL embedding inputs may contain text, images, videos, or mixtures of these modalities. Each accepted item produces one normalized vector. Output dimensions range from 64 to 4096; reduced Matryoshka vectors are truncated and normalized again.

The engine loads an immutable Hugging Face revision and uses Qwen's pinned reference implementation. Missing or newly initialized checkpoint-weight warnings invalidate the engine and its measurements.

The initial runtime context limit is 8192. Video sampling and visual pixel limits are server-controlled and form part of cache identity.

On the RTX 3090, the validated BF16 SDPA text run used approximately 15.39 GiB reserved for batch 1 and 15.50 GiB for batch 4 with short inputs. A 512-pixel image reserved 15.43 GiB. An eight-frame 384-pixel video reserved 17.14 GiB, while a batch of two such videos reserved 18.84 GiB. These synthetic measurements do not establish final production limits.

Public embedding jobs accept text, image media ids, video media ids, and segmented video requests. Segmented video jobs cut cacheable clips under decoded media storage and embed each clip as a separate item. If a query is provided, the service embeds the query in the same vector space and returns top-k cosine-ranked items.

## Related files

- `app/api/routes/embeddings.py` owns public embedding job creation and the OpenAI-style text embedding entrypoint.
- `app/services/embeddings/qwen.py` owns the pinned Qwen3-VL embedding engine lifecycle and vector generation.
- `app/services/runtime/executor.py` owns embedding job execution, model activation, vector scoring, and top-k result shaping.
- `app/services/runtime/media_inputs.py` owns conversion from public text/image/video inputs into Qwen-ready inputs and cacheable video segments.
- `app/services/runtime/types.py` owns embedding request payloads, segmentation options, sampling options, and scored item contracts.
- `app/services/runtime/vector.py` owns cosine scoring for query-to-item ranking.
