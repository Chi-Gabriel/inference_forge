const PLAYHEAD_CLASS = "playhead";

export function renderTimeline(container, video, segments) {
  container.replaceChildren();
  const duration = readDuration(video, segments);
  for (const segment of segments) {
    const element = document.createElement("button");
    element.type = "button";
    element.className = "segment";
    element.style.left = `${(segment.start / duration) * 100}%`;
    element.style.width = `${((segment.end - segment.start) / duration) * 100}%`;
    element.style.background = scoreColor(segment.score ?? 0);
    element.title = `${formatTime(segment.start)}–${formatTime(segment.end)} score ${formatScore(segment.score)}`;
    element.addEventListener("click", () => {
      video.currentTime = segment.start;
      video.play();
    });
    container.appendChild(element);
  }
  const playhead = document.createElement("div");
  playhead.className = PLAYHEAD_CLASS;
  container.appendChild(playhead);
  const update = () => {
    const left = duration > 0 ? (video.currentTime / duration) * 100 : 0;
    playhead.style.left = `${Math.min(100, Math.max(0, left))}%`;
  };
  video.addEventListener("timeupdate", update);
  video.addEventListener("loadedmetadata", update);
  update();
}

export function normalizeSegments(items) {
  return items.map((item, index) => {
    const segment = item.segment || {};
    return {
      id: item.id || `segment-${index}`,
      start: Number(segment.start_seconds ?? segment.start ?? index),
      end: Number(segment.end_seconds ?? segment.end ?? index + 1),
      score: Number(item.score ?? item.similarity ?? 0),
      rerankScore: item.rerank_score ?? item.rerankScore,
      label: item.label || item.text || `Segment ${index + 1}`,
      mediaId: item.media_id ?? item.mediaId,
      latencyMs: item.latency_ms ?? item.latencyMs,
    };
  });
}

export function formatTime(value) {
  const minutes = Math.floor(value / 60);
  const seconds = Math.floor(value % 60)
    .toString()
    .padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export function formatScore(value) {
  if (value === undefined || Number.isNaN(value)) {
    return "n/a";
  }
  return Number(value).toFixed(3);
}

function readDuration(video, segments) {
  if (Number.isFinite(video.duration) && video.duration > 0) {
    return video.duration;
  }
  return Math.max(...segments.map((segment) => segment.end), 1);
}

function scoreColor(score) {
  const clamped = Math.min(1, Math.max(0, score));
  const hue = 7 + clamped * 135;
  const alpha = 0.22 + clamped * 0.68;
  return `hsla(${hue}, 84%, 56%, ${alpha})`;
}
