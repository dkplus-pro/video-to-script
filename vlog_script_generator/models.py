from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class VideoMetadata:
    file_name: str
    path: str
    duration: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    readable: bool = False
    suspected_waste: bool = False
    waste_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExtractedFrame:
    video_file: str
    time_seconds: float
    path: str
    brightness: float | None = None
    blur_score: float | None = None
    skipped_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Filmstrip:
    video_file: str
    path: str
    frame_paths: list[str]
    start_time: float
    end_time: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AsrSegment:
    start: float
    end: float
    text: str
    emotion: str = "未知"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MaterialAnalysis:
    video_file: str
    filmstrip: str = ""
    summary: str = ""
    usable_segments: list[dict[str, Any]] = field(default_factory=list)
    waste_level: str = "部分可用"
    emotion: str = "未知"
    editing_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def ensure_dir(path: str | Path) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target

