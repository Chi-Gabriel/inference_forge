code-rules.md
code-vibe.md
knowledge.md
remember.md
deployment.md
Dockerfile
docker-compose.yml
.env.example
.env
pyproject.toml
README.md
embedding-service/
  Logic/
  app/
    main.py

    api/
      __init__.py
      router.py
      routes/
        health.py
        models.py
        embeddings.py
        multimodal_embeddings.py
        media.py
        rerank.py
        admin.py

    schemas/
      __init__.py
      openai.py
      media.py
      embeddings.py
      rerank.py
      jobs.py
      errors.py

    core/
      __init__.py
      config.py
      logging.py
      errors.py
      lifecycle.py
      security.py

    engines/
      __init__.py
      base.py
      model_loader.py
      qwen_embedding.py
      qwen_reranker.py

    media/
      __init__.py
      ids.py
      registry.py
      storage.py
      downloader.py
      decoder.py
      cache_keys.py
      cleanup.py

    scheduler/
      __init__.py
      batcher.py
      jobs.py
      limits.py
      queue.py

    redis/
      __init__.py
      client.py
      keys.py
      store.py
      locks.py

    workers/
      __init__.py
      embedding_worker.py
      reranker_worker.py
      cleanup_worker.py

  scripts/
    

tests/
    codes/
      