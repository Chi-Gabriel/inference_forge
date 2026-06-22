import threading


class SourceUrlIndex:
    def __init__(self) -> None:
        self._media_by_url: dict[str, str] = {}
        self._locks_by_url: dict[str, threading.Lock] = {}

    def get(self, url: str) -> str | None:
        return self._media_by_url.get(url)

    def set(self, url: str, media_id: str) -> None:
        self._media_by_url[url] = media_id

    def pop(self, url: str) -> None:
        self._media_by_url.pop(url, None)
        self._locks_by_url.pop(url, None)

    def lock(self, url: str) -> threading.Lock:
        lock = self._locks_by_url.get(url)
        if lock is None:
            lock = threading.Lock()
            self._locks_by_url[url] = lock
        return lock
