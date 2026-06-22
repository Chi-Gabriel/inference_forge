# Inference Forge Web Console

This is a browser-only development console for testing public Inference Forge APIs. It is intentionally outside `app/` and communicates only through HTTP.

Run it from the repository root:

```bash
python -m http.server 8080 -d web
```

Then open `http://localhost:8080`.

The API base URL and API key are saved in browser local storage. Run history is memory-only.
