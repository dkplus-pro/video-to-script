from __future__ import annotations

from pathlib import Path


DEFAULT_EXTENSIONS = {"mp4", "mov", "mkv", "avi", "m4v"}


def scan_video_files(input_dir: str | Path, extensions: list[str] | None = None) -> list[Path]:
    root = Path(input_dir)
    exts = {e.lower().lstrip(".") for e in (extensions or sorted(DEFAULT_EXTENSIONS))}
    if not root.exists():
        raise FileNotFoundError(f"Input directory does not exist: {root}")
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower().lstrip(".") in exts]
    return sorted(files, key=lambda p: str(p).lower())

