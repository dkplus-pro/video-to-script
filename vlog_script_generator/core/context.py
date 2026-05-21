from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from vlog_script_generator.models import ensure_dir


@dataclass
class RunContext:
    input_dir: Path
    output_dir: Path
    story_path: Path | None
    config: dict
    resume: bool = True
    force: bool = False

    @property
    def cache_dir(self) -> Path:
        return ensure_dir(self.output_dir / "cache")

    @property
    def final_dir(self) -> Path:
        return ensure_dir(self.output_dir / "final")

    @property
    def checkpoints_dir(self) -> Path:
        return ensure_dir(self.output_dir / "checkpoints")

