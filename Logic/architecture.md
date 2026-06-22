# Architecture

The API is a control and ingress layer. It validates requests, resolves media, creates jobs, and waits or returns a job reference. It does not import or execute GPU engines.

Workers claim bounded batches from service queues. Embedding and reranking services own their domain behavior and engine adapters. Configuration, errors, job contracts, batching policy, Redis coordination, storage, media handling, and GPU residency are platform capabilities.

Services may be disabled independently. Disabled services are omitted from advertised models and their routes must not accept work.

Model engines are replaceable behind typed lifecycle and inference contracts. Public schemas must not expose Transformers, Sentence Transformers, vLLM, CUDA, or filesystem details.

Model identifiers and immutable Hugging Face revisions are deployment configuration. Workers must not silently move to a newer checkpoint revision.
