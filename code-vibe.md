# Coding approach

- Keep the public API independent of inference engines and deployment topology.
- Validate and bound work before queueing it; GPU workers never trust raw client input.
- Batch by estimated token and visual cost, not item count alone.
- Switch resident models only between batches and use deadlines to prevent queue starvation.
- Treat VRAM limits as measured budgets containing weights, activations, workspaces, and fragmentation margin.
- Keep media bytes and large vectors outside Redis; Redis coordinates short-lived state.
- Make failures structured, observable, retry-aware, and safe to expose.
- Prefer small typed modules and explicit interfaces over framework coupling.

