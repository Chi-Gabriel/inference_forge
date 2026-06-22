export function bindElements() {
  return {
    apiBaseUrl: document.getElementById("apiBaseUrl"),
    apiKey: document.getElementById("apiKey"),
    apiStatus: document.getElementById("apiStatus"),
    checkApi: document.getElementById("checkApi"),
    videoForm: document.getElementById("videoForm"),
    videoFile: document.getElementById("videoFile"),
    videoUrl: document.getElementById("videoUrl"),
    chunkSeconds: document.getElementById("chunkSeconds"),
    overlapSeconds: document.getElementById("overlapSeconds"),
    videoFps: document.getElementById("videoFps"),
    maxFrames: document.getElementById("maxFrames"),
    dimensions: document.getElementById("dimensions"),
    topK: document.getElementById("topK"),
    videoQuery: document.getElementById("videoQuery"),
    enableRerank: document.getElementById("enableRerank"),
    videoPreview: document.getElementById("videoPreview"),
    timeline: document.getElementById("timeline"),
    latencyBadge: document.getElementById("latencyBadge"),
    progressBar: document.getElementById("progressBar"),
    progressLabel: document.getElementById("progressLabel"),
    resultList: document.getElementById("resultList"),
    historyList: document.getElementById("historyList"),
    textForm: document.getElementById("textForm"),
    textCorpus: document.getElementById("textCorpus"),
    textQuery: document.getElementById("textQuery"),
    textResults: document.getElementById("textResults"),
    imageForm: document.getElementById("imageForm"),
    imageFiles: document.getElementById("imageFiles"),
    imageQuery: document.getElementById("imageQuery"),
    imageResults: document.getElementById("imageResults"),
  };
}

export function initializeTabs() {
  document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", switchTab));
}

export function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function renderHistoryItems(container, history) {
  container.replaceChildren(
    ...history.map((run) => {
      const item = document.createElement("article");
      item.className = "result-item";
      item.innerHTML = `<strong>${run.kind}</strong> · ${run.elapsedMs} ms<p class="muted">${escapeHtml(run.summary)} · ${run.createdAt}</p>`;
      return item;
    }),
  );
}

function switchTab(event) {
  const tabName = event.currentTarget.dataset.tab;
  document
    .querySelectorAll(".tab")
    .forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === tabName));
  document
    .querySelectorAll(".tab-panel")
    .forEach((panel) => panel.classList.toggle("active", panel.id === `${tabName}Tab`));
}
