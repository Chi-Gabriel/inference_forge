import hashlib
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


def hash_file(path: Path) -> tuple[str, int]:
    sha256 = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        while chunk := source.read(CHUNK_SIZE):
            size += len(chunk)
            sha256.update(chunk)
    return sha256.hexdigest(), size
