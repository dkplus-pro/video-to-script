from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .cache import read_json, write_json


class Checkpoint:
    def __init__(self, path: str | Path, input_dir: str | Path) -> None:
        self.path = Path(path)
        self.state: dict[str, Any] = read_json(self.path, {}) or {}
        if not self.state:
            self.state = {
                "taskId": datetime.now().strftime("%Y-%m-%d-%H%M%S"),
                "inputDir": str(input_dir),
                "status": "created",
                "steps": {},
                "videos": {},
            }

    def mark_step(self, step: str, status: str, payload: Any | None = None) -> None:
        item = {"status": status, "updatedAt": datetime.now().isoformat(timespec="seconds")}
        if payload is not None:
            item["payload"] = payload
        self.state.setdefault("steps", {})[step] = item
        self.save()

    def mark_video(self, file_name: str, step: str, status: str) -> None:
        videos = self.state.setdefault("videos", {})
        videos.setdefault(file_name, {})[step] = status
        self.save()

    def is_step_done(self, step: str) -> bool:
        return self.state.get("steps", {}).get(step, {}).get("status") == "done"

    def save(self) -> None:
        write_json(self.path, self.state)

