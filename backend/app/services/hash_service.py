from __future__ import annotations

import hashlib
from pathlib import Path


DEFAULT_CHUNK_SIZE = 1024 * 1024


def calculate_sha256(
    file_path: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> str:
    """
    Calculate SHA-256 incrementally.

    The complete file is never loaded into memory.
    """

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Asset not found: {file_path}"
        )

    digest = hashlib.sha256()

    with path.open("rb") as file:
        while True:
            chunk = file.read(chunk_size)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()