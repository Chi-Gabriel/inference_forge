# Jobs and batching

Every GPU request crosses a queue and batching boundary. A work item carries its service kind, creation time, deadline, estimated cost, and opaque service payload.

Batch admission is limited by aggregate cost. Service-specific estimators account for tokens, images, sampled frames, and modality preprocessing. Items that cannot fit alone are rejected before GPU execution.

A resident model processes bounded epochs rather than draining a continuously changing queue. An epoch ends when its time or cost budget is consumed, the queue snapshot is complete, or another queue reaches its maximum wait.

Model switching occurs only between batches. Minimum residency and switch cooldown values prevent oscillation. An overdue competing queue overrides normal throughput preference.

Co-residency is allowed only when profiled model peaks plus activation reserve and fragmentation margin fit below the configured VRAM cap.

The first public implementation uses the same job contract with an in-process queue and worker. This is a development bridge, not the final distributed worker topology. Public clients already create jobs and poll structured status; the backing store can move to Redis without changing those routes.
