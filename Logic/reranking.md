# Reranking

Reranking accepts one multimodal query and a bounded list of multimodal documents. It returns one relevance score per input document and preserves input indices so callers can recover stable ordering for equal scores.

The GPU unit is a query-document pair. Requests are flattened into pairs, admitted by aggregate token and visual cost, processed as padded tensor micro-batches, and reassembled afterward.

The upstream reference helper evaluates documents sequentially. The service intentionally batches its prepared pairs through the reference tokenizer and lower-level score computation.

The initial single-GPU deployment uses the 2B reranker so it can remain resident with the 8B embedder. Queue limits are modality-specific because video pair cost is substantially higher than text pair cost.

## Related files

- `app/api/routes/rerank.py` owns public reranking job creation.
- `app/services/reranking/qwen.py` owns the pinned Qwen3-VL reranker lifecycle and batched lower-level score computation.
- `app/services/runtime/executor.py` owns reranking job execution, model activation, result ordering, and response shaping.
- `app/services/runtime/media_inputs.py` owns conversion from public multimodal query/document inputs into Qwen-ready reranker inputs.
- `app/services/runtime/types.py` owns reranking request payloads and sampling options.
