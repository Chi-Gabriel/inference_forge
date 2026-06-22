from pathlib import Path


class StoragePaths:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.uploads = root / "uploads"
        self.downloads = root / "downloads"
        self.temp = root / "temp"
        self.decoded = root / "decoded"
        self.cache = root / "cache"

    def ensure(self) -> None:
        for path in [
            self.root,
            self.uploads,
            self.downloads,
            self.temp,
            self.decoded,
            self.cache,
        ]:
            path.mkdir(parents=True, exist_ok=True)
