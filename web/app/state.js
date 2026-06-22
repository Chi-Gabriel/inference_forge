const API_BASE_URL_KEY = "inference_forge_api_base_url";
const API_KEY_KEY = "inference_forge_api_key";

export const runHistory = [];

export function loadStoredSettings() {
  return {
    apiBaseUrl: localStorage.getItem(API_BASE_URL_KEY) || "http://localhost:8000",
    apiKey: localStorage.getItem(API_KEY_KEY) || "",
  };
}

export function saveApiBaseUrl(value) {
  localStorage.setItem(API_BASE_URL_KEY, value.trim());
}

export function saveApiKey(value) {
  localStorage.setItem(API_KEY_KEY, value);
}

export function addRun(run) {
  runHistory.unshift({
    ...run,
    createdAt: new Date().toISOString(),
  });
}
