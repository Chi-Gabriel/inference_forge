const JOB_POLL_INTERVAL_MS = 850;
const JOB_TIMEOUT_MS = 600000;

export class ApiClient {
  constructor(getSettings) {
    this.getSettings = getSettings;
  }

  async listModels() {
    return this.request("/v1/models");
  }

  async uploadMedia(file) {
    const form = new FormData();
    form.append("file", file);
    return this.request("/v1/media/uploads", {
      method: "POST",
      body: form,
    });
  }

  async downloadMedia(url) {
    return this.request("/v1/media/downloads", {
      method: "POST",
      body: JSON.stringify({ url }),
    });
  }

  async createEmbeddingJob(payload) {
    return this.request("/v1/embeddings/jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async createRerankJob(payload) {
    return this.request("/v1/rerank/jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async getJob(jobId) {
    return this.request(`/v1/jobs/${encodeURIComponent(jobId)}`);
  }

  async waitForJob(jobId, onUpdate) {
    const started = performance.now();
    while (performance.now() - started < JOB_TIMEOUT_MS) {
      const job = await this.getJob(jobId);
      onUpdate(job);
      if (job.status === "complete" || job.status === "failed") {
        return job;
      }
      await new Promise((resolve) => setTimeout(resolve, JOB_POLL_INTERVAL_MS));
    }
    throw new Error("Job polling timed out.");
  }

  async request(path, options = {}) {
    const { apiBaseUrl, apiKey } = this.getSettings();
    const headers = new Headers(options.headers || {});
    if (!(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }
    if (apiKey) {
      headers.set("Authorization", `Bearer ${apiKey}`);
    }
    const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}${path}`, {
      ...options,
      headers,
    });
    const payload = await readPayload(response);
    if (!response.ok) {
      throw new ApiError(response.status, payload);
    }
    return payload;
  }
}

export class ApiError extends Error {
  constructor(status, payload) {
    super(formatApiError(status, payload));
    this.status = status;
    this.payload = payload;
  }
}

async function readPayload(response) {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    return { message: text };
  }
}

function formatApiError(status, payload) {
  if (status === 404) {
    return "This API endpoint is not implemented yet.";
  }
  if (payload?.detail) {
    return typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail);
  }
  if (payload?.message) {
    return payload.message;
  }
  return `API request failed with status ${status}.`;
}
