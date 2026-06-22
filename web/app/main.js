import { ApiClient } from "./api.js";
import { bindElements, escapeHtml, initializeSidebar, initializeTabs, renderHistoryItems } from "./dom.js";
import { addRun, loadStoredSettings, runHistory, saveApiBaseUrl, saveApiKey } from "./state.js";
import { formatScore, formatTime, normalizeSegments, renderTimeline } from "./timeline.js";

const settings = loadStoredSettings();
const client = new ApiClient(readSettings);
const elements = bindElements();

initialize();

function initialize() {
  elements.apiBaseUrl.value = settings.apiBaseUrl;
  elements.apiKey.value = settings.apiKey;
  elements.apiBaseUrl.addEventListener("input", () => saveApiBaseUrl(elements.apiBaseUrl.value));
  elements.apiKey.addEventListener("input", () => saveApiKey(elements.apiKey.value));
  elements.checkApi.addEventListener("click", checkApi);
  elements.videoFile.addEventListener("change", previewSelectedVideo);
  elements.videoForm.addEventListener("submit", submitVideo);
  elements.textForm.addEventListener("submit", submitText);
  elements.imageForm.addEventListener("submit", submitImage);
  initializeSidebar(elements.sidebarToggle);
  initializeTabs();
}

function readSettings() {
  return {
    apiBaseUrl: elements.apiBaseUrl.value || "http://localhost:8000",
    apiKey: elements.apiKey.value,
  };
}

async function checkApi() {
  setApiStatus("neutral", "Checking");
  try {
    const models = await client.listModels();
    const count = models?.data?.length ?? 0;
    setApiStatus("good", `${count} model${count === 1 ? "" : "s"}`);
  } catch (error) {
    setApiStatus("bad", error.message);
  }
}

async function submitVideo(event) {
  event.preventDefault();
  setProgress(3, "Preparing media.");
  const started = performance.now();
  try {
    const media = await resolveVideoMedia();
    setProgress(15, "Creating embedding job.");
    const embeddingJob = await client.createEmbeddingJob(buildVideoEmbeddingPayload(media));
    const embeddingResult = await waitForCreatedJob(embeddingJob);
    const segments = normalizeSegments(embeddingResult.result?.items || embeddingResult.items || []);
    let finalSegments = segments;
    if (elements.enableRerank.checked) {
      setProgress(84, "Running reranker.");
      const rerankJob = await client.createRerankJob(buildRerankPayload(segments));
      const rerankResult = await waitForCreatedJob(rerankJob);
      finalSegments = mergeRerankScores(segments, rerankResult.result?.items || rerankResult.items || []);
    }
    const elapsedMs = Math.round(performance.now() - started);
    renderVideoResults(finalSegments, elapsedMs);
    recordRun("video", elapsedMs, `${finalSegments.length} segment results`);
    setProgress(100, "Complete.");
  } catch (error) {
    showError(error.message);
  }
}

async function submitText(event) {
  event.preventDefault();
  const lines = elements.textCorpus.value.split("\n").map((line) => line.trim()).filter(Boolean);
  const payload = {
    input: lines.map((text) => ({ type: "text", text })),
    query: { type: "text", text: elements.textQuery.value },
    dimensions: Number(elements.dimensions.value),
  };
  await runSimpleEmbedding("text", payload, elements.textResults);
}

async function submitImage(event) {
  event.preventDefault();
  const files = Array.from(elements.imageFiles.files || []);
  elements.imageResults.replaceChildren();
  const mediaRecords = [];
  for (const file of files) {
    const image = document.createElement("img");
    image.src = URL.createObjectURL(file);
    elements.imageResults.appendChild(image);
    mediaRecords.push(await client.uploadMedia(file));
  }
  await runSimpleEmbedding("image", {
    input: mediaRecords.map((record) => ({ type: "image", media_id: record.media_id ?? record.id })),
    query: { type: "text", text: elements.imageQuery.value },
    dimensions: Number(elements.dimensions.value),
  }, elements.imageResults);
}

async function runSimpleEmbedding(kind, payload, target) {
  const started = performance.now();
  try {
    const job = await client.createEmbeddingJob(payload);
    const result = await waitForCreatedJob(job);
    const elapsedMs = Math.round(performance.now() - started);
    target.prepend(renderNotice(`${kind} job complete in ${elapsedMs} ms with status ${result.status}.`, "good"));
    recordRun(kind, elapsedMs, "embedding job complete");
  } catch (error) {
    target.prepend(renderNotice(error.message, "bad"));
  }
}

async function resolveVideoMedia() {
  const file = elements.videoFile.files?.[0];
  const url = elements.videoUrl.value.trim();
  if (file) {
    return client.uploadMedia(file);
  }
  if (url) {
    const media = await client.downloadMedia(url);
    await previewRemoteVideo(media);
    return media;
  }
  throw new Error("Select a video file or provide a video URL.");
}

function buildVideoEmbeddingPayload(media) {
  return {
    model: "Qwen/Qwen3-VL-Embedding-8B",
    input: [
      {
        type: "video",
        media_id: media.media_id ?? media.id,
        segmentation: {
          chunk_seconds: Number(elements.chunkSeconds.value),
          overlap_seconds: Number(elements.overlapSeconds.value),
        },
        sampling: {
          fps: Number(elements.videoFps.value),
          max_frames: Number(elements.maxFrames.value),
        },
      },
    ],
    query: {
      type: "text",
      text: elements.videoQuery.value,
    },
    dimensions: Number(elements.dimensions.value),
    top_k: Number(elements.topK.value),
  };
}

function buildRerankPayload(segments) {
  return {
    query: {
      type: "text",
      text: elements.videoQuery.value,
    },
    documents: segments.map((segment) => ({
      id: segment.id,
      type: "video_segment",
      media_id: segment.mediaId,
      segment: {
        start_seconds: segment.start,
        end_seconds: segment.end,
      },
    })),
    top_k: Number(elements.topK.value),
  };
}

async function waitForCreatedJob(createdJob) {
  const jobId = createdJob.job_id ?? createdJob.id;
  if (!jobId) {
    return createdJob;
  }
  const job = await client.waitForJob(jobId, (job) => {
    setProgress(job.progress ?? 30, job.stage_label || job.status || "Processing.");
  });
  if (job.status === "failed") {
    throw new Error(job.error || "Job failed.");
  }
  return job;
}

function mergeRerankScores(segments, rerankedItems) {
  const scores = new Map(rerankedItems.map((item) => [item.id, item.score ?? item.rerank_score]));
  return segments.map((segment) => ({
    ...segment,
    rerankScore: scores.get(segment.id) ?? segment.rerankScore,
  }));
}

function renderVideoResults(segments, elapsedMs) {
  elements.latencyBadge.textContent = `${elapsedMs} ms`;
  elements.latencyBadge.className = "pill good";
  renderTimeline(elements.timeline, elements.videoPreview, segments);
  elements.resultList.replaceChildren(...segments.map(renderSegment));
}

function renderSegment(segment) {
  const item = document.createElement("article");
  item.className = "result-item";
  item.innerHTML = `
    <div class="result-head">
      <strong>${formatTime(segment.start)}–${formatTime(segment.end)}</strong>
      <span class="score">${formatScore(segment.score)}</span>
    </div>
    <p class="muted">${escapeHtml(segment.label)}</p>
    <p class="muted">Rerank: ${formatScore(segment.rerankScore)} · latency: ${segment.latencyMs ?? "n/a"} ms</p>
  `;
  return item;
}

function previewSelectedVideo() {
  const file = elements.videoFile.files?.[0];
  if (!file) {
    return;
  }
  elements.videoPreview.src = URL.createObjectURL(file);
}

async function previewRemoteVideo(media) {
  const mediaId = media.media_id ?? media.id;
  if (!mediaId) {
    return;
  }
  setProgress(10, "Preparing browser video preview.");
  const blob = await client.mediaPreviewBlob(mediaId);
  elements.videoPreview.src = URL.createObjectURL(blob);
}

function setProgress(percent, label) {
  elements.progressBar.style.width = `${Math.max(0, Math.min(100, Number(percent) || 0))}%`;
  elements.progressLabel.textContent = label;
}

function showError(message) {
  setProgress(0, message);
  elements.resultList.replaceChildren(renderNotice(message, "bad"));
  elements.latencyBadge.textContent = "Failed";
  elements.latencyBadge.className = "pill bad";
}

function renderNotice(message, tone) {
  const element = document.createElement("div");
  element.className = `result-item pill-${tone}`;
  element.textContent = message;
  return element;
}

function recordRun(kind, elapsedMs, summary) {
  addRun({ kind, elapsedMs, summary });
  renderHistory();
}

function renderHistory() {
  renderHistoryItems(elements.historyList, runHistory);
}

function setApiStatus(tone, label) {
  elements.apiStatus.className = `pill ${tone}`;
  elements.apiStatus.textContent = label;
}
