# Reranking

Reranking accepts one multimodal query and a bounded list of multimodal documents. It returns one relevance score per input document and preserves input indices so callers can recover stable ordering for equal scores.

The GPU unit is a query-document pair. Requests are flattened into pairs, admitted by aggregate token and visual cost, processed as padded tensor micro-batches, and reassembled afterward.

The upstream reference helper evaluates documents sequentially. The service intentionally batches its prepared pairs through the reference tokenizer and lower-level score computation.

The initial single-GPU deployment uses the 2B reranker so it can remain resident with the 8B embedder. Queue limits are modality-specific because video pair cost is substantially higher than text pair cost.
