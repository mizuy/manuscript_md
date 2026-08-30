from __future__ import annotations

import os
from pathlib import Path

FALLBACK_PAPERPILE_PATHS: tuple[Path, ...] = (
    Path.home() / "paperpile.bib",
    Path.home() / "My Drive/paperpile.bib",
    Path.home() / "Google Drive/My Drive/paperpile.bib",
)


def resolve_paperpile_bib(explicit: Path | None = None) -> Path:
    """Locate paperpile.bib from an explicit path, PAPERPILE_BIB, or fallbacks."""
    if explicit is not None:
        if explicit.is_file():
            return explicit
        raise FileNotFoundError(f"paperpile.bib not found: {explicit}")

    env = os.environ.get("PAPERPILE_BIB")
    if env:
        path = Path(env).expanduser()
        if not path.is_file() and not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        if path.is_file():
            return path

    for candidate in FALLBACK_PAPERPILE_PATHS:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError("paperpile.bib not found (set PAPERPILE_BIB)")


def resolve_paperpile() -> Path:
    """Alias used by reference-ingest helpers."""
    return resolve_paperpile_bib()
